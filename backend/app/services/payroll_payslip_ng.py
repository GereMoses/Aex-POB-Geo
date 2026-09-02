"""
Statutory payslip PDF generator (reportlab — pure Python, no system deps).

The legacy payslip service relies on weasyprint, which is not installed (heavy
cairo/pango libs), so it never produced output. This builds a clean, print-ready
payslip straight from the persisted PaySalary + line items + compensation.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Optional

from sqlalchemy.orm import Session

from ..models.payroll import PaySalary, PaySalaryItem, PayPeriod, PayItemType
from ..models.personnel import Personnel
from .payroll_run_ng import get_active_compensation

COMPANY = "Apex POB"


def _naira(v) -> str:
    # Use the "NGN" code rather than the ₦ glyph — the core PDF fonts (Helvetica)
    # have no naira glyph, which would render as a missing-character box.
    return f"NGN {float(v or 0):,.2f}"


def generate_payslip_pdf(db: Session, salary_id: int) -> Optional[bytes]:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer)

    sal = db.query(PaySalary).filter(PaySalary.id == salary_id).first()
    if not sal:
        return None
    emp = db.query(Personnel).filter(Personnel.id == sal.emp_id).first()
    period = db.query(PayPeriod).filter(PayPeriod.id == sal.period_id).first()
    comp = get_active_compensation(db, sal.emp_id, period.start_date if period else date.today())
    items = (db.query(PaySalaryItem).filter(PaySalaryItem.salary_id == salary_id)
             .order_by(PaySalaryItem.calculation_order).all())

    earnings = [(i.item_name, i.item_value) for i in items if i.item_type == PayItemType.EARNING]
    deductions = [(i.item_name, i.item_value) for i in items if i.item_type == PayItemType.DEDUCTION]

    emp_name = (getattr(emp, "full_name", None)
                or f"{getattr(emp, 'first_name', '') or ''} {getattr(emp, 'last_name', '') or ''}".strip()
                or "—")
    emp_code = getattr(emp, "emp_code", None) or "—"

    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Title"], fontSize=15, spaceAfter=2)
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    lbl = ParagraphStyle("lbl", parent=styles["Normal"], fontSize=8.5, textColor=colors.grey)
    val = ParagraphStyle("val", parent=styles["Normal"], fontSize=9.5)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm, title=f"Payslip {emp_code}")
    flow = []
    flow.append(Paragraph(COMPANY, h))
    flow.append(Paragraph(f"PAYSLIP — {period.period_name if period else ''}", sub))
    flow.append(Spacer(1, 8))

    # Employee + statutory identity block
    def cell(label, value):
        return [Paragraph(label, lbl), Paragraph(str(value or "—"), val)]
    ident = Table([
        cell("Employee", emp_name) + cell("Staff ID", emp_code),
        cell("Grade", getattr(comp, "grade", None)) + cell("Pay date", period.pay_date if period and period.pay_date else "—"),
        cell("TIN", getattr(comp, "tin", None)) + cell("RSA PIN", getattr(comp, "rsa_pin", None)),
        cell("PFA", getattr(comp, "pfa_name", None)) + cell("Tax state", getattr(comp, "tax_state", None)),
        cell("Bank", getattr(comp, "bank_name", None)) + cell("Account", getattr(comp, "bank_account_no", None)),
    ], colWidths=[28 * mm, 55 * mm, 28 * mm, 55 * mm])
    ident.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    flow.append(ident)
    flow.append(Spacer(1, 10))

    # Earnings / deductions side by side
    def money_table(title, rows, total_label, total):
        data = [[title, ""]]
        for n, v in rows:
            data.append([n, _naira(v)])
        data.append([total_label, _naira(total)])
        t = Table(data, colWidths=[52 * mm, 33 * mm])
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d2137")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("LINEABOVE", (0, -1), (-1, -1), 0.6, colors.grey),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    total_e = sum((v for _, v in earnings), 0)
    total_d = sum((v for _, v in deductions), 0)
    side = Table([[money_table("EARNINGS", earnings, "Gross", total_e),
                   money_table("DEDUCTIONS", deductions, "Total Deductions", total_d)]],
                 colWidths=[88 * mm, 88 * mm])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    flow.append(side)
    flow.append(Spacer(1, 10))

    # Net pay banner
    net = Table([["NET PAY", _naira(sal.net_salary)]], colWidths=[120 * mm, 56 * mm])
    net.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1a7f37")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (0, 0), 10),
    ]))
    flow.append(net)
    flow.append(Spacer(1, 8))

    emp_pension = float((comp.basic + comp.housing + comp.transport)) * 0.10 if comp else 0
    flow.append(Paragraph(
        f"Employer contributions (not deducted from you): Pension {_naira(emp_pension)}. "
        f"Status: {sal.calc_status.value if sal.calc_status else 'pending'}. "
        f"This is a system-generated payslip from {COMPANY}.", sub))

    doc.build(flow)
    return buf.getvalue()
