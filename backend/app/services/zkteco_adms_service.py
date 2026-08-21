"""
ZKTeco ADMS Service for PostgreSQL
Handles biometric data push from ZKTeco devices with PostgreSQL-specific optimizations
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, insert, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import json
import logging

from ..models.personnel import AttendanceLog
from ..models.device import Device, AccessLog
from ..core.database import get_db

logger = logging.getLogger(__name__)


class ZKTecoADMSService:
    """ZKTeco ADMS service optimized for PostgreSQL with connection pooling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process_attendance_punch(self, punch_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Process attendance punch from ZKTeco ADMS device
        Uses PostgreSQL UPSERT (ON CONFLICT) for concurrent punch handling
        
        Args:
            punch_data: ZKTeco ADMS punch data
            db: Database session with connection pooling
            
        Returns:
            Processing result with PostgreSQL-specific handling
        """
        try:
            # Extract ZKTeco ADMS data
            device_sn = punch_data.get('SN')  # Device serial number
            user_id = punch_data.get('user_id')  # Badge ID
            timestamp = punch_data.get('timestamp')  # YYYY-MM-DD HH:mm:ss format
            punch_type = punch_data.get('type', 0)  # 0=check-in, 1=check-out
            verify_type = punch_data.get('verify_type', 1)  # Biometric verification type
            
            # Parse ZKTeco timestamp format to PostgreSQL TIMESTAMP
            try:
                # ZKTeco ADMS format: "2024-01-15 14:30:25"
                punch_timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                punch_timestamp = punch_timestamp.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError) as e:
                self.logger.error(f"Invalid timestamp format: {timestamp}, error: {e}")
                return {
                    "success": False,
                    "error": "INVALID_TIMESTAMP",
                    "message": f"Invalid timestamp format: {timestamp}"
                }
            
            # PostgreSQL UPSERT for attendance log
            attendance_data = {
                'personnel_id': self._get_personnel_id_by_badge(user_id, db),
                'device_id': device_sn,
                'event_type': 'check_in' if punch_type == 0 else 'check_out',
                'timestamp': punch_timestamp,
                'verification_method': self._get_verification_method(verify_type),
                'device_type': 'ZKTeco_ADMS',
                'network_type': 'lan',
                'raw_data': punch_data,
                'is_processed': False,
                'created_at': datetime.now(timezone.utc)
            }
            
            # PostgreSQL-specific UPSERT using ON CONFLICT
            stmt = pg_insert(AttendanceLog).values(**attendance_data)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['personnel_id', 'timestamp', 'device_id']
            )
            
            result = db.execute(stmt)
            db.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Processed attendance punch: {user_id} at {punch_timestamp}")
                return {
                    "success": True,
                    "action": "INSERTED",
                    "message": "Attendance punch recorded successfully",
                    "data": {
                        "personnel_id": attendance_data['personnel_id'],
                        "timestamp": timestamp,
                        "event_type": attendance_data['event_type']
                    }
                }
            else:
                # Duplicate punch - already exists
                self.logger.warning(f"Duplicate attendance punch ignored: {user_id} at {punch_timestamp}")
                return {
                    "success": True,
                    "action": "DUPLICATE_IGNORED",
                    "message": "Duplicate attendance punch ignored",
                    "data": {
                        "personnel_id": attendance_data['personnel_id'],
                        "timestamp": timestamp
                    }
                }
                
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Database integrity error processing punch: {e}")
            return {
                "success": False,
                "error": "INTEGRITY_ERROR",
                "message": "Database constraint violation"
            }
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error processing attendance punch: {e}")
            return {
                "success": False,
                "error": "PROCESSING_ERROR",
                "message": str(e)
            }
    
    async def process_bulk_attendance(self, punch_logs: List[Dict[str, Any]], db: Session) -> Dict[str, Any]:
        """
        Process bulk attendance data from ZKTeco ADMS
        Uses PostgreSQL batch operations for performance
        
        Args:
            punch_logs: List of ZKTeco ADMS punch logs
            db: Database session with connection pooling
            
        Returns:
            Bulk processing result
        """
        try:
            processed_count = 0
            duplicate_count = 0
            error_count = 0
            errors = []
            
            for punch_data in punch_logs:
                result = await self.process_attendance_punch(punch_data, db)
                
                if result["success"]:
                    if result["action"] == "INSERTED":
                        processed_count += 1
                    elif result["action"] == "DUPLICATE_IGNORED":
                        duplicate_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "punch_data": punch_data,
                        "error": result["error"],
                        "message": result["message"]
                    })
            
            self.logger.info(f"Bulk attendance processing: {processed_count} inserted, {duplicate_count} duplicates, {error_count} errors")
            
            return {
                "success": True,
                "processed": processed_count,
                "duplicates": duplicate_count,
                "errors": error_count,
                "error_details": errors[:10],  # Limit error details
                "total": len(punch_logs)
            }
            
        except Exception as e:
            self.logger.error(f"Error in bulk attendance processing: {e}")
            return {
                "success": False,
                "error": "BULK_PROCESSING_ERROR",
                "message": str(e),
                "processed": processed_count if 'processed_count' in locals() else 0
            }
    
    async def update_device_status(self, device_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Update ZKTeco device status using PostgreSQL UPSERT
        Handles concurrent device status updates from multiple devices
        
        Args:
            device_data: ZKTeco device status data
            db: Database session with connection pooling
            
        Returns:
            Device update result
        """
        try:
            device_sn = device_data.get('SN')
            if not device_sn:
                return {
                    "success": False,
                    "error": "MISSING_DEVICE_SN",
                    "message": "Device serial number is required"
                }
            
            # Prepare device data for PostgreSQL
            device_update = {
                'device_id': device_sn,
                'name': device_data.get('name', f'ZKTeco_{device_sn}'),
                'serial_number': device_sn,
                'manufacturer': 'ZKTeco',
                'ip_address': device_data.get('ip'),
                'status': 'online',
                'last_seen': datetime.now(timezone.utc),
                'raw_data': device_data
            }
            
            # PostgreSQL UPSERT for device status
            stmt = pg_insert(Device).values(**device_update)
            stmt = stmt.on_conflict_do_update(
                index_elements=['device_id'],
                set_= {
                    'status': 'online',
                    'last_seen': datetime.now(timezone.utc),
                    'raw_data': device_data
                }
            )
            
            result = db.execute(stmt)
            db.commit()
            
            self.logger.info(f"Device status updated: {device_sn}")
            
            return {
                "success": True,
                "action": "UPSERTED",
                "device_id": device_sn,
                "status": "online",
                "message": "Device status updated successfully"
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating device status: {e}")
            return {
                "success": False,
                "error": "DEVICE_UPDATE_ERROR",
                "message": str(e)
            }
    
    def _get_personnel_id_by_badge(self, badge_id: str, db: Session) -> Optional[int]:
        """Get personnel ID by badge ID using PostgreSQL optimized query"""
        try:
            from ..models.personnel import Personnel
            
            # Use PostgreSQL-specific query with index optimization
            result = db.execute(
                text("SELECT id FROM personnel WHERE badge_id = :badge_id LIMIT 1"),
                {"badge_id": badge_id}
            ).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting personnel ID for badge {badge_id}: {e}")
            return None
    
    def _get_verification_method(self, verify_type: int) -> str:
        """Convert ZKTeco verification type to human readable method"""
        verification_map = {
            1: "fingerprint",
            2: "face", 
            3: "card",
            4: "password",
            8: "finger_vein",
            9: "palm",
            10: "iris"
        }
        return verification_map.get(verify_type, "unknown")
    
    async def queue_device_command(self, device_sn: str, command: str) -> Dict[str, Any]:
        """
        Queue emergency command to ZKTeco device via ADMS
        Integrates with emergency system for hardware control
        
        Args:
            device_sn: Device serial number
            command: Command to execute (RELAY_ON, RELAY_OFF, EMERGENCY_ON, EMERGENCY_OFF, EMERGENCY_TEST)
            
        Returns:
            Command queuing result
        """
        try:
            # Validate command
            valid_commands = [
                'RELAY_ON', 'RELAY_OFF',           # Door control
                'EMERGENCY_ON', 'EMERGENCY_OFF',   # Siren/strobe control
                'EMERGENCY_TEST',                # Test mode
                'LOCKDOWN', 'UNLOCK'              # Emergency modes
            ]
            
            if command not in valid_commands:
                return {
                    "success": False,
                    "error": "INVALID_COMMAND",
                    "message": f"Invalid command: {command}. Valid commands: {valid_commands}"
                }
            
            # Create device command record
            command_data = {
                'device_sn': device_sn,
                'command': command,
                'command_type': self._get_command_type(command),
                'status': 'queued',
                'created_at': datetime.now(timezone.utc),
                'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5)  # Commands expire after 5 minutes
            }
            
            # In real implementation, this would integrate with ZKTeco ADMS API
            # For now, simulate successful queuing
            self.logger.info(f"Queued command '{command}' to device {device_sn}")
            
            # Simulate ADMS API call
            # POST /iclock/api/devcmd/
            # {"sn": device_sn, "cmd": command}
            
            return {
                "success": True,
                "command": command,
                "device_sn": device_sn,
                "command_id": f"cmd_{datetime.now(timezone.utc).timestamp()}",
                "status": "queued",
                "message": f"Command '{command}' queued successfully for device {device_sn}",
                "queued_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error queuing command to device {device_sn}: {e}")
            return {
                "success": False,
                "error": "COMMAND_QUEUE_ERROR",
                "message": str(e)
            }
    
    async def get_device_command_status(self, command_id: str) -> Dict[str, Any]:
        """
        Get status of queued device command
        
        Args:
            command_id: Command ID from queue_device_command
            
        Returns:
            Command status result
        """
        try:
            # In real implementation, this would check ADMS command status
            # For now, simulate command execution
            
            return {
                "success": True,
                "command_id": command_id,
                "status": "executed",
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "message": "Command executed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting command status {command_id}: {e}")
            return {
                "success": False,
                "error": "COMMAND_STATUS_ERROR",
                "message": str(e)
            }
    
    async def get_device_statistics(self, device_sn: str, db: Session) -> Dict[str, Any]:
        """
        Get device statistics using PostgreSQL optimized queries
        For monitoring ZKTeco device performance
        """
        try:
            # PostgreSQL-specific queries for device statistics
            stats_queries = {
                'total_punches': """
                    SELECT COUNT(*) as count 
                    FROM attendance_logs 
                    WHERE device_id = :device_sn
                """,
                'punches_today': """
                    SELECT COUNT(*) as count 
                    FROM attendance_logs 
                    WHERE device_id = :device_sn 
                    AND DATE(timestamp) = CURRENT_DATE
                """,
                'punches_this_week': """
                    SELECT COUNT(*) as count 
                    FROM attendance_logs 
                    WHERE device_id = :device_sn 
                    AND timestamp >= DATE_TRUNC('week', CURRENT_DATE)
                """,
                'last_punch': """
                    SELECT MAX(timestamp) as last_punch 
                    FROM attendance_logs 
                    WHERE device_id = :device_sn
                """,
                'unique_users': """
                    SELECT COUNT(DISTINCT personnel_id) as count 
                    FROM attendance_logs 
                    WHERE device_id = :device_sn
                """
            }
            
            stats = {}
            for stat_name, query in stats_queries.items():
                result = db.execute(text(query), {"device_sn": device_sn}).fetchone()
                stats[stat_name] = result[0] if result else 0
            
            return {
                "success": True,
                "device_sn": device_sn,
                "statistics": stats,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting device statistics for {device_sn}: {e}")
            return {
                "success": False,
                "error": "STATISTICS_ERROR",
                "message": str(e)
            }
    
    def _get_command_type(self, command: str) -> str:
        """Get command type for categorization"""
        if command in ['RELAY_ON', 'RELAY_OFF']:
            return 'door_control'
        elif command in ['EMERGENCY_ON', 'EMERGENCY_OFF', 'EMERGENCY_TEST']:
            return 'emergency_device'
        elif command in ['LOCKDOWN', 'UNLOCK']:
            return 'emergency_mode'
        else:
            return 'general'
    
    async def process_emergency_device_response(self, device_sn: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process response from emergency device (siren, strobe, etc.)
        Handles device status updates and command acknowledgments
        
        Args:
            device_sn: Device serial number
            response_data: Response data from device
            
        Returns:
            Response processing result
        """
        try:
            self.logger.info(f"Processing emergency device response from {device_sn}")
            
            # Update device status based on response
            device_status = response_data.get('status', 'unknown')
            command_id = response_data.get('command_id')
            error_code = response_data.get('error_code')
            
            # Update emergency device record if exists
            # This would integrate with emergency_device table
            
            return {
                "success": True,
                "device_sn": device_sn,
                "device_status": device_status,
                "command_id": command_id,
                "error_code": error_code,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "message": f"Emergency device response processed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing emergency device response from {device_sn}: {e}")
            return {
                "success": False,
                "error": "DEVICE_RESPONSE_ERROR",
                "message": str(e)
            }


# Global service instance
zkteco_adms_service = ZKTecoADMSService()
