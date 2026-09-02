"""
BioTime 9.5 Compatible Report Service with POB Extensions
Comprehensive reporting service aggregating data from all 12 modules
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    _PANDAS_AVAILABLE = False
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case, extract, text, desc, Time
from sqlalchemy.dialects.postgresql import JSONB

# Import all module models
from ..models.personnel import Personnel
from ..models.personnel import AttendanceLog
from ..models.department import Department
from ..models.biotime_models import PersonnelEmployee, ZonePersonnelTracking, IClockOperLog
from ..models.payroll import PaySalary, PaySalaryItem, PayPeriod, PayZoneAllowance
from ..models.biotime_models import BaseOperationLog, AuthUser
from ..models.system import Company as BaseCompany

logger = logging.getLogger(__name__)

class ReportService:
    """Comprehensive BioTime 9.5 compatible report service with POB extensions"""

    # Report registry - maps report codes to functions
    REPORT_REGISTRY = {}

    # Filter schema: maps report_code → {filter_key: expected_type}
    # Used by validate_filters() to strip unknown keys and coerce types.
    FILTER_SCHEMA: Dict[str, Dict[str, type]] = {
        'personnel.employee_list':  {'department': str, 'personnel_type': str, 'is_active': bool, 'search': str},
        'personnel.dept_summary':   {'department': str},
        'personnel.birthday':       {'month': int},
        'personnel.anniversary':    {'month': int, 'department': str},
        'personnel.contractor':     {'department': str, 'search': str},
        'att.daily':                {'date_from': str, 'date_to': str, 'date': str, 'department': str, 'emp_code': str, 'status': str},
        'att.monthly':              {'month': str, 'department': str},
        'att.summary':              {'date_from': str, 'date_to': str, 'department': str},
        'att.late':                 {'date': str, 'department': str},
        'att.early':                {'date': str, 'department': str},
        'att.absent':               {'date': str, 'department': str},
        'att.ot':                   {'date': str, 'department': str},
        'att.leave':                {'date_from': str, 'date_to': str, 'department': str},
        'att.shift':                {'date_from': str, 'date_to': str},
        'att.exceptions':           {'date_from': str, 'date_to': str, 'department': str},
        'ac.events':                {'date_from': str, 'date_to': str, 'emp_code': str, 'terminal_sn': str},
        'ac.door_status':           {},
        'ac.antipassback':          {'date': str},
        'ac.first_card':            {'date': str},
        'ac.inout_count':           {'date': str},
        'device.status':            {},
        'device.transactions':      {'date_from': str, 'date_to': str},
        'device.offline':           {'date_from': str, 'date_to': str},
        'device.firmware':          {},
        'pay.salary_summary':       {'period_id': int},
        'pay.payslip_bulk':         {'period_id': int},
        'pay.bank_sheet':           {'period_id': int},
        'pay.item_wise':            {'period_id': int},
        'pay.variance':             {'period_id': int},
        'pay.zone_cost':            {'period_id': int},
        'pay.contractor_cost':      {'period_id': int},
        'visitor.daily_log':        {'date': str},
        'visitor.host_report':      {'date_from': str, 'date_to': str},
        'visitor.overstay':         {'date_from': str, 'date_to': str},
        'visitor.blacklist':        {},
        'visitor.type_summary':     {'date_from': str, 'date_to': str},
        'visitor.induction':        {},
        'meeting.utilization':      {'date_from': str, 'date_to': str},
        'meeting.booking_log':      {'date_from': str, 'date_to': str},
        'meeting.attendance':       {'date_from': str, 'date_to': str},
        'meeting.noshow':           {'date_from': str, 'date_to': str},
        'meeting.minutes':          {'date_from': str, 'date_to': str},
        'system.operation_log':     {'date_from': str, 'date_to': str, 'module': str},
        'system.login_log':         {'date_from': str, 'date_to': str},
        'system.data_audit':        {'date_from': str, 'date_to': str, 'module': str},
        'system.license_usage':     {},
        'system.api_usage':         {'date_from': str},
        # Zone Security & Audit Reports
        # POB Operations Reports
        'pob.daily_manifest':           {'department': str, 'company': str, 'personnel_type': str, 'zone_id': int},
        'pob.crew_change':              {'date': str, 'change_type': str},
        'pob.rotation_overdue':         {'threshold_days': int, 'department': str, 'company': str},
        'pob.zone_occupancy_history':   {'zone_id': int, 'date_from': str, 'date_to': str},
        'pob.headcount_by_company':     {'company': str},
    }
    
    def __init__(self, db: Session):
        self.db = db
        self._page = 1
        self._page_size = 50
        self._register_reports()

    def _paginate(self, query):
        """Return (rows, total) using SQL COUNT + LIMIT/OFFSET."""
        total = query.count()
        rows = query.limit(self._page_size).offset((self._page - 1) * self._page_size).all()
        return rows, total

    @staticmethod
    def _fmt_dt(dt, fmt='%Y-%m-%dT%H:%M:%S'):
        """Format a datetime as ISO-8601. Returns '' for None."""
        if dt is None:
            return ''
        try:
            return dt.strftime(fmt)
        except Exception:
            return str(dt)

    def validate_filters(self, report_code: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Strip unknown filter keys and coerce types. Raises ValueError for bad values."""
        schema = self.FILTER_SCHEMA.get(report_code)
        if schema is None:
            return filters  # Unknown code — let get_report_data raise ValueError

        cleaned: Dict[str, Any] = {}
        for key, value in filters.items():
            if key not in schema:
                logger.warning("report=%s dropped_unknown_filter=%s", report_code, key)
                continue
            if value is None:
                continue
            expected = schema[key]
            try:
                if expected is int:
                    cleaned[key] = int(value)
                elif expected is bool:
                    if isinstance(value, bool):
                        cleaned[key] = value
                    elif isinstance(value, str):
                        cleaned[key] = value.lower() in ('true', '1', 'yes')
                    else:
                        cleaned[key] = bool(value)
                else:
                    cleaned[key] = str(value)
            except (ValueError, TypeError):
                raise ValueError(f"Filter '{key}' must be {expected.__name__}, got {value!r}")
        return cleaned
    
    def _register_reports(self):
        """Register all report functions"""
        # Personnel Reports
        self.REPORT_REGISTRY.update({
            'personnel.employee_list': self.personnel_employee_list,
            'personnel.dept_summary': self.personnel_department_summary,
            'personnel.birthday': self.personnel_birthday_list,
            'personnel.anniversary': self.personnel_anniversary_list,
            'personnel.contractor': self.personnel_contractor_list,
        })
        
        # Attendance Reports
        self.REPORT_REGISTRY.update({
            'att.daily': self.attendance_daily_report,
            'att.monthly': self.attendance_monthly_summary,
            'att.summary': self.attendance_summary_report,
            'att.late': self.attendance_late_report,
            'att.early': self.attendance_early_report,
            'att.absent': self.attendance_absent_report,
            'att.ot': self.attendance_overtime_report,
            'att.leave': self.attendance_leave_report,
            'att.shift': self.attendance_shift_schedule,
            'att.exceptions': self.attendance_exceptions,
        })
        
        
        
        
        
        # Payroll Reports
        self.REPORT_REGISTRY.update({
            'pay.salary_summary': self.payroll_salary_summary,
            'pay.payslip_bulk': self.payroll_payslip_bulk,
            'pay.bank_sheet': self.payroll_bank_sheet,
            'pay.item_wise': self.payroll_item_wise,
            'pay.variance': self.payroll_variance,
            'pay.zone_cost': self.payroll_zone_cost,
            'pay.contractor_cost': self.payroll_contractor_cost,
        })
        
        
        
        
        # System Reports
        self.REPORT_REGISTRY.update({
            'system.operation_log': self.system_operation_log,
            'system.login_log': self.system_login_log,
            'system.data_audit': self.system_data_audit,
            'system.license_usage': self.system_license_usage,
            'system.api_usage': self.system_api_usage,
        })

    
    def get_report_data(self, report_code: str, filters: Dict[str, Any], 
                       page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        Generic report data endpoint
        
        Args:
            report_code: Report code from registry
            filters: Filter parameters
            page: Page number
            page_size: Page size
            
        Returns:
            Dict with columns, rows, total count
        """
        try:
            if report_code not in self.REPORT_REGISTRY:
                raise ValueError(f"Report code '{report_code}' not found")
            
            # Get report function
            report_func = self.REPORT_REGISTRY[report_code]

            # Set pagination state so handlers can call self._paginate()
            self._page = page
            self._page_size = page_size

            # Validate and clean filters against the known schema
            filters = self.validate_filters(report_code, filters)

            # Execute report with filters
            result = report_func(filters)

            data = result.get('data', [])
            if 'total' in result:
                # Handler applied SQL-level pagination already
                total = result['total']
                paginated_data = data
            else:
                # Legacy handler: Python-level slice (safe fallback)
                total = len(data)
                start = (page - 1) * page_size
                end = start + page_size
                paginated_data = data[start:end]

            return {
                'columns': result.get('columns', []),
                'data': paginated_data,
                'total': total,
                'summary': result.get('summary', {}),
                'chart_data': result.get('chart_data', {}),
                'timezone': 'UTC',
            }
            
        except Exception as e:
            logger.error(f"Error generating report {report_code}: {str(e)}")
            raise
    
    # ==================== PERSONNEL REPORTS ====================
    
    def personnel_employee_list(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Employee list with details"""
        query = self.db.query(Personnel)

        if filters.get('department'):
            query = query.filter(Personnel.department == filters['department'])
        if filters.get('personnel_type'):
            query = query.filter(Personnel.personnel_type == filters['personnel_type'])
        if filters.get('is_active') is not None:
            query = query.filter(Personnel.is_active == filters['is_active'])
        if filters.get('search'):
            search = f"%{filters['search']}%"
            query = query.filter(Personnel.full_name.ilike(search))
        
        query = query.order_by(Personnel.full_name)
        personnel, total = self._paginate(query)

        columns = [
            {'field': 'badge_id', 'label': 'Badge ID', 'type': 'text'},
            {'field': 'full_name', 'label': 'Full Name', 'type': 'text'},
            {'field': 'department', 'label': 'Department', 'type': 'text'},
            {'field': 'position', 'label': 'Position', 'type': 'text'},
            {'field': 'email', 'label': 'Email', 'type': 'text'},
            {'field': 'phone', 'label': 'Phone', 'type': 'text'},
            {'field': 'personnel_type', 'label': 'Type', 'type': 'text'},
            {'field': 'is_active', 'label': 'Active', 'type': 'boolean'},
        ]

        data = []
        for p in personnel:
            data.append({
                'badge_id': p.badge_id or '',
                'full_name': p.full_name or '',
                'department': p.department or '',
                'position': p.position or '',
                'email': p.email or '',
                'phone': p.phone or '',
                'personnel_type': p.personnel_type or '',
                'is_active': p.is_active or False,
            })

        return {
            'columns': columns,
            'data': data,
            'total': total,
            'summary': {'total_employees': total}
        }
    
    def personnel_department_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Personnel count by department"""
        result = self.db.query(
            Personnel.department,
            func.count(Personnel.id).label('total_count'),
            func.sum(case((Personnel.is_active == True, 1), else_=0)).label('active_count'),
            func.sum(case((Personnel.personnel_type == 'Contractor', 1), else_=0)).label('contractor_count')
        ).group_by(Personnel.department).all()
        
        columns = [
            {'field': 'department', 'label': 'Department', 'type': 'text'},
            {'field': 'total_count', 'label': 'Total Count', 'type': 'number'},
            {'field': 'active_count', 'label': 'Active Count', 'type': 'number'},
            {'field': 'contractor_count', 'label': 'Contractor Count', 'type': 'number'},
        ]
        
        data = []
        for row in result:
            data.append({
                'department': row.department or 'Unknown',
                'total_count': row.total_count or 0,
                'active_count': row.active_count or 0,
                'contractor_count': row.contractor_count or 0,
            })
        
        # Chart data for bar chart
        chart_data = {
            'labels': [row['department'] for row in data],
            'datasets': [{
                'label': 'Total Employees',
                'data': [row['total_count'] for row in data],
                'backgroundColor': '#4F81BD'
            }]
        }
        
        return {
            'columns': columns,
            'data': data,
            'chart_data': chart_data,
            'summary': {'total_departments': len(data)}
        }
    
    def personnel_birthday_list(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Employee birthdays by month"""
        month_filter = filters.get('month')

        query = self.db.query(PersonnelEmployee).filter(
            PersonnelEmployee.birthday.isnot(None),
            PersonnelEmployee.status == 0,
        )
        if month_filter:
            query = query.filter(extract('month', PersonnelEmployee.birthday) == month_filter)
        query = query.order_by(extract('month', PersonnelEmployee.birthday), extract('day', PersonnelEmployee.birthday))
        employees, total = self._paginate(query)

        columns = [
            {'field': 'emp_code',   'label': 'Badge ID',    'type': 'text'},
            {'field': 'full_name',  'label': 'Full Name',   'type': 'text'},
            {'field': 'birth_date', 'label': 'Birth Date',  'type': 'date'},
            {'field': 'age',        'label': 'Age',         'type': 'number'},
        ]

        data = []
        today = date.today()
        for emp in employees:
            if emp.birthday:
                age = today.year - emp.birthday.year - ((today.month, today.day) < (emp.birthday.month, emp.birthday.day))
                data.append({
                    'emp_code':   emp.emp_code or '',
                    'full_name':  f"{emp.first_name or ''} {emp.last_name or ''}".strip(),
                    'birth_date': emp.birthday.strftime('%Y-%m-%d'),
                    'age': age,
                })

        # Chart: aggregate by month across ALL records (separate query)
        month_agg = self.db.query(
            extract('month', PersonnelEmployee.birthday).label('m'),
            func.count().label('cnt')
        ).filter(PersonnelEmployee.birthday.isnot(None)).group_by('m').order_by('m').all()
        month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        chart_data = {
            'labels': [month_names[int(r.m) - 1] for r in month_agg],
            'datasets': [{'label': 'Birthdays', 'data': [r.cnt for r in month_agg], 'backgroundColor': '#9BBB59'}]
        }
        
        return {
            'columns': columns,
            'data': data,
            'total': total,
            'chart_data': chart_data,
            'summary': {'total_birthdays': total}
        }

    # ==================== ATTENDANCE REPORTS ====================
    
    _ATT_STATUS = {0: 'Present', 1: 'Late', 2: 'Early Leave', 3: 'Absent', 4: 'Leave', 5: 'Holiday', 6: 'Weekend'}

    def attendance_daily_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attendance audit report — one row per employee per day.
        Supports any date range via date_from / date_to.
        Joins att_report (computed) with att_timetable (scheduled) and
        iclock_transaction (raw punch count) for full audit trail.
        """
        default_from = (date.today() - timedelta(days=6)).strftime('%Y-%m-%d')
        default_to   = date.today().strftime('%Y-%m-%d')
        date_from = filters.get('date_from', filters.get('date', default_from))
        date_to   = filters.get('date_to',   filters.get('date', default_to))

        sql = text("""
            SELECT
                r.att_date,
                e.emp_code,
                (e.first_name || ' ' || e.last_name)   AS full_name,
                COALESCE(d.dept_name, '')               AS department,
                -- Scheduled times from timetable
                t.start_time                            AS scheduled_in,
                t.end_time                              AS scheduled_out,
                r.scheduled_minutes,
                -- Actual from att_report (computed by attendance_calculation_service)
                r.check_in,
                r.check_out,
                r.work_minutes,
                r.late_minutes,
                r.early_minutes,
                r.ot_minutes,
                r.att_status,
                -- Raw punch count from iclock_transaction for cross-verification
                COALESCE(tx.punch_count, 0)            AS punch_count
            FROM att_report r
            JOIN personnel_employee e ON r.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            LEFT JOIN att_timetable t ON r.timetable_id = t.id
            LEFT JOIN (
                SELECT emp_code, punch_time::date AS p_date, COUNT(*) AS punch_count
                FROM iclock_transaction
                WHERE punch_time::date BETWEEN :date_from AND :date_to
                GROUP BY emp_code, punch_time::date
            ) tx ON tx.emp_code = e.emp_code AND tx.p_date = r.att_date
            WHERE r.att_date BETWEEN :date_from AND :date_to
            ORDER BY r.att_date DESC, d.dept_name, full_name
        """)
        params = {'date_from': date_from, 'date_to': date_to}

        if filters.get('emp_code'):
            sql = text(sql.text.replace(
                'WHERE r.att_date BETWEEN',
                'WHERE e.emp_code = :emp_code AND r.att_date BETWEEN'
            ))
            params['emp_code'] = filters['emp_code']

        rows = self.db.execute(sql, params).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        if filters.get('status'):
            want = filters['status'].lower()
            status_rev = {v.lower(): k for k, v in self._ATT_STATUS.items()}
            if want in status_rev:
                rows = [r for r in rows if r._mapping['att_status'] == status_rev[want]]

        columns = [
            {'field': 'att_date',          'label': 'Date',           'type': 'date',     'width': 110},
            {'field': 'emp_code',           'label': 'Emp Code',       'type': 'text',     'width': 100},
            {'field': 'full_name',          'label': 'Full Name',      'type': 'text',     'width': 160},
            {'field': 'department',         'label': 'Department',     'type': 'text',     'width': 130},
            {'field': 'scheduled_in',       'label': 'Sched In',       'type': 'text',     'width': 90},
            {'field': 'scheduled_out',      'label': 'Sched Out',      'type': 'text',     'width': 90},
            {'field': 'check_in',           'label': 'Actual In',      'type': 'datetime', 'width': 140},
            {'field': 'check_out',          'label': 'Actual Out',     'type': 'datetime', 'width': 140},
            {'field': 'work_hours',         'label': 'Work Hrs',       'type': 'number',   'width': 90},
            {'field': 'scheduled_hours',    'label': 'Sched Hrs',      'type': 'number',   'width': 90},
            {'field': 'late_minutes',       'label': 'Late (min)',      'type': 'number',   'width': 90},
            {'field': 'early_minutes',      'label': 'Early (min)',     'type': 'number',   'width': 90},
            {'field': 'ot_minutes',         'label': 'OT (min)',        'type': 'number',   'width': 80},
            {'field': 'punch_count',        'label': 'Punches',         'type': 'number',   'width': 80},
            {'field': 'status',             'label': 'Status',          'type': 'text',     'width': 100},
        ]

        data = []
        status_counts: Dict[str, int] = {}
        for r in rows:
            m = r._mapping
            ci, co = m['check_in'], m['check_out']
            st = self._ATT_STATUS.get(m['att_status'], 'Unknown')
            status_counts[st] = status_counts.get(st, 0) + 1

            # Format scheduled times (stored as timedelta in postgres time columns)
            def fmt_time(val):
                if val is None:
                    return ''
                if hasattr(val, 'strftime'):
                    return val.strftime('%H:%M')
                if hasattr(val, 'seconds'):          # timedelta
                    s = int(val.total_seconds())
                    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}"
                return str(val)[:5]

            data.append({
                'att_date':       str(m['att_date']),
                'emp_code':       m['emp_code'],
                'full_name':      m['full_name'],
                'department':     m['department'],
                'scheduled_in':   fmt_time(m['scheduled_in']),
                'scheduled_out':  fmt_time(m['scheduled_out']),
                'check_in':       ci.strftime('%Y-%m-%d %H:%M') if ci else '',
                'check_out':      co.strftime('%Y-%m-%d %H:%M') if co else '',
                'work_hours':     round((m['work_minutes'] or 0) / 60, 2),
                'scheduled_hours': round((m['scheduled_minutes'] or 0) / 60, 2),
                'late_minutes':   m['late_minutes'] or 0,
                'early_minutes':  m['early_minutes'] or 0,
                'ot_minutes':     m['ot_minutes'] or 0,
                'punch_count':    m['punch_count'] or 0,
                'status':         st,
            })

        present = status_counts.get('Present', 0) + status_counts.get('Late', 0) + status_counts.get('Early Leave', 0)
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                'date_from':    date_from,
                'date_to':      date_to,
                'total_records': len(data),
                'present':      present,
                'absent':       status_counts.get('Absent', 0),
                'late':         status_counts.get('Late', 0),
                'leave':        status_counts.get('Leave', 0),
            },
        }
    
    def attendance_monthly_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Monthly attendance summary from att_report"""
        month_filter = filters.get('month', date.today().strftime('%Y-%m'))
        year, month = map(int, month_filter.split('-'))
        start_date = date(year, month, 1)
        end_date = date(year + (month // 12), (month % 12) + 1, 1) - timedelta(days=1)

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   COUNT(*) FILTER (WHERE r.att_status IN (0,1,2)) AS present_days,
                   COUNT(*) FILTER (WHERE r.att_status = 3)        AS absent_days,
                   COUNT(*) FILTER (WHERE r.att_status = 1)        AS late_days,
                   ROUND(SUM(r.work_minutes)::numeric / 60, 2)     AS total_work_hours,
                   SUM(r.late_minutes)                             AS total_late_minutes
            FROM att_report r
            JOIN personnel_employee e ON r.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            WHERE r.att_date BETWEEN :start_date AND :end_date
            GROUP BY e.id, e.emp_code, e.first_name, e.last_name, d.dept_name
            ORDER BY d.dept_name, full_name
        """)
        rows = self.db.execute(sql, {'start_date': start_date, 'end_date': end_date}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',           'label': 'Emp Code',        'type': 'text'},
            {'field': 'full_name',          'label': 'Full Name',       'type': 'text'},
            {'field': 'department',         'label': 'Department',      'type': 'text'},
            {'field': 'present_days',       'label': 'Present Days',    'type': 'number'},
            {'field': 'absent_days',        'label': 'Absent Days',     'type': 'number'},
            {'field': 'late_days',          'label': 'Late Days',       'type': 'number'},
            {'field': 'total_work_hours',   'label': 'Work Hours',      'type': 'number'},
            {'field': 'total_late_minutes', 'label': 'Late Minutes',    'type': 'number'},
        ]
        data = [dict(r._mapping) for r in rows]

        dept_summary: Dict[str, int] = {}
        for row in data:
            d = row.get('department', '')
            dept_summary[d] = dept_summary.get(d, 0) + int(row.get('present_days') or 0)

        chart_data = {
            'labels': list(dept_summary.keys()),
            'datasets': [{'label': 'Present Days', 'data': list(dept_summary.values()), 'backgroundColor': '#0078D4'}],
        }
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'chart_data': chart_data,
            'summary': {'total_employees': len(data), 'month': month_filter},
        }
    
    def attendance_late_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Late arrival report from att_report — employees with late_minutes > 0"""
        date_filter = filters.get('date', date.today().strftime('%Y-%m-%d'))

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   r.check_in, r.late_minutes
            FROM att_report r
            JOIN personnel_employee e ON r.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            WHERE r.att_date = :att_date AND r.late_minutes > 0
            ORDER BY r.late_minutes DESC
        """)
        rows = self.db.execute(sql, {'att_date': date_filter}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',     'label': 'Emp Code',   'type': 'text'},
            {'field': 'full_name',    'label': 'Full Name',  'type': 'text'},
            {'field': 'department',   'label': 'Department', 'type': 'text'},
            {'field': 'check_in',     'label': 'Check In',   'type': 'datetime'},
            {'field': 'late_minutes', 'label': 'Late (min)', 'type': 'number'},
        ]
        data = []
        for r in rows:
            m = r._mapping
            ci = m['check_in']
            data.append({
                'emp_code':     m['emp_code'],
                'full_name':    m['full_name'],
                'department':   m['department'],
                'check_in':     ci.strftime('%Y-%m-%d %H:%M') if ci else '',
                'late_minutes': m['late_minutes'] or 0,
            })

        dept_late: Dict[str, int] = {}
        for row in data:
            dept_late[row['department']] = dept_late.get(row['department'], 0) + row['late_minutes']

        chart_data = {
            'labels': list(dept_late.keys()),
            'datasets': [{'label': 'Late Minutes', 'data': list(dept_late.values()), 'backgroundColor': '#F79646'}],
        }
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'chart_data': chart_data,
            'summary': {
                'total_late': len(data),
                'total_late_minutes': sum(r['late_minutes'] for r in data),
                'date': date_filter,
            },
        }
    
    # ==================== MUSTERING REPORTS (POB EXTENSION) ====================
    
    # ── Mustering label maps ─────────────────────────────────────────────────
    _MUSTER_EVENT_TYPE = {
        0: 'Real Emergency', 1: 'Drill', 2: 'Fire',
        3: 'Gas', 4: 'Man Down',
    }
    _MUSTER_STATUS  = {0: 'Active', 1: 'Completed'}
    _MUSTER_LOG_STATUS = {0: 'Missing', 1: 'Safe', 2: 'Injured'}

    @staticmethod
    def _latest_period_id(db) -> int | None:
        row = db.execute(text(
            "SELECT id FROM pay_period ORDER BY end_date DESC LIMIT 1"
        )).fetchone()
        return row.id if row else None

    @staticmethod
    def _period_meta(db, period_id: int) -> dict:
        row = db.execute(text(
            "SELECT period_name, start_date, end_date, status FROM pay_period WHERE id = :pid"
        ), {'pid': period_id}).fetchone()
        if not row:
            return {}
        return {
            'period_id':   period_id,
            'period_name': row.period_name,
            'start_date':  str(row.start_date),
            'end_date':    str(row.end_date),
            'period_status': row.status or '',
        }

    @staticmethod
    def _employee_roster_context(db) -> dict:
        """Fallback context when no payroll periods exist — shows payroll-ready headcount."""
        rows = db.execute(text("""
            SELECT department,
                   COUNT(*)                                         AS total,
                   COUNT(CASE WHEN is_active THEN 1 END)           AS active,
                   COUNT(CASE WHEN personnel_type='CONTRACTOR' THEN 1 END) AS contractors
            FROM personnel
            GROUP BY department
            ORDER BY department
        """)).fetchall()
        return {
            'no_payroll_data': True,
            'message': 'No payroll periods found. Create a pay period to run payroll.',
            'employee_roster': [
                {'department': r.department or 'Unassigned',
                 'total': int(r.total), 'active': int(r.active),
                 'contractors': int(r.contractors)}
                for r in rows
            ],
            'total_active_employees': sum(int(r.active) for r in rows),
        }

    def payroll_salary_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Salary summary by department for a pay period — with period header and dept breakdown."""
        period_id = filters.get('period_id') or self._latest_period_id(self.db)
        if not period_id:
            return {'columns': [], 'data': [], 'total': 0,
                    'summary': self._employee_roster_context(self.db)}

        rows = self.db.execute(text("""
            SELECT
                COALESCE(NULLIF(p.department, ''), 'Unassigned')   AS department,
                COUNT(s.id)                                         AS employee_count,
                COALESCE(SUM(s.basic_salary),     0)               AS total_basic,
                COALESCE(SUM(s.gross_salary),     0)               AS total_gross,
                COALESCE(SUM(s.total_earnings),   0)               AS total_earnings,
                COALESCE(SUM(s.total_deductions), 0)               AS total_deductions,
                COALESCE(SUM(s.net_salary),       0)               AS total_net,
                COALESCE(AVG(s.gross_salary),     0)               AS avg_gross,
                COALESCE(AVG(s.net_salary),       0)               AS avg_net,
                COALESCE(SUM(s.ot_hours),         0)               AS total_ot_hours,
                COALESCE(SUM(s.present_days),     0)               AS total_present_days,
                COALESCE(SUM(s.absent_days),      0)               AS total_absent_days
            FROM pay_salary s
            JOIN personnel p ON s.emp_id = p.id
            WHERE s.period_id = :pid
            GROUP BY COALESCE(NULLIF(p.department, ''), 'Unassigned')
            ORDER BY department
        """), {'pid': period_id}).fetchall()

        columns = [
            {'field': 'department',       'label': 'Department',    'type': 'text'},
            {'field': 'employee_count',   'label': 'Employees',     'type': 'number'},
            {'field': 'total_basic',      'label': 'Total Basic',   'type': 'currency'},
            {'field': 'total_earnings',   'label': 'Total Earnings','type': 'currency'},
            {'field': 'total_deductions', 'label': 'Deductions',    'type': 'currency'},
            {'field': 'total_gross',      'label': 'Total Gross',   'type': 'currency'},
            {'field': 'total_net',        'label': 'Total Net',     'type': 'currency'},
            {'field': 'avg_gross',        'label': 'Avg Gross',     'type': 'currency'},
            {'field': 'avg_net',          'label': 'Avg Net',       'type': 'currency'},
            {'field': 'total_ot_hours',   'label': 'OT Hours',      'type': 'number'},
            {'field': 'total_present_days','label': 'Present Days', 'type': 'number'},
            {'field': 'total_absent_days', 'label': 'Absent Days',  'type': 'number'},
        ]
        data = [{
            'department':       r.department,
            'employee_count':   int(r.employee_count),
            'total_basic':      float(r.total_basic),
            'total_earnings':   float(r.total_earnings),
            'total_deductions': float(r.total_deductions),
            'total_gross':      float(r.total_gross),
            'total_net':        float(r.total_net),
            'avg_gross':        round(float(r.avg_gross), 2),
            'avg_net':          round(float(r.avg_net), 2),
            'total_ot_hours':   float(r.total_ot_hours),
            'total_present_days': float(r.total_present_days),
            'total_absent_days':  float(r.total_absent_days),
        } for r in rows]

        chart_data = {
            'labels': [r['department'] for r in data],
            'datasets': [
                {'label': 'Gross Salary', 'data': [r['total_gross'] for r in data], 'backgroundColor': '#4F81BD'},
                {'label': 'Net Salary',   'data': [r['total_net']   for r in data], 'backgroundColor': '#70AD47'},
            ],
        }
        meta = self._period_meta(self.db, period_id)
        return {
            'columns': columns, 'data': data, 'chart_data': chart_data,
            'total': len(data),
            'summary': {
                **meta,
                'total_employees':    sum(r['employee_count']   for r in data),
                'total_gross':        round(sum(r['total_gross'] for r in data), 2),
                'total_net':          round(sum(r['total_net']   for r in data), 2),
                'total_deductions':   round(sum(r['total_deductions'] for r in data), 2),
            },
        }

    def payroll_zone_cost(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """POB zone cost analysis — salary data grouped by employee's current zone, with zone allowance config."""
        period_id = filters.get('period_id') or self._latest_period_id(self.db)

        # Zone allowance configuration (always available regardless of period data)
        allowance_rows = self.db.execute(text("""
            SELECT
                COALESCE(z.name, za.zone_name, 'Unknown Zone') AS zone_name,
                za.allowance_type,
                za.amount                                       AS allowance_amount,
                za.is_hazard,
                za.hazard_rate,
                za.effective_date,
                za.end_date,
                za.is_active
            FROM pay_zone_allowance za
            LEFT JOIN zones z ON za.area_id = z.id
            ORDER BY zone_name
        """)).fetchall()

        # Salary breakdown by zone (when period data exists)
        salary_rows = []
        if period_id:
            salary_rows = self.db.execute(text("""
                SELECT
                    COALESCE(z.name, p.current_location, 'Unassigned') AS zone_name,
                    COUNT(s.id)                                         AS employee_count,
                    COALESCE(SUM(s.zone_hours),   0)                   AS total_zone_hours,
                    COALESCE(SUM(s.night_hours),  0)                   AS total_night_hours,
                    COALESCE(SUM(s.hazard_days),  0)                   AS total_hazard_days,
                    COALESCE(SUM(s.gross_salary), 0)                   AS total_gross,
                    COALESCE(SUM(s.net_salary),   0)                   AS total_net
                FROM pay_salary s
                JOIN personnel p ON s.emp_id = p.id
                LEFT JOIN zones z ON p.current_zone_id = z.id
                WHERE s.period_id = :pid
                  AND (s.zone_hours > 0 OR s.night_hours > 0 OR s.hazard_days > 0)
                GROUP BY COALESCE(z.name, p.current_location, 'Unassigned')
                ORDER BY total_gross DESC
            """), {'pid': period_id}).fetchall()

        columns = [
            {'field': 'zone_name',         'label': 'Zone',             'type': 'text'},
            {'field': 'employee_count',    'label': 'Employees',        'type': 'number'},
            {'field': 'total_zone_hours',  'label': 'Zone Hours',       'type': 'number'},
            {'field': 'total_night_hours', 'label': 'Night Hours',      'type': 'number'},
            {'field': 'total_hazard_days', 'label': 'Hazard Days',      'type': 'number'},
            {'field': 'total_gross',       'label': 'Total Gross',      'type': 'currency'},
            {'field': 'total_net',         'label': 'Total Net',        'type': 'currency'},
        ]
        data = [{
            'zone_name':         r.zone_name,
            'employee_count':    int(r.employee_count),
            'total_zone_hours':  float(r.total_zone_hours),
            'total_night_hours': float(r.total_night_hours),
            'total_hazard_days': float(r.total_hazard_days),
            'total_gross':       float(r.total_gross),
            'total_net':         float(r.total_net),
        } for r in salary_rows]

        allowance_config = [{
            'zone_name':       r.zone_name,
            'allowance_amount':float(r.allowance_amount),
            'is_hazard':       bool(r.is_hazard),
            'hazard_rate':     float(r.hazard_rate or 0),
            'effective_date':  str(r.effective_date) if r.effective_date else '',
            'end_date':        str(r.end_date) if r.end_date else '',
            'is_active':       bool(r.is_active),
        } for r in allowance_rows]

        chart_data = {
            'labels': [r['zone_name'] for r in data],
            'datasets': [
                {'label': 'Total Gross', 'data': [r['total_gross'] for r in data], 'backgroundColor': '#F79646'},
                {'label': 'Total Net',   'data': [r['total_net']   for r in data], 'backgroundColor': '#4F81BD'},
            ],
        }
        meta = self._period_meta(self.db, period_id) if period_id else {}
        return {
            'columns': columns, 'data': data, 'chart_data': chart_data,
            'total': len(data),
            'summary': {
                **meta,
                'total_zones':      len(data),
                'total_gross':      round(sum(r['total_gross'] for r in data), 2),
                'total_net':        round(sum(r['total_net']   for r in data), 2),
                'allowance_config': allowance_config,
                **(self._employee_roster_context(self.db) if not period_id else {}),
            },
        }

    # ==================== VISITOR REPORTS ====================
    
    # ── Visitor label maps ────────────────────────────────────────────────────
    _VIS_LOG_STATUS  = {0: 'On Site', 1: 'Checked Out', 2: 'Overstay'}
    _VIS_PREREG_STATUS = {
        0: 'Pending', 1: 'Approved', 2: 'Rejected',
        3: 'Checked In', 4: 'Checked Out', 5: 'Expired',
    }
    _VIS_ID_TYPE = {0: 'National ID', 1: 'Passport', 2: 'Driver\'s License'}
    _VIS_MUSTER_STATUS = {0: 'Missing', 1: 'Safe'}

    # ── Shared visitor base SQL (visit log + all enrichment joins) ────────────
    _VIS_BASE_SQL = """
        SELECT
            vl.id                                                    AS log_id,
            v.visitor_code,
            v.full_name                                              AS visitor_name,
            COALESCE(v.company, '')                                  AS company,
            COALESCE(vt.type_name, 'General')                       AS visitor_type,
            v.id_type,
            COALESCE(v.id_no, '')                                    AS id_no,
            v.phone,
            v.email,
            v.safety_induction_done,
            vl.check_in_time,
            vl.check_out_time,
            vl.status                                                AS log_status,
            vl.card_no,
            vl.badge_printed,
            vl.overstay_alert_sent,
            EXTRACT(EPOCH FROM (
                COALESCE(vl.check_out_time, now()) - vl.check_in_time
            ))/3600                                                  AS duration_hours,
            COALESCE(he.first_name || ' ' || TRIM(he.last_name), '') AS host_name,
            COALESCE(he.emp_code, '')                                AS host_emp_code,
            COALESCE(pa.area_name, '')                               AS area_name,
            COALESCE(pr.purpose, '')                                 AS visit_purpose,
            COALESCE(pr.vehicle_no, '')                              AS vehicle_no,
            pr.id IS NOT NULL                                        AS pre_registered,
            COALESCE(vt.default_visit_hours, 8)                     AS allowed_hours
        FROM vis_visit_log vl
        JOIN vis_visitor v          ON vl.visitor_id    = v.id
        LEFT JOIN vis_type vt       ON v.visitor_type_id = vt.id
        LEFT JOIN vis_pre_registration pr ON vl.pre_reg_id = pr.id
        LEFT JOIN personnel_employee he   ON vl.host_emp_id = he.id
        LEFT JOIN personnel_area pa       ON vl.area_id     = pa.id
    """

    def system_operation_log(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """System operation log"""
        query = self.db.query(BaseOperationLog).join(AuthUser)
        
        if filters.get('date_from'):
            query = query.filter(BaseOperationLog.created_at >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(BaseOperationLog.created_at <= filters['date_to'])
        if filters.get('module'):
            query = query.filter(BaseOperationLog.table_name == filters['module'])

        query = query.order_by(desc(BaseOperationLog.created_at))
        logs, total = self._paginate(query)

        columns = [
            {'field': 'timestamp', 'label': 'Time', 'type': 'datetime'},
            {'field': 'user', 'label': 'User', 'type': 'text'},
            {'field': 'ip_address', 'label': 'IP Address', 'type': 'text'},
            {'field': 'module', 'label': 'Module', 'type': 'text'},
            {'field': 'action', 'label': 'Action', 'type': 'text'},
            {'field': 'target', 'label': 'Target', 'type': 'text'},
        ]

        data = []
        for log in logs:
            data.append({
                'timestamp': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
                'user': log.user.username if log.user else '',
                'ip_address': log.ip_address or '',
                'module': log.table_name or '',
                'action': log.action or '',
                'target': f"{log.table_name}#{log.record_id}" if log.record_id else log.table_name or '',
            })

        return {
            'columns': columns,
            'data': data,
            'total': total,
            'summary': {
                'total_operations': total,
            }
        }
    
    # ==================== PERSONNEL (continued) ====================

    def personnel_anniversary_list(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Work anniversary listing"""
        month_filter = filters.get('month')
        query = self.db.query(Personnel).filter(Personnel.hire_date.isnot(None))
        if month_filter:
            query = query.filter(extract('month', Personnel.hire_date) == month_filter)
        if filters.get('department'):
            query = query.filter(Personnel.department == filters['department'])
        query = query.order_by(Personnel.full_name)
        personnel, total = self._paginate(query)

        columns = [
            {'field': 'badge_id',      'label': 'Badge ID',      'type': 'text'},
            {'field': 'full_name',     'label': 'Full Name',     'type': 'text'},
            {'field': 'department',    'label': 'Department',    'type': 'text'},
            {'field': 'hire_date',     'label': 'Hire Date',     'type': 'date'},
            {'field': 'years_service', 'label': 'Years Service', 'type': 'number'},
        ]
        today = date.today()
        data = []
        for p in personnel:
            if p.hire_date:
                yrs = today.year - p.hire_date.year - (
                    (today.month, today.day) < (p.hire_date.month, p.hire_date.day)
                )
                data.append({
                    'badge_id':      p.badge_id or '',
                    'full_name':     p.full_name or '',
                    'department':    p.department or '',
                    'hire_date':     p.hire_date.strftime('%Y-%m-%d'),
                    'years_service': yrs,
                })
        return {'columns': columns, 'data': data, 'total': total, 'summary': {'total': total}}

    def personnel_contractor_list(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Contractor personnel listing"""
        query = self.db.query(Personnel).filter(
            Personnel.personnel_type.ilike('%contractor%')
        )
        if filters.get('department'):
            query = query.filter(Personnel.department == filters['department'])
        if filters.get('search'):
            query = query.filter(Personnel.full_name.ilike(f"%{filters['search']}%"))
        query = query.order_by(Personnel.full_name)
        personnel, total = self._paginate(query)

        columns = [
            {'field': 'badge_id',        'label': 'Badge ID',    'type': 'text'},
            {'field': 'full_name',       'label': 'Full Name',   'type': 'text'},
            {'field': 'department',      'label': 'Department',  'type': 'text'},
            {'field': 'position',        'label': 'Position',    'type': 'text'},
            {'field': 'personnel_type',  'label': 'Type',        'type': 'text'},
            {'field': 'hire_date',       'label': 'Start Date',  'type': 'date'},
            {'field': 'is_active',       'label': 'Active',      'type': 'boolean'},
        ]
        data = [{
            'badge_id':       p.badge_id or '',
            'full_name':      p.full_name or '',
            'department':     p.department or '',
            'position':       p.position or '',
            'personnel_type': p.personnel_type or '',
            'hire_date':      p.hire_date.strftime('%Y-%m-%d') if p.hire_date else '',
            'is_active':      p.is_active or False,
        } for p in personnel]
        return {'columns': columns, 'data': data, 'total': total, 'summary': {'total_contractors': total}}

    # ==================== ATTENDANCE (continued) ====================

    def attendance_summary_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Overall attendance statistics for a date range from att_report"""
        date_from = filters.get('date_from', date.today().replace(day=1).strftime('%Y-%m-%d'))
        date_to   = filters.get('date_to',   date.today().strftime('%Y-%m-%d'))

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   COUNT(*) FILTER (WHERE r.att_status IN (0,1,2)) AS present_days,
                   COUNT(*) FILTER (WHERE r.att_status = 3)        AS absent_days,
                   COUNT(*) FILTER (WHERE r.att_status = 4)        AS leave_days,
                   ROUND(SUM(r.work_minutes)::numeric / 60, 2)     AS total_work_hours,
                   SUM(r.late_minutes)                             AS total_late_minutes,
                   SUM(r.ot_minutes)                               AS total_ot_minutes
            FROM att_report r
            JOIN personnel_employee e ON r.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            WHERE r.att_date BETWEEN :date_from AND :date_to
            GROUP BY e.id, e.emp_code, e.first_name, e.last_name, d.dept_name
            ORDER BY d.dept_name, full_name
        """)
        rows = self.db.execute(sql, {'date_from': date_from, 'date_to': date_to}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',           'label': 'Emp Code',     'type': 'text'},
            {'field': 'full_name',          'label': 'Full Name',    'type': 'text'},
            {'field': 'department',         'label': 'Department',   'type': 'text'},
            {'field': 'present_days',       'label': 'Present Days', 'type': 'number'},
            {'field': 'absent_days',        'label': 'Absent Days',  'type': 'number'},
            {'field': 'leave_days',         'label': 'Leave Days',   'type': 'number'},
            {'field': 'total_work_hours',   'label': 'Work Hours',   'type': 'number'},
            {'field': 'total_late_minutes', 'label': 'Late Min',     'type': 'number'},
            {'field': 'total_ot_minutes',   'label': 'OT Min',       'type': 'number'},
        ]
        data = [dict(r._mapping) for r in rows]
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                'total_employees': len(data),
                'total_present_days': sum(int(r.get('present_days') or 0) for r in data),
                'date_from': date_from, 'date_to': date_to,
            },
        }

    def attendance_early_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Early departure from att_report — employees with early_minutes > 0"""
        date_filter = filters.get('date', date.today().strftime('%Y-%m-%d'))

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   r.check_out, r.early_minutes
            FROM att_report r
            JOIN personnel_employee e ON r.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            WHERE r.att_date = :att_date AND r.early_minutes > 0
            ORDER BY r.early_minutes DESC
        """)
        rows = self.db.execute(sql, {'att_date': date_filter}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',      'label': 'Emp Code',    'type': 'text'},
            {'field': 'full_name',     'label': 'Full Name',   'type': 'text'},
            {'field': 'department',    'label': 'Department',  'type': 'text'},
            {'field': 'check_out',     'label': 'Check Out',   'type': 'datetime'},
            {'field': 'early_minutes', 'label': 'Early (min)', 'type': 'number'},
        ]
        data = []
        for r in rows:
            m = r._mapping
            co = m['check_out']
            data.append({
                'emp_code':      m['emp_code'],
                'full_name':     m['full_name'],
                'department':    m['department'],
                'check_out':     co.strftime('%Y-%m-%d %H:%M') if co else '',
                'early_minutes': m['early_minutes'] or 0,
            })
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {'total_early': len(data), 'date': date_filter},
        }

    def attendance_absent_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Active employees absent (att_status=3) or with no att_report for the date"""
        date_filter = filters.get('date', date.today().strftime('%Y-%m-%d'))

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   COALESCE(r.att_status, -1) AS att_status
            FROM personnel_employee e
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            LEFT JOIN att_report r ON r.emp_id = e.id AND r.att_date = :att_date
            WHERE e.status = 0
              AND (r.id IS NULL OR r.att_status = 3)
            ORDER BY d.dept_name, full_name
        """)
        rows = self.db.execute(sql, {'att_date': date_filter}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',   'label': 'Emp Code',   'type': 'text'},
            {'field': 'full_name',  'label': 'Full Name',  'type': 'text'},
            {'field': 'department', 'label': 'Department', 'type': 'text'},
            {'field': 'reason',     'label': 'Reason',     'type': 'text'},
        ]
        data = [{
            'emp_code':   r._mapping['emp_code'],
            'full_name':  r._mapping['full_name'],
            'department': r._mapping['department'],
            'reason':     'Marked Absent' if r._mapping['att_status'] == 3 else 'No Record',
        } for r in rows]
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {'total_absent': len(data), 'date': date_filter},
        }

    def attendance_overtime_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Overtime report from att_report — employees with ot_minutes > 0"""
        date_filter = filters.get('date', date.today().strftime('%Y-%m-%d'))

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   r.check_in, r.check_out,
                   r.work_minutes,
                   GREATEST(r.ot_minutes, r.overtime_minutes, 0) AS ot_minutes
            FROM att_report r
            JOIN personnel_employee e ON r.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            WHERE r.att_date = :att_date
              AND GREATEST(r.ot_minutes, r.overtime_minutes, 0) > 0
            ORDER BY ot_minutes DESC
        """)
        rows = self.db.execute(sql, {'att_date': date_filter}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',   'label': 'Emp Code',   'type': 'text'},
            {'field': 'full_name',  'label': 'Full Name',  'type': 'text'},
            {'field': 'department', 'label': 'Department', 'type': 'text'},
            {'field': 'check_in',   'label': 'Check In',   'type': 'datetime'},
            {'field': 'check_out',  'label': 'Check Out',  'type': 'datetime'},
            {'field': 'work_hours', 'label': 'Work Hours', 'type': 'number'},
            {'field': 'ot_hours',   'label': 'OT Hours',   'type': 'number'},
        ]
        data = []
        for r in rows:
            m = r._mapping
            ci, co = m['check_in'], m['check_out']
            data.append({
                'emp_code':   m['emp_code'],
                'full_name':  m['full_name'],
                'department': m['department'],
                'check_in':   ci.strftime('%Y-%m-%d %H:%M') if ci else '',
                'check_out':  co.strftime('%Y-%m-%d %H:%M') if co else '',
                'work_hours': round((m['work_minutes'] or 0) / 60, 2),
                'ot_hours':   round((m['ot_minutes'] or 0) / 60, 2),
            })
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                'total_with_ot': len(data),
                'total_ot_hours': round(sum(r['ot_hours'] for r in data), 2),
                'date': date_filter,
            },
        }

    def attendance_leave_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Leave records from att_leave table"""
        date_from = filters.get('date_from', date.today().replace(day=1).strftime('%Y-%m-%d'))
        date_to   = filters.get('date_to',   date.today().strftime('%Y-%m-%d'))

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   l.start_time::date AS start_date,
                   l.end_time::date   AS end_date,
                   lt.leave_name      AS leave_type,
                   l.reason,
                   CASE l.approval_status
                       WHEN 0 THEN 'Pending'
                       WHEN 1 THEN 'Approved'
                       WHEN 2 THEN 'Rejected'
                       ELSE 'Unknown'
                   END AS approval_status
            FROM att_leave l
            JOIN personnel_employee e ON l.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            LEFT JOIN att_leave_type lt ON l.leave_type_id = lt.id
            WHERE l.start_time::date <= :date_to
              AND l.end_time::date   >= :date_from
            ORDER BY l.start_time DESC
        """)
        rows = self.db.execute(sql, {'date_from': date_from, 'date_to': date_to}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',         'label': 'Emp Code',    'type': 'text'},
            {'field': 'full_name',         'label': 'Full Name',   'type': 'text'},
            {'field': 'department',        'label': 'Department',  'type': 'text'},
            {'field': 'start_date',        'label': 'Start Date',  'type': 'date'},
            {'field': 'end_date',          'label': 'End Date',    'type': 'date'},
            {'field': 'leave_type',        'label': 'Leave Type',  'type': 'text'},
            {'field': 'approval_status',   'label': 'Status',      'type': 'text'},
        ]
        data = []
        for r in rows:
            m = r._mapping
            data.append({
                'emp_code':       m['emp_code'],
                'full_name':      m['full_name'],
                'department':     m['department'],
                'start_date':     str(m['start_date']) if m['start_date'] else '',
                'end_date':       str(m['end_date']) if m['end_date'] else '',
                'leave_type':     m['leave_type'] or 'Leave',
                'approval_status': m['approval_status'],
            })
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {'total_leave_records': len(data), 'date_from': date_from, 'date_to': date_to},
        }

    def attendance_shift_schedule(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Shift schedule overview"""
        total = 0
        try:
            from ..models.shift_management import ScheduleManagement
            query = self.db.query(ScheduleManagement)
            if filters.get('date_from'):
                query = query.filter(ScheduleManagement.start_date >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(ScheduleManagement.end_date <= filters['date_to'])
            schedules, total = self._paginate(query)
        except Exception:
            schedules = []

        columns = [
            {'field': 'emp_id',      'label': 'Employee ID',  'type': 'text'},
            {'field': 'shift_name',  'label': 'Shift',        'type': 'text'},
            {'field': 'start_date',  'label': 'Start Date',   'type': 'date'},
            {'field': 'end_date',    'label': 'End Date',     'type': 'date'},
        ]
        data = [{
            'emp_id':     getattr(s, 'emp_id', '') or '',
            'shift_name': getattr(s, 'shift_name', '') or '',
            'start_date': s.start_date.strftime('%Y-%m-%d') if getattr(s, 'start_date', None) else '',
            'end_date':   s.end_date.strftime('%Y-%m-%d') if getattr(s, 'end_date', None) else '',
        } for s in schedules]
        return {'columns': columns, 'data': data, 'total': total, 'summary': {'total_schedules': total}}

    def attendance_exceptions(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Attendance exceptions from att_exception table"""
        date_from = filters.get('date_from', date.today().replace(day=1).strftime('%Y-%m-%d'))
        date_to   = filters.get('date_to',   date.today().strftime('%Y-%m-%d'))

        sql = text("""
            SELECT e.emp_code,
                   (e.first_name || ' ' || e.last_name) AS full_name,
                   COALESCE(d.dept_name, '') AS department,
                   ex.att_date, ex.exception_type, ex.deviation_minutes,
                   ex.exception_note,
                   CASE ex.handle_action
                       WHEN 'approved' THEN 'Approved'
                       WHEN 'rejected' THEN 'Rejected'
                       ELSE 'Pending'
                   END AS handle_status
            FROM att_exception ex
            JOIN personnel_employee e ON ex.emp_id = e.id
            LEFT JOIN personnel_department d ON e.dept_id = d.id
            WHERE ex.att_date BETWEEN :date_from AND :date_to
            ORDER BY ex.att_date DESC, d.dept_name
        """)
        rows = self.db.execute(sql, {'date_from': date_from, 'date_to': date_to}).fetchall()

        if filters.get('department'):
            dept = filters['department'].lower()
            rows = [r for r in rows if dept in (r._mapping['department'] or '').lower()]

        columns = [
            {'field': 'emp_code',          'label': 'Emp Code',      'type': 'text'},
            {'field': 'full_name',         'label': 'Full Name',     'type': 'text'},
            {'field': 'department',        'label': 'Department',    'type': 'text'},
            {'field': 'att_date',          'label': 'Date',          'type': 'date'},
            {'field': 'exception_type',    'label': 'Exception',     'type': 'text'},
            {'field': 'deviation_minutes', 'label': 'Deviation (min)','type': 'number'},
            {'field': 'handle_status',     'label': 'Status',        'type': 'text'},
        ]
        data = []
        for r in rows:
            m = r._mapping
            data.append({
                'emp_code':          m['emp_code'],
                'full_name':         m['full_name'],
                'department':        m['department'],
                'att_date':          str(m['att_date']) if m['att_date'] else '',
                'exception_type':    m['exception_type'] or '',
                'deviation_minutes': m['deviation_minutes'] or 0,
                'handle_status':     m['handle_status'],
            })
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {'total_exceptions': len(data), 'date_from': date_from, 'date_to': date_to},
        }

    # ==================== ACCESS CONTROL ====================

    # ── ZKTeco event type labels ─────────────────────────────────────────────
    _AC_EVENT_TYPE = {
        0: 'Normal Access',    1: 'Fingerprint Access', 2: 'Card Access',
        3: 'Password Access',  4: 'Face Access',        5: 'Emergency Unlock',
        6: 'Emergency Lock',   7: 'Door Alarm',         8: 'Duress',
        9: 'Anti-Passback',   10: 'Interlock',
    }
    _AC_VERIFY   = {0: 'Password', 1: 'Fingerprint', 2: 'Face', 3: 'Card'}
    _AC_INOUT    = {0: 'In', 1: 'Out'}

    @staticmethod
    def _connectivity_status(last_contact, now_utc):
        """Derive human-readable connectivity status from last contact timestamp."""
        if last_contact is None:
            return 'Never Connected'
        lc = last_contact.replace(tzinfo=None) if last_contact.tzinfo else last_contact
        hours_ago = (now_utc - lc).total_seconds() / 3600
        if hours_ago <= 2:
            return 'Online'
        if hours_ago <= 24:
            return 'Warning'
        return 'Offline'

    def payroll_payslip_bulk(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk payslip listing — full salary breakdown per employee for a period."""
        period_id = filters.get('period_id') or self._latest_period_id(self.db)
        if not period_id:
            return {'columns': [], 'data': [], 'total': 0,
                    'summary': self._employee_roster_context(self.db)}

        params: Dict[str, Any] = {'pid': period_id}
        dept_clause = ""
        if filters.get('department'):
            dept_clause = "AND COALESCE(NULLIF(p.department,''), 'Unassigned') = :dept"
            params['dept'] = filters['department']

        rows = self.db.execute(text(f"""
            SELECT
                p.emp_code,
                COALESCE(p.badge_id, p.emp_code)                    AS badge_id,
                COALESCE(p.full_name,
                    TRIM(p.first_name || ' ' || p.last_name))       AS full_name,
                COALESCE(NULLIF(p.department,''), 'Unassigned')      AS department,
                COALESCE(NULLIF(p.position,''), '—')                 AS position,
                p.employment_type,
                p.personnel_type,
                s.id                                                  AS salary_id,
                COALESCE(s.basic_salary, 0)                           AS basic_salary,
                COALESCE(s.total_earnings, 0)                         AS total_earnings,
                COALESCE(s.total_deductions, 0)                       AS total_deductions,
                COALESCE(s.gross_salary, 0)                           AS gross_salary,
                COALESCE(s.net_salary, 0)                             AS net_salary,
                COALESCE(s.work_days, 0)                              AS work_days,
                COALESCE(s.present_days, 0)                           AS present_days,
                COALESCE(s.absent_days, 0)                            AS absent_days,
                COALESCE(s.leave_days, 0)                             AS leave_days,
                COALESCE(s.ot_hours, 0)                               AS ot_hours,
                COALESCE(s.late_minutes, 0)                           AS late_minutes,
                s.calc_status,
                s.is_final,
                s.calc_time,
                COALESCE(
                    NULLIF(TRIM(cu.full_name),''), cu.username
                )                                                     AS calc_by_name,
                COALESCE(
                    NULLIF(TRIM(vu.full_name),''), vu.username
                )                                                     AS verified_by_name
            FROM pay_salary s
            JOIN personnel p    ON s.emp_id = p.id
            LEFT JOIN users cu  ON s.calc_by = cu.id
            LEFT JOIN users vu  ON s.verified_by = vu.id
            WHERE s.period_id = :pid
              {dept_clause}
            ORDER BY p.department, p.full_name
        """), params).fetchall()

        columns = [
            {'field': 'badge_id',         'label': 'Badge ID',       'type': 'text'},
            {'field': 'full_name',         'label': 'Full Name',      'type': 'text'},
            {'field': 'department',        'label': 'Department',     'type': 'text'},
            {'field': 'position',          'label': 'Position',       'type': 'text'},
            {'field': 'employment_type',   'label': 'Emp. Type',      'type': 'text'},
            {'field': 'basic_salary',      'label': 'Basic',          'type': 'currency'},
            {'field': 'total_earnings',    'label': 'Earnings',       'type': 'currency'},
            {'field': 'total_deductions',  'label': 'Deductions',     'type': 'currency'},
            {'field': 'gross_salary',      'label': 'Gross',          'type': 'currency'},
            {'field': 'net_salary',        'label': 'Net',            'type': 'currency'},
            {'field': 'present_days',      'label': 'Present Days',   'type': 'number'},
            {'field': 'absent_days',       'label': 'Absent Days',    'type': 'number'},
            {'field': 'ot_hours',          'label': 'OT Hours',       'type': 'number'},
            {'field': 'calc_status',       'label': 'Status',         'type': 'text'},
            {'field': 'calc_by',           'label': 'Calculated By',  'type': 'text'},
        ]
        data = [{
            'badge_id':        r.badge_id or r.emp_code or '',
            'full_name':       r.full_name or '',
            'department':      r.department,
            'position':        r.position,
            'employment_type': r.employment_type or '',
            'basic_salary':    float(r.basic_salary),
            'total_earnings':  float(r.total_earnings),
            'total_deductions':float(r.total_deductions),
            'gross_salary':    float(r.gross_salary),
            'net_salary':      float(r.net_salary),
            'present_days':    float(r.present_days),
            'absent_days':     float(r.absent_days),
            'ot_hours':        float(r.ot_hours),
            'calc_status':     self._PAY_CALC_STATUS.get(str(r.calc_status or ''), str(r.calc_status or 'Pending')),
            'calc_by':         r.calc_by_name or '—',
        } for r in rows]

        meta = self._period_meta(self.db, period_id)
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                **meta,
                'total_employees':  len(data),
                'total_gross':      round(sum(r['gross_salary']    for r in data), 2),
                'total_net':        round(sum(r['net_salary']       for r in data), 2),
                'total_deductions': round(sum(r['total_deductions'] for r in data), 2),
                'finalized':        sum(1 for r in rows if r.is_final),
                'pending':          sum(1 for r in rows if not r.is_final),
            },
        }

    def payroll_bank_sheet(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Bank payment sheet — one row per employee with net salary for transfer."""
        period_id = filters.get('period_id') or self._latest_period_id(self.db)
        if not period_id:
            return {'columns': [], 'data': [], 'total': 0,
                    'summary': self._employee_roster_context(self.db)}

        rows = self.db.execute(text("""
            SELECT
                COALESCE(p.badge_id, p.emp_code)                    AS badge_id,
                p.emp_code,
                COALESCE(p.full_name,
                    TRIM(p.first_name || ' ' || p.last_name))       AS full_name,
                COALESCE(NULLIF(p.department,''), 'Unassigned')      AS department,
                COALESCE(NULLIF(p.position,''), '—')                 AS position,
                COALESCE(s.net_salary, 0)                            AS net_salary,
                s.calc_status,
                s.is_final
            FROM pay_salary s
            JOIN personnel p ON s.emp_id = p.id
            WHERE s.period_id = :pid
            ORDER BY p.department, p.full_name
        """), {'pid': period_id}).fetchall()

        columns = [
            {'field': 'badge_id',    'label': 'Badge ID',    'type': 'text'},
            {'field': 'full_name',   'label': 'Full Name',   'type': 'text'},
            {'field': 'department',  'label': 'Department',  'type': 'text'},
            {'field': 'position',    'label': 'Position',    'type': 'text'},
            {'field': 'net_salary',  'label': 'Net Salary',  'type': 'currency'},
            {'field': 'calc_status', 'label': 'Status',      'type': 'text'},
            {'field': 'is_final',    'label': 'Finalized',   'type': 'boolean'},
        ]
        data = [{
            'badge_id':   r.badge_id or r.emp_code,
            'full_name':  r.full_name or '',
            'department': r.department,
            'position':   r.position,
            'net_salary': float(r.net_salary),
            'calc_status':self._PAY_CALC_STATUS.get(str(r.calc_status or ''), str(r.calc_status or 'Pending')),
            'is_final':   bool(r.is_final),
        } for r in rows]

        meta = self._period_meta(self.db, period_id)
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                **meta,
                'total_employees': len(data),
                'total_net':       round(sum(r['net_salary'] for r in data), 2),
                'finalized':       sum(1 for r in rows if r.is_final),
                'pending':         sum(1 for r in rows if not r.is_final),
            },
        }

    def payroll_item_wise(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Item-wise salary breakdown — every earning and deduction line per employee."""
        period_id = filters.get('period_id') or self._latest_period_id(self.db)
        if not period_id:
            # Show pay item catalog from pay_item table even without a period
            catalog = self.db.execute(text("""
                SELECT i.item_name, i.item_type, i.calc_type,
                       COALESCE(i.amount, 0) AS amount,
                       ps.structure_name, i.is_taxable, i.is_mandatory
                FROM pay_item i
                JOIN pay_structure ps ON i.structure_id = ps.id
                ORDER BY i.item_type, i.sequence
            """)).fetchall()
            columns = [
                {'field': 'structure_name', 'label': 'Structure',  'type': 'text'},
                {'field': 'item_name',       'label': 'Item Name',  'type': 'text'},
                {'field': 'item_type',       'label': 'Type',       'type': 'text'},
                {'field': 'calc_type',       'label': 'Calc Type',  'type': 'text'},
                {'field': 'amount',          'label': 'Amount',     'type': 'currency'},
                {'field': 'is_taxable',      'label': 'Taxable',    'type': 'boolean'},
                {'field': 'is_mandatory',    'label': 'Mandatory',  'type': 'boolean'},
            ]
            data = [{
                'structure_name': r.structure_name,
                'item_name':      r.item_name,
                'item_type':      self._PAY_ITEM_TYPE.get(str(r.item_type or ''), str(r.item_type or '')),
                'calc_type':      str(r.calc_type or ''),
                'amount':         float(r.amount),
                'is_taxable':     bool(r.is_taxable),
                'is_mandatory':   bool(r.is_mandatory),
            } for r in catalog]
            ctx = self._employee_roster_context(self.db)
            ctx['catalog_items'] = len(data)
            return {'columns': columns, 'data': data, 'total': len(data), 'summary': ctx}

        rows = self.db.execute(text("""
            SELECT
                COALESCE(p.badge_id, p.emp_code)                    AS badge_id,
                COALESCE(p.full_name,
                    TRIM(p.first_name || ' ' || p.last_name))       AS full_name,
                COALESCE(NULLIF(p.department,''), 'Unassigned')      AS department,
                si.item_name,
                si.item_type,
                COALESCE(si.item_value, 0)                           AS amount,
                si.is_manual_adjustment,
                si.adjustment_reason,
                si.formula_used
            FROM pay_salary_item si
            JOIN pay_salary s  ON si.salary_id = s.id
            JOIN personnel p   ON s.emp_id = p.id
            WHERE s.period_id = :pid
            ORDER BY p.department, p.full_name, si.item_type,
                     COALESCE(si.calculation_order, 999)
        """), {'pid': period_id}).fetchall()

        columns = [
            {'field': 'badge_id',   'label': 'Badge ID',   'type': 'text'},
            {'field': 'full_name',  'label': 'Full Name',  'type': 'text'},
            {'field': 'department', 'label': 'Department', 'type': 'text'},
            {'field': 'item_name',  'label': 'Item',       'type': 'text'},
            {'field': 'item_type',  'label': 'Type',       'type': 'text'},
            {'field': 'amount',     'label': 'Amount',     'type': 'currency'},
            {'field': 'is_manual',  'label': 'Manual Adj.','type': 'boolean'},
            {'field': 'adj_reason', 'label': 'Adj. Reason','type': 'text'},
        ]
        data = [{
            'badge_id':   r.badge_id or '',
            'full_name':  r.full_name or '',
            'department': r.department,
            'item_name':  r.item_name or '',
            'item_type':  self._PAY_ITEM_TYPE.get(str(r.item_type or ''), str(r.item_type or '')),
            'amount':     float(r.amount),
            'is_manual':  bool(r.is_manual_adjustment),
            'adj_reason': r.adjustment_reason or '',
        } for r in rows]

        earnings    = sum(r['amount'] for r in data if r['item_type'] == 'Earning')
        deductions  = sum(r['amount'] for r in data if r['item_type'] == 'Deduction')
        meta = self._period_meta(self.db, period_id)

        # Aggregate totals by item name for management summary
        item_totals: Dict[str, float] = {}
        for r in data:
            item_totals[r['item_name']] = round(item_totals.get(r['item_name'], 0) + r['amount'], 2)

        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                **meta,
                'total_items':       len(data),
                'total_earnings':    round(earnings, 2),
                'total_deductions':  round(deductions, 2),
                'item_totals':       item_totals,
            },
        }

    def payroll_variance(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Period-over-period salary variance — highlights increases, decreases, and new/exited staff."""
        # Resolve period IDs — need two consecutive periods
        period_a = filters.get('period_a')
        period_b = filters.get('period_b')
        if not period_a or not period_b:
            periods = self.db.execute(text(
                "SELECT id, period_name FROM pay_period ORDER BY end_date DESC LIMIT 2"
            )).fetchall()
            if len(periods) >= 2:
                period_b, period_a = periods[0].id, periods[1].id  # b=current, a=previous
            else:
                ctx = self._employee_roster_context(self.db)
                ctx['message'] = 'Need at least 2 pay periods for variance analysis.'
                return {'columns': [], 'data': [], 'total': 0, 'summary': ctx}

        rows = self.db.execute(text("""
            SELECT
                COALESCE(p.badge_id, p.emp_code)                    AS badge_id,
                COALESCE(p.full_name,
                    TRIM(p.first_name || ' ' || p.last_name))       AS full_name,
                COALESCE(NULLIF(p.department,''), 'Unassigned')      AS department,
                COALESCE(sa.gross_salary, 0)                         AS gross_prev,
                COALESCE(sb.gross_salary, 0)                         AS gross_curr,
                COALESCE(sa.net_salary,   0)                         AS net_prev,
                COALESCE(sb.net_salary,   0)                         AS net_curr,
                COALESCE(sa.total_deductions, 0)                     AS ded_prev,
                COALESCE(sb.total_deductions, 0)                     AS ded_curr,
                CASE
                    WHEN sa.id IS NULL THEN 'New'
                    WHEN sb.id IS NULL THEN 'Exited'
                    ELSE 'Continued'
                END                                                   AS emp_status
            FROM personnel p
            LEFT JOIN pay_salary sa ON sa.emp_id = p.id AND sa.period_id = :pid_a
            LEFT JOIN pay_salary sb ON sb.emp_id = p.id AND sb.period_id = :pid_b
            WHERE sa.id IS NOT NULL OR sb.id IS NOT NULL
            ORDER BY p.department, p.full_name
        """), {'pid_a': period_a, 'pid_b': period_b}).fetchall()

        meta_a = self._period_meta(self.db, period_a)
        meta_b = self._period_meta(self.db, period_b)

        columns = [
            {'field': 'badge_id',      'label': 'Badge ID',          'type': 'text'},
            {'field': 'full_name',     'label': 'Full Name',         'type': 'text'},
            {'field': 'department',    'label': 'Department',        'type': 'text'},
            {'field': 'emp_status',    'label': 'Status',            'type': 'text'},
            {'field': 'net_prev',      'label': 'Net (Previous)',    'type': 'currency'},
            {'field': 'net_curr',      'label': 'Net (Current)',     'type': 'currency'},
            {'field': 'net_variance',  'label': 'Net Variance',      'type': 'currency'},
            {'field': 'variance_pct',  'label': 'Variance %',        'type': 'percentage'},
            {'field': 'gross_prev',    'label': 'Gross (Previous)',  'type': 'currency'},
            {'field': 'gross_curr',    'label': 'Gross (Current)',   'type': 'currency'},
        ]
        data = []
        for r in rows:
            net_prev = float(r.net_prev)
            net_curr = float(r.net_curr)
            variance = round(net_curr - net_prev, 2)
            var_pct  = round((variance / net_prev * 100), 2) if net_prev else 0
            data.append({
                'badge_id':     r.badge_id or '',
                'full_name':    r.full_name or '',
                'department':   r.department,
                'emp_status':   r.emp_status,
                'net_prev':     net_prev,
                'net_curr':     net_curr,
                'net_variance': variance,
                'variance_pct': var_pct,
                'gross_prev':   float(r.gross_prev),
                'gross_curr':   float(r.gross_curr),
            })

        increased  = sum(1 for r in data if r['net_variance'] > 0)
        decreased  = sum(1 for r in data if r['net_variance'] < 0)
        unchanged  = sum(1 for r in data if r['net_variance'] == 0 and r['emp_status'] == 'Continued')
        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                'previous_period':   meta_a.get('period_name', ''),
                'current_period':    meta_b.get('period_name', ''),
                'total_employees':   len(data),
                'increased':         increased,
                'decreased':         decreased,
                'unchanged':         unchanged,
                'new_employees':     sum(1 for r in data if r['emp_status'] == 'New'),
                'exited_employees':  sum(1 for r in data if r['emp_status'] == 'Exited'),
                'total_net_variance':round(sum(r['net_variance'] for r in data), 2),
            },
        }

    def payroll_contractor_cost(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Contractor payroll cost analysis — contractors vs staff cost breakdown."""
        period_id = filters.get('period_id') or self._latest_period_id(self.db)

        # Always show contractor headcount (even without period data)
        contractor_roster = self.db.execute(text("""
            SELECT
                COALESCE(p.badge_id, p.emp_code)                    AS badge_id,
                COALESCE(p.full_name,
                    TRIM(p.first_name || ' ' || p.last_name))       AS full_name,
                COALESCE(NULLIF(p.department,''), 'Unassigned')      AS department,
                COALESCE(NULLIF(p.position,''), '—')                 AS position,
                p.personnel_type,
                p.employment_type,
                p.hire_date,
                p.is_active,
                p.is_pob
            FROM personnel p
            WHERE UPPER(p.personnel_type) = 'CONTRACTOR'
            ORDER BY p.department, p.full_name
        """)).fetchall()

        if not period_id:
            columns = [
                {'field': 'badge_id',      'label': 'Badge ID',     'type': 'text'},
                {'field': 'full_name',     'label': 'Full Name',    'type': 'text'},
                {'field': 'department',    'label': 'Department',   'type': 'text'},
                {'field': 'position',      'label': 'Position',     'type': 'text'},
                {'field': 'hire_date',     'label': 'Hire Date',    'type': 'date'},
                {'field': 'is_pob',        'label': 'POB',          'type': 'boolean'},
            ]
            data = [{
                'badge_id':  r.badge_id or '',
                'full_name': r.full_name or '',
                'department':r.department,
                'position':  r.position,
                'hire_date': str(r.hire_date) if r.hire_date else '',
                'is_pob':    bool(r.is_pob),
            } for r in contractor_roster]
            ctx = self._employee_roster_context(self.db)
            ctx['total_contractors'] = len(data)
            ctx['no_period_data'] = True
            return {'columns': columns, 'data': data, 'total': len(data), 'summary': ctx}

        rows = self.db.execute(text("""
            SELECT
                COALESCE(p.badge_id, p.emp_code)                    AS badge_id,
                COALESCE(p.full_name,
                    TRIM(p.first_name || ' ' || p.last_name))       AS full_name,
                COALESCE(NULLIF(p.department,''), 'Unassigned')      AS department,
                COALESCE(NULLIF(p.position,''), '—')                 AS position,
                p.personnel_type,
                COALESCE(s.basic_salary,     0)                      AS basic_salary,
                COALESCE(s.gross_salary,     0)                      AS gross_salary,
                COALESCE(s.total_deductions, 0)                      AS total_deductions,
                COALESCE(s.net_salary,       0)                      AS net_salary,
                COALESCE(s.zone_hours,       0)                      AS zone_hours,
                COALESCE(s.hazard_days,      0)                      AS hazard_days,
                s.calc_status,
                s.contractor_flag
            FROM pay_salary s
            JOIN personnel p ON s.emp_id = p.id
            WHERE s.period_id = :pid
              AND UPPER(p.personnel_type) = 'CONTRACTOR'
            ORDER BY p.department, p.full_name
        """), {'pid': period_id}).fetchall()

        columns = [
            {'field': 'badge_id',        'label': 'Badge ID',     'type': 'text'},
            {'field': 'full_name',        'label': 'Full Name',    'type': 'text'},
            {'field': 'department',       'label': 'Department',   'type': 'text'},
            {'field': 'position',         'label': 'Position',     'type': 'text'},
            {'field': 'basic_salary',     'label': 'Basic',        'type': 'currency'},
            {'field': 'gross_salary',     'label': 'Gross',        'type': 'currency'},
            {'field': 'total_deductions', 'label': 'Deductions',   'type': 'currency'},
            {'field': 'net_salary',       'label': 'Net',          'type': 'currency'},
            {'field': 'zone_hours',       'label': 'Zone Hours',   'type': 'number'},
            {'field': 'hazard_days',      'label': 'Hazard Days',  'type': 'number'},
            {'field': 'calc_status',      'label': 'Status',       'type': 'text'},
        ]
        data = [{
            'badge_id':        r.badge_id or '',
            'full_name':       r.full_name or '',
            'department':      r.department,
            'position':        r.position,
            'basic_salary':    float(r.basic_salary),
            'gross_salary':    float(r.gross_salary),
            'total_deductions':float(r.total_deductions),
            'net_salary':      float(r.net_salary),
            'zone_hours':      float(r.zone_hours),
            'hazard_days':     float(r.hazard_days),
            'calc_status':     self._PAY_CALC_STATUS.get(str(r.calc_status or ''), str(r.calc_status or 'Pending')),
        } for r in rows]

        meta = self._period_meta(self.db, period_id)
        # Dept breakdown
        dept_totals: Dict[str, float] = {}
        for r in data:
            dept_totals[r['department']] = round(dept_totals.get(r['department'], 0) + r['net_salary'], 2)

        return {
            'columns': columns, 'data': data, 'total': len(data),
            'summary': {
                **meta,
                'total_contractors':     len(data),
                'total_contractor_roster': len(contractor_roster),
                'unpaid_contractors':    len(contractor_roster) - len(data),
                'total_gross':           round(sum(r['gross_salary'] for r in data), 2),
                'total_net':             round(sum(r['net_salary']   for r in data), 2),
                'dept_breakdown':        dept_totals,
            },
        }

    # ==================== VISITOR (continued) ====================

    def system_login_log(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """User login history"""
        query = (
            self.db.query(BaseOperationLog)
            .filter(BaseOperationLog.action == 'login')
        )
        if filters.get('date_from'):
            query = query.filter(BaseOperationLog.created_at >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(BaseOperationLog.created_at <= filters['date_to'])

        query = query.order_by(desc(BaseOperationLog.created_at))
        logs, total = self._paginate(query)
        columns = [
            {'field': 'timestamp',  'label': 'Time',       'type': 'datetime'},
            {'field': 'user',       'label': 'User',       'type': 'text'},
            {'field': 'ip_address', 'label': 'IP Address', 'type': 'text'},
        ]
        data = [{
            'timestamp':  l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else '',
            'user':       l.user.username if getattr(l, 'user', None) else '',
            'ip_address': l.ip_address or '',
        } for l in logs]
        return {
            'columns': columns, 'data': data,
            'total': total,
            'summary': {
                'total_logins': total,
            },
        }

    def system_data_audit(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Data change audit log"""
        query = self.db.query(BaseOperationLog)
        if filters.get('date_from'):
            query = query.filter(BaseOperationLog.created_at >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(BaseOperationLog.created_at <= filters['date_to'])
        if filters.get('module'):
            query = query.filter(BaseOperationLog.table_name == filters['module'])

        query = query.order_by(desc(BaseOperationLog.created_at))
        logs, total = self._paginate(query)
        columns = [
            {'field': 'timestamp',  'label': 'Time',       'type': 'datetime'},
            {'field': 'user',       'label': 'User',       'type': 'text'},
            {'field': 'module',     'label': 'Module',     'type': 'text'},
            {'field': 'action',     'label': 'Action',     'type': 'text'},
            {'field': 'target',     'label': 'Target',     'type': 'text'},
            {'field': 'old_values', 'label': 'Old Values', 'type': 'text'},
            {'field': 'new_values', 'label': 'New Values', 'type': 'text'},
        ]
        data = [{
            'timestamp':  l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else '',
            'user':       l.user.username if getattr(l, 'user', None) else '',
            'module':     l.table_name or '',
            'action':     l.action or '',
            'target':     f"{l.table_name}#{l.record_id}" if l.record_id else l.table_name or '',
            'old_values': (l.old_values or '')[:100],
            'new_values': (l.new_values or '')[:100],
        } for l in logs]
        return {
            'columns': columns, 'data': data,
            'total': total,
            'summary': {'total_changes': total},
        }

    def system_license_usage(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """System resource utilization summary"""
        total_users    = self.db.query(func.count(Personnel.id)).filter(Personnel.is_active == True).scalar() or 0
        total_devices  = 0  # No physical readers in a mobile-only deployment.

        columns = [
            {'field': 'resource',  'label': 'Resource', 'type': 'text'},
            {'field': 'used',      'label': 'Used',     'type': 'number'},
        ]
        data = [
            {'resource': 'Active Users',  'used': total_users},
            {'resource': 'Total Devices', 'used': total_devices},
        ]
        return {
            'columns': columns, 'data': data,
            'summary': {'active_users': total_users, 'total_devices': total_devices},
        }

    def system_api_usage(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """API usage by module"""
        query = self.db.query(
            BaseOperationLog.table_name.label('module'),
            func.count(BaseOperationLog.id).label('call_count'),
        ).group_by(BaseOperationLog.table_name)
        if filters.get('date_from'):
            query = query.filter(BaseOperationLog.created_at >= filters['date_from'])
        results = query.all()

        columns = [
            {'field': 'module',     'label': 'Module',      'type': 'text'},
            {'field': 'call_count', 'label': 'API Calls',   'type': 'number'},
        ]
        data = [{'module': r.module or 'Unknown', 'call_count': r.call_count or 0} for r in results]
        chart_data = {
            'labels': [r['module'] for r in data],
            'datasets': [{'label': 'API Calls', 'data': [r['call_count'] for r in data], 'backgroundColor': '#4F81BD'}],
        }
        return {
            'columns': columns, 'data': data, 'chart_data': chart_data,
            'summary': {'total_calls': sum(r['call_count'] for r in data)},
        }

    # ==================== ZONE SECURITY & AUDIT REPORTS ====================

