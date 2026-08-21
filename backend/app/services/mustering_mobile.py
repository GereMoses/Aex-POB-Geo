"""
Mobile Mustering Service
Mobile capabilities for mustering system - GPS tracking, mobile check-ins, photo capture
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import json
import base64
import requests

from app.models.biotime_models import (
    MusteringEvent, MusteringLog, PersonnelEmployee
)
from app.models.zone import Zone

logger = logging.getLogger(__name__)

class MobileMusteringService:
    """Mobile mustering service for field operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_mobile_checkin(
        self,
        event_id: int,
        emp_code: str,
        gps_coordinates: str,
        photo_base64: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        checked_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Register mobile check-in for mustering
        """
        try:
            # Validate event exists and is active
            event = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.id == event_id,
                    MusteringEvent.status == 0  # Active
                )
            ).first()
            
            if not event:
                raise ValueError(f"Active mustering event {event_id} not found")
            
            # Validate employee exists
            employee = self.db.query(PersonnelEmployee).filter(
                PersonnelEmployee.emp_code == emp_code
            ).first()
            
            if not employee:
                raise ValueError(f"Employee {emp_code} not found")
            
            # Create mobile check-in log
            mobile_log = MusteringLog(
                event_id=event_id,
                emp_code=emp_code,
                emp_name=f"{employee.first_name or ''} {employee.last_name}".strip(),
                check_time=datetime.utcnow(),
                device_sn=device_info.get('device_sn') if device_info else 'MOBILE_APP',
                device_alias=device_info.get('device_name') if device_info else 'Mobile App',
                status=1,  # Safe
                gps=gps_coordinates,
                photo=photo_base64,
                notes=notes
            )
            
            self.db.add(mobile_log)
            self.db.commit()
            
            # Update event headcount
            self._update_event_headcount(event_id)
            
            logger.info(f"Mobile check-in registered: {emp_code} for event {event_id}")
            
            return {
                "success": True,
                "checkin_id": mobile_log.id,
                "emp_code": emp_code,
                "emp_name": f"{employee.first_name or ''} {employee.last_name}".strip(),
                "check_time": mobile_log.check_time.isoformat(),
                "gps": gps_coordinates,
                "status": "safe",
                "device_info": device_info
            }
            
        except ValueError as e:
            logger.error(f"Validation error in mobile check-in: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in register_mobile_checkin: {e}")
            self.db.rollback()
            raise
    
    def get_mobile_checkins(
        self,
        event_id: int,
        status: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get mobile check-ins for an event
        """
        try:
            # Validate event exists
            event = self.db.query(MusteringEvent).filter(MusteringEvent.id == event_id).first()
            if not event:
                raise ValueError(f"Mustering event {event_id} not found")
            
            # Query mobile check-ins
            query = self.db.query(MusteringLog).filter(
                and_(
                    MusteringLog.event_id == event_id,
                    MusteringLog.device_sn.like('MOBILE_%')  # Mobile check-ins
                )
            )
            
            if status is not None:
                query = query.filter(MusteringLog.status == status)
            
            if start_time:
                query = query.filter(MusteringLog.check_time >= start_time)
            
            if end_time:
                query = query.filter(MusteringLog.check_time <= end_time)
            
            checkins = query.order_by(desc(MusteringLog.check_time)).limit(limit).all()
            
            result = []
            for checkin in checkins:
                result.append({
                    "checkin_id": checkin.id,
                    "emp_code": checkin.emp_code,
                    "emp_name": checkin.emp_name,
                    "check_time": checkin.check_time,
                    "gps": checkin.gps,
                    "photo": checkin.photo,
                    "status": checkin.status,
                    "device_sn": checkin.device_sn,
                    "device_alias": checkin.device_alias,
                    "notes": checkin.notes,
                    "response_time": self._calculate_response_time(checkin, event)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting mobile check-ins: {e}")
            raise
    
    def upload_emergency_photo(
        self,
        event_id: int,
        emp_code: str,
        photo_base64: str,
        gps_coordinates: str,
        taken_by: Optional[int] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload emergency photo during mustering
        """
        try:
            # Validate event exists and is active
            event = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.id == event_id,
                    MusteringEvent.status == 0  # Active
                )
            ).first()
            
            if not event:
                raise ValueError(f"Active mustering event {event_id} not found")
            
            # Validate employee exists
            employee = self.db.query(PersonnelEmployee).filter(
                PersonnelEmployee.emp_code == emp_code
            ).first()
            
            if not employee:
                raise ValueError(f"Employee {emp_code} not found")
            
            # Create or update emergency photo log
            existing_log = self.db.query(MusteringLog).filter(
                and_(
                    MusteringEvent.id == event_id,
                    MusteringLog.emp_code == emp_code,
                    MusteringLog.device_sn.like('EMERGENCY_PHOTO_%')
                )
            ).first()
            
            if existing_log:
                # Update existing log
                existing_log.photo = photo_base64
                existing_log.gps = gps_coordinates
                existing_log.notes = description
                existing_log.check_time = datetime.utcnow()
                self.db.commit()
                
                log_id = existing_log.id
            else:
                # Create new emergency photo log
                emergency_log = MusteringLog(
                    event_id=event_id,
                    emp_code=emp_code,
                    emp_name=f"{employee.first_name or ''} {employee.last_name}".strip(),
                    check_time=datetime.utcnow(),
                    device_sn='EMERGENCY_UPLOAD',
                    device_alias='Emergency Photo Upload',
                    status=1,  # Safe (photo indicates person is accounted for)
                    gps=gps_coordinates,
                    photo=photo_base64,
                    notes=description
                )
                
                self.db.add(emergency_log)
                self.db.commit()
                log_id = emergency_log.id
            
            # Update event headcount
            self._update_event_headcount(event_id)
            
            logger.info(f"Emergency photo uploaded for {emp_code} in event {event_id}")
            
            return {
                "success": True,
                "photo_id": log_id,
                "emp_code": emp_code,
                "upload_time": datetime.utcnow().isoformat(),
                "gps": gps_coordinates,
                "status": "safe"
            }
            
        except ValueError as e:
            logger.error(f"Validation error in emergency photo upload: {e}")
            raise
        except Exception as e:
            logger.error(f"Error uploading emergency photo: {e}")
            self.db.rollback()
            raise
    
    def get_missing_personnel_locations(
        self,
        event_id: int,
        last_known_location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get last known locations for missing personnel
        """
        try:
            # Get missing personnel for the event
            missing_logs = self.db.query(MusteringLog).filter(
                and_(
                    MusteringEvent.id == event_id,
                    MusteringLog.status == 0  # Missing
                )
            ).all()
            
            if not missing_logs:
                return []
            
            result = []
            for log in missing_logs:
                # Get last known location for this person
                last_known = self._get_last_known_location(log.emp_code)
                
                location_data = {
                    "emp_code": log.emp_code,
                    "emp_name": log.emp_name,
                    "last_check_time": log.check_time,
                    "last_gps": log.gps,
                    "last_known_location": last_known,
                    "time_since_last_check": self._calculate_time_since(log.check_time),
                    "status": "missing"
                }
                result.append(location_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting missing personnel locations: {e}")
            raise
    
    def send_emergency_alert(
        self,
        event_id: int,
        emp_codes: List[str],
        message: str,
        alert_type: str = "MISSING_PERSONNEL",
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        """
        Send emergency alert for missing personnel
        """
        try:
            # Validate event exists and is active
            event = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.id == event_id,
                    MusteringEvent.status == 0  # Active
                )
            ).first()
            
            if not event:
                raise ValueError(f"Active mustering event {event_id} not found")
            
            # Create emergency alert log
            alert_log = MusteringLog(
                event_id=event_id,
                emp_code=", ".join(emp_codes),
                emp_name="Multiple Personnel",
                check_time=datetime.utcnow(),
                device_sn="EMERGENCY_ALERT",
                device_alias="Emergency Alert System",
                status=0,  # Missing (alert indicates missing)
                notes=f"EMERGENCY: {message} - Personnel: {', '.join(emp_codes)}"
            )
            
            self.db.add(alert_log)
            self.db.commit()
            
            # Update event headcount
            self._update_event_headcount(event_id)
            
            # Send notifications (in real implementation, this would trigger SMS/email alerts)
            logger.warning(f"EMERGENCY ALERT: {message} - Personnel: {', '.join(emp_codes)}")
            
            return {
                "success": True,
                "alert_id": alert_log.id,
                "message": message,
                "alert_type": alert_type,
                "priority": priority,
                "emp_codes": emp_codes,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ValueError as e:
            logger.error(f"Validation error in emergency alert: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending emergency alert: {e}")
            self.db.rollback()
            raise
    
    def get_mobile_mustering_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        zone_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get mobile mustering statistics
        """
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Query mobile check-ins
            query = self.db.query(MusteringLog).filter(
                and_(
                    MusteringLog.check_time >= start_date,
                    MusteringLog.check_time <= end_date,
                    MusteringLog.device_sn.like('MOBILE_%')
                )
            )
            
            if zone_id:
                # Get events in specified zone
                zone_events = self.db.query(MusteringEvent).filter(
                    MusteringEvent.zone_id == zone_id,
                    MusteringEvent.start_time >= start_date,
                    MusteringEvent.start_time <= end_date
                ).all()
                
                event_ids = [event.id for event in zone_events]
                if event_ids:
                    query = query.filter(MusteringLog.event_id.in_(event_ids))
            
            checkins = query.order_by(desc(MusteringLog.check_time)).all()

            if not checkins:
                return {
                    "total_checkins": 0,
                    "mobile_usage": 0,
                    "photo_uploads": 0,
                    "emergency_alerts": 0,
                    "unique_users": 0,
                    "avg_checkin_time": 0
                }
            
            # Calculate statistics
            total_checkins = len(checkins)
            mobile_checkins = len([c for c in checkins if 'MOBILE_' in c.device_sn])
            photo_uploads = len([c for c in checkins if 'EMERGENCY_PHOTO_' in c.device_sn])
            emergency_alerts = len([c for c in checkins if 'EMERGENCY_ALERT_' in c.device_sn])
            unique_users = len(set(c.emp_code for c in checkins))
            
            # Calculate average check-in time
            checkin_times = []
            for checkin in checkins:
                if checkin.event and checkin.event.start_time:
                    response_time = (checkin.check_time - checkin.event.start_time).total_seconds() / 60
                    checkin_times.append(response_time)
            
            avg_checkin_time = sum(checkin_times) / len(checkin_times) if checkin_times else 0
            
            return {
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "total_checkins": total_checkins,
                "mobile_usage": round((mobile_checkins / total_checkins) * 100, 2) if total_checkins > 0 else 0,
                "photo_uploads": round((photo_uploads / total_checkins) * 100, 2) if total_checkins > 0 else 0,
                "emergency_alerts": round((emergency_alerts / total_checkins) * 100, 2) if total_checkins > 0 else 0,
                "unique_users": unique_users,
                "avg_checkin_time": round(avg_checkin_time, 2),
                "zone_breakdown": self._get_mobile_stats_by_zone(checkins)
            }

        except Exception as e:
            logger.error(f"Error getting mobile mustering statistics: {e}")
            raise
    
    def _update_event_headcount(self, event_id: int):
        """Update event headcount after mobile check-in"""
        try:
            event = self.db.query(MusteringEvent).filter(MusteringEvent.id == event_id).first()
            if not event:
                return
            
            # Get current headcount
            logs = self.db.query(MusteringLog).filter(MusteringEvent.id == event_id).all()
            
            total_safe = len([log for log in logs if log.status == 1])
            total_injured = len([log for log in logs if log.status == 2])
            
            # Update event
            event.total_safe = total_safe
            event.total_injured = total_injured
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating event headcount: {e}")
    
    def _calculate_response_time(self, log: MusteringLog, event: MusteringEvent) -> float:
        """Calculate response time from check-in to event start"""
        if not log.check_time or not event.start_time:
            return 0.0
        
        return (log.check_time - event.start_time).total_seconds() / 60
    
    def _calculate_time_since(self, check_time: datetime) -> str:
        """Calculate time since check-in"""
        if not check_time:
            return "Unknown"
        
        delta = datetime.utcnow() - check_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m ago"
        elif hours > 0:
            return f"{hours}h {minutes}m ago"
        else:
            return f"{minutes}m ago"
    
    def _get_last_known_location(self, emp_code: str) -> str:
        """Get last known location for employee"""
        try:
            last_log = self.db.query(MusteringLog).filter(
                and_(
                    MusteringLog.emp_code == emp_code,
                    MusteringLog.status.in_([1, 2])  # Safe or Injured
                )
            ).order_by(desc(MusteringLog.check_time)).first()
            
            if last_log and last_log.gps:
                return f"{last_log.gps} (Last seen: {self._calculate_time_since(last_log.check_time)})"
            
            return "No previous location data"
            
        except Exception as e:
            logger.error(f"Error getting last known location: {e}")
            return "Unknown"
    
    def _get_mobile_stats_by_zone(self, checkins: List) -> Dict[str, Any]:
        """Get mobile statistics broken down by zone"""
        zone_stats = {}
        
        for checkin in checkins:
            if checkin.event and checkin.event.zone:
                zone_id = checkin.event.zone_id
                zone_name = checkin.event.zone.name if checkin.event.zone else 'Unknown'
                
                if zone_id not in zone_stats:
                    zone_stats[zone_id] = {
                        'zone_name': zone_name,
                        'total_checkins': 0,
                        'mobile_checkins': 0,
                        'photo_uploads': 0,
                        'emergency_alerts': 0
                    }
                
                zone_stats[zone_id]['total_checkins'] += 1
                if 'MOBILE_' in checkin.device_sn:
                    zone_stats[zone_id]['mobile_checkins'] += 1
                if 'EMERGENCY_PHOTO_' in checkin.device_sn:
                    zone_stats[zone_id]['photo_uploads'] += 1
                if 'EMERGENCY_ALERT_' in checkin.device_sn:
                    zone_stats[zone_id]['emergency_alerts'] += 1
        
        return zone_stats
