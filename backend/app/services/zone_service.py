"""
Enhanced Zone Service for Zones-Only Architecture

This service handles the simplified zone management system where zones are the primary
geographical concept for device assignment and personnel access control.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class ZoneService:
    """Enhanced service for zones-only architecture"""
    
    def __init__(self):
        pass
    
    async def get_zones(
        self, 
        db: Session,
        skip: int = 0,
        limit: int = 100,
        state: Optional[str] = None,
        zone_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get zones with optional filtering
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            state: Filter by state
            zone_type: Filter by zone type
            status: Filter by status
            
        Returns:
            List of zones with their details
        """
        try:
            # Import here to avoid circular imports
            from ..models.zone import Zone
            
            logger.info(f"Getting zones with filters: state={state}, zone_type={zone_type}, status={status}")
            
            query = db.query(Zone).filter(Zone.is_active == True)
            
            # Apply filters
            if state:
                query = query.filter(Zone.state == state)
            if zone_type:
                query = query.filter(Zone.zone_type == zone_type)
            if status:
                query = query.filter(Zone.status == status)
            
            # Apply pagination
            zones = query.offset(skip).limit(limit).all()
            logger.info(f"Found {len(zones)} zones")
            
            result = []
            for zone in zones:
                # Get device count for this zone (temporarily disabled)
                device_count = 0
                
                result.append({
                    "id": zone.id,
                    "name": zone.name,
                    "code": zone.code,
                    "zone_type": zone.zone_type,
                    "description": zone.description,
                    "status": zone.status,
                    "state": zone.state,
                    "address": zone.address,
                    "latitude": zone.latitude,
                    "longitude": zone.longitude,
                    "max_capacity": zone.max_capacity,
                    "current_occupancy": zone.current_occupancy,
                    "current_personnel_count": zone.current_personnel_count,
                    "hazard_level": zone.hazard_level,
                    "safety_level": zone.safety_level,
                    "access_level": zone.access_level,
                    "device_count": device_count,
                    "zone_manager_id": zone.zone_manager_id,
                    "contact_person": zone.contact_person,
                    "contact_phone": zone.contact_phone,
                    "zkteco_sync_enabled": zone.zkteco_sync_enabled,
                    "last_sync_at": zone.last_sync_at.isoformat() if zone.last_sync_at else None,
                    "floor_plan_url": zone.floor_plan_url,
                    "floor_plan_file_path": zone.floor_plan_file_path,
                    "floor_plan_filename": zone.floor_plan_filename,
                    "floor_plan_uploaded_at": zone.floor_plan_uploaded_at.isoformat() if zone.floor_plan_uploaded_at else None,
                    "created_at": zone.created_at.isoformat() if zone.created_at else None,
                    "updated_at": zone.updated_at.isoformat() if zone.updated_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting zones: {e}")
            return []
    
    async def get_zone_by_id(
        self,
        db: Session,
        zone_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get zone by ID with full details
        
        Args:
            db: Database session
            zone_id: Zone ID
            
        Returns:
            Zone details or None if not found
        """
        try:
            from ..models.zone import Zone, ZonePersonnelAssignment
            from ..models.device import Device
            from ..models.personnel import Personnel
            
            zone = db.query(Zone).filter(
                Zone.id == zone_id,
                Zone.is_active == True
            ).first()
            
            if not zone:
                return None
            
            # Get devices in this zone
            devices = db.query(Device).filter(Device.zone_id == zone_id).all()
            device_list = [{
                "id": device.id,
                "device_id": device.device_id,
                "name": device.name,
                "status": device.status.value if device.status else None,
                "ip_address": device.ip_address,
                "device_type": device.device_type.value if device.device_type else None
            } for device in devices]
            
            # Get personnel assigned to this zone
            personnel_assignments = db.query(ZonePersonnelAssignment).filter(
                ZonePersonnelAssignment.zone_id == zone_id,
                ZonePersonnelAssignment.status == "ACTIVE"
            ).all()
            
            personnel_list = []
            for assignment in personnel_assignments:
                personnel = db.query(Personnel).filter(Personnel.id == assignment.personnel_id).first()
                if personnel:
                    personnel_list.append({
                        "id": personnel.id,
                        "full_name": personnel.full_name,
                        "badge_id": personnel.badge_id,
                        "role": assignment.role,
                        "access_level": assignment.access_level,
                        "is_primary_zone": assignment.is_primary_zone,
                        "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None
                    })
            
            return {
                "id": zone.id,
                "name": zone.name,
                "code": zone.code,
                "zone_type": zone.zone_type,
                "description": zone.description,
                "status": zone.status,
                "state": zone.state,
                "address": zone.address,
                "latitude": zone.latitude,
                "longitude": zone.longitude,
                "max_capacity": zone.max_capacity,
                "hazard_level": zone.hazard_level,
                "safety_level": zone.safety_level,
                "access_level": zone.access_level,
                "device_count": len(devices),
                "devices": device_list,
                "zone_manager_id": zone.zone_manager_id,
                "contact_person": zone.contact_person,
                "contact_phone": zone.contact_phone,
                "zkteco_sync_enabled": zone.zkteco_sync_enabled,
                "last_sync_at": zone.last_sync_at.isoformat() if zone.last_sync_at else None,
                "floor_plan_url": zone.floor_plan_url,
                "floor_plan_file_path": zone.floor_plan_file_path,
                "floor_plan_filename": zone.floor_plan_filename,
                "floor_plan_uploaded_at": zone.floor_plan_uploaded_at.isoformat() if zone.floor_plan_uploaded_at else None,
                "personnel_count": len(personnel_list),
                "personnel": personnel_list,
                "created_at": zone.created_at.isoformat() if zone.created_at else None,
                "updated_at": zone.updated_at.isoformat() if zone.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting zone by ID: {e}")
            return None
    
    async def create_zone(
        self,
        db: Session,
        zone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new zone
        
        Args:
            db: Database session
            zone_data: Zone creation data
            
        Returns:
            Creation result with success status
        """
        try:
            from ..models.zone import Zone, ZoneType
            
            # Validate required fields
            if not zone_data.get("name"):
                return {
                    "success": False,
                    "error": "Zone name is required"
                }
            
            if not zone_data.get("zone_type"):
                return {
                    "success": False,
                    "error": "Zone type is required"
                }
            
            # Check if code already exists
            if zone_data.get("code"):
                existing = db.query(Zone).filter(Zone.code == zone_data["code"]).first()
                if existing:
                    return {
                        "success": False,
                        "error": f"Zone with code '{zone_data['code']}' already exists"
                    }
            
            # Generate code if not provided
            code = zone_data.get("code")
            if not code:
                state_abbr = zone_data.get("state", "UNK")[:3].upper()
                zone_name = zone_data["name"][:10].replace(" ", "_").upper()
                code = f"{state_abbr}-{zone_name}-{zone_data.get('zone_type', 'UNK')[:3].upper()}"
            
            # Create new zone - map frontend zone types to database enum values
            zone_type_mapping = {
                'WORK_AREA': 'RESTRICTED',
                'PRODUCTION_AREA': 'RESTRICTED', 
                'RESTRICTED': 'RESTRICTED',
                'PUBLIC': 'PUBLIC',
                'SAFE_HAVEN': 'SAFE_HAVEN',
                'ACCOMMODATION': 'PUBLIC',
                'HELIPAD': 'PUBLIC',
                'CONTROL_ROOM': 'RESTRICTED',
                'STORAGE': 'RESTRICTED',
                'EMERGENCY': 'SAFE_HAVEN'
            }
            
            db_zone_type = zone_type_mapping.get(zone_data.get("zone_type"), 'RESTRICTED')
            
            from datetime import datetime, timezone
            
            zone = Zone(
                name=zone_data["name"],
                code=code,
                zone_type=db_zone_type,
                description=zone_data.get("description"),
                state=zone_data.get("state"),
                address=zone_data.get("address"),
                latitude=float(zone_data.get("latitude")) if zone_data.get("latitude") and zone_data.get("latitude").strip() else None,
                longitude=float(zone_data.get("longitude")) if zone_data.get("longitude") and zone_data.get("longitude").strip() else None,
                max_capacity=int(zone_data.get("max_capacity")) if zone_data.get("max_capacity") and str(zone_data.get("max_capacity")).strip() else None,
                hazard_level=zone_data.get("hazard_level", "LOW"),
                safety_level=zone_data.get("safety_level", "NORMAL"),
                access_level=zone_data.get("access_level", "RESTRICTED"),
                zone_manager_id=zone_data.get("zone_manager_id"),
                contact_person=zone_data.get("contact_person"),
                contact_phone=zone_data.get("contact_phone"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.add(zone)
            db.commit()
            db.refresh(zone)
            
            return {
                "success": True,
                "data": {
                    "id": zone.id,
                    "name": zone.name,
                    "code": zone.code,
                    "zone_type": zone.zone_type,
                    "description": zone.description,
                    "status": zone.status,
                    "state": zone.state,
                    "created_at": zone.created_at.isoformat() if zone.created_at else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating zone: {e}")
            return {
                "success": False,
                "error": f"Failed to create zone: {str(e)}"
            }
    
    async def update_zone(
        self,
        db: Session,
        zone_id: int,
        zone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing zone
        
        Args:
            db: Database session
            zone_id: Zone ID
            zone_data: Zone update data
            
        Returns:
            Update result with success status
        """
        try:
            from ..models.zone import Zone, ZoneType
            
            # Check if zone exists
            zone = db.query(Zone).filter(Zone.id == zone_id).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Validate required fields
            if not zone_data.get("name"):
                return {
                    "success": False,
                    "error": "Zone name is required"
                }
            
            if not zone_data.get("zone_type"):
                return {
                    "success": False,
                    "error": "Zone type is required"
                }
            
            # Check if code already exists (excluding current zone)
            if zone_data.get("code") and zone_data["code"] != zone.code:
                existing = db.query(Zone).filter(Zone.code == zone_data["code"], Zone.id != zone_id).first()
                if existing:
                    return {
                        "success": False,
                        "error": f"Zone with code '{zone_data['code']}' already exists"
                    }
            
            # Update zone fields
            zone.name = zone_data["name"]
            zone.zone_type = zone_data["zone_type"]
            zone.description = zone_data.get("description")
            zone.state = zone_data.get("state")
            zone.address = zone_data.get("address")
            zone.latitude = float(zone_data.get("latitude")) if zone_data.get("latitude") and zone_data.get("latitude").strip() else None
            zone.longitude = float(zone_data.get("longitude")) if zone_data.get("longitude") and zone_data.get("longitude").strip() else None
            zone.max_capacity = int(zone_data.get("max_capacity")) if zone_data.get("max_capacity") and str(zone_data.get("max_capacity")).strip() else None
            zone.hazard_level = zone_data.get("hazard_level", "LOW")
            zone.safety_level = zone_data.get("safety_level", "NORMAL")
            zone.access_level = zone_data.get("access_level", "RESTRICTED")
            zone.zone_manager_id = zone_data.get("zone_manager_id")
            zone.contact_person = zone_data.get("contact_person")
            zone.contact_phone = zone_data.get("contact_phone")
            zone.updated_at = datetime.now(timezone.utc)
            
            # Update code if provided
            if zone_data.get("code") and zone_data["code"] != zone.code:
                zone.code = zone_data["code"]
            
            db.commit()
            db.refresh(zone)
            
            return {
                "success": True,
                "data": {
                    "id": zone.id,
                    "name": zone.name,
                    "code": zone.code,
                    "zone_type": zone.zone_type,
                    "description": zone.description,
                    "status": zone.status,
                    "state": zone.state,
                    "updated_at": zone.updated_at.isoformat() if zone.updated_at else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating zone: {e}")
            return {
                "success": False,
                "error": f"Failed to update zone: {str(e)}"
            }
    
    async def delete_zone(
        self,
        db: Session,
        zone_id: int
    ) -> Dict[str, Any]:
        """
        Delete a zone
        
        Args:
            db: Database session
            zone_id: Zone ID
            
        Returns:
            Deletion result
        """
        try:
            # Import Zone model
            from ..models.zone import Zone
            
            # Check if zone exists
            zone = db.query(Zone).filter(Zone.id == zone_id).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Delete the zone using soft delete (mark as inactive)
            zone_name = zone.name
            zone.is_active = False
            zone.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Successfully deleted zone {zone_id}: {zone_name}")
            
            return {
                "success": True,
                "message": f"Zone '{zone_name}' deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting zone: {e}")
            db.rollback()
            return {
                "success": False,
                "error": f"Failed to delete zone: {str(e)}"
            }
    
    async def assign_personnel_to_zone(
        self,
        db: Session,
        personnel_id: int,
        zone_id: int,
        assignment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assign personnel to a zone with access control
        
        Args:
            db: Database session
            personnel_id: Personnel ID
            zone_id: Zone ID
            assignment_data: Assignment details
            
        Returns:
            Assignment result
        """
        try:
            from ..models.zone import ZonePersonnelAssignment
            from ..models.personnel import Personnel
            from ..models.zone import Zone
            
            # Check if personnel exists
            personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
            if not personnel:
                return {
                    "success": False,
                    "error": f"Personnel with ID {personnel_id} not found"
                }
            
            # Check if zone exists
            zone = db.query(Zone).filter(Zone.id == zone_id).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Check if assignment already exists
            existing = db.query(ZonePersonnelAssignment).filter(
                ZonePersonnelAssignment.zone_id == zone_id,
                ZonePersonnelAssignment.personnel_id == personnel_id,
                ZonePersonnelAssignment.status == "ACTIVE"
            ).first()
            
            if existing:
                return {
                    "success": False,
                    "error": f"Personnel already assigned to zone {zone.name}"
                }
            
            # Create assignment
            assignment = ZonePersonnelAssignment(
                zone_id=zone_id,
                personnel_id=personnel_id,
                role=assignment_data.get("role"),
                access_level=assignment_data.get("access_level", "STANDARD"),
                is_primary_zone=assignment_data.get("is_primary_zone", False),
                is_permanent=assignment_data.get("is_permanent", False),
                access_times=assignment_data.get("access_times"),
                device_access=assignment_data.get("device_access"),
                approved_by=assignment_data.get("approved_by"),
                notes=assignment_data.get("notes")
            )
            
            db.add(assignment)
            
            # Update personnel current zone if this is primary assignment
            if assignment_data.get("is_primary_zone", False):
                personnel.current_zone_id = zone_id
            
            # Update zone personnel count
            zone.current_personnel_count = db.query(ZonePersonnelAssignment).filter(
                ZonePersonnelAssignment.zone_id == zone_id,
                ZonePersonnelAssignment.status == "ACTIVE"
            ).count()
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Personnel {personnel.full_name} assigned to zone {zone.name}",
                "data": {
                    "assignment_id": assignment.id,
                    "personnel_id": personnel_id,
                    "personnel_name": personnel.full_name,
                    "zone_id": zone_id,
                    "zone_name": zone.name,
                    "role": assignment.role,
                    "access_level": assignment.access_level
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error assigning personnel to zone: {e}")
            return {
                "success": False,
                "error": f"Failed to assign personnel to zone: {str(e)}"
            }
    
    async def get_zone_dashboard(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get zone dashboard data for overview
        
        Args:
            db: Database session
            
        Returns:
            Zone dashboard statistics
        """
        try:
            from ..models.zone import Zone, ZoneType
            from ..models.device import Device, DeviceStatus
            from ..models.personnel import Personnel
            
            # Total zones
            total_zones = db.query(Zone).filter(Zone.is_active == True).count()
            
            # Zones by state
            zones_by_state = db.query(
                Zone.state,
                func.count(Zone.id).label('count')
            ).filter(Zone.is_active == True).group_by(Zone.state).all()
            
            # Zones by type
            zones_by_type = db.query(
                Zone.zone_type,
                func.count(Zone.id).label('count')
            ).filter(Zone.is_active == True).group_by(Zone.zone_type).all()
            
            # Zone status distribution
            zones_by_status = db.query(
                Zone.status,
                func.count(Zone.id).label('count')
            ).filter(Zone.is_active == True).group_by(Zone.status).all()
            
            # Device statistics
            total_devices = db.query(Device).count()
            online_devices = db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()
            
            # Personnel in zones
            personnel_in_zones = db.query(Personnel).filter(Personnel.current_zone_id.isnot(None)).count()
            
            # Capacity utilization
            zones = db.query(Zone).filter(Zone.is_active == True).all()
            total_capacity = sum(z.max_capacity or 0 for z in zones)
            current_occupancy = sum(z.current_occupancy or 0 for z in zones)
            
            return {
                "total_zones": total_zones,
                "zones_by_state": {str(state): count for state, count in zones_by_state if state},
                "zones_by_type": {str(zone_type or "Unknown"): count for zone_type, count in zones_by_type},
                "zones_by_status": {str(status or "Unknown"): count for status, count in zones_by_status},
                "device_statistics": {
                    "total_devices": total_devices,
                    "online_devices": online_devices,
                    "offline_devices": total_devices - online_devices,
                    "online_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0
                },
                "personnel_statistics": {
                    "total_personnel_in_zones": personnel_in_zones,
                    "average_per_zone": (personnel_in_zones / total_zones) if total_zones > 0 else 0
                },
                "capacity_statistics": {
                    "total_capacity": total_capacity,
                    "current_occupancy": current_occupancy,
                    "utilization_percentage": (current_occupancy / total_capacity * 100) if total_capacity > 0 else 0,
                    "available_capacity": total_capacity - current_occupancy
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting zone dashboard: {e}")
            return {}
    
    async def get_zones_by_state(
        self,
        db: Session,
        state: str
    ) -> List[Dict[str, Any]]:
        """
        Get all zones in a specific state
        
        Args:
            db: Database session
            state: State name
            
        Returns:
            List of zones in the state
        """
        return await self.get_zones(db, state=state)
    
    async def update_zone_occupancy(
        self,
        db: Session,
        zone_id: int,
        occupancy_change: int
    ) -> Dict[str, Any]:
        """
        Update zone occupancy (for real-time tracking)
        
        Args:
            db: Database session
            zone_id: Zone ID
            occupancy_change: Change in occupancy (+1 for entry, -1 for exit)
            
        Returns:
            Update result
        """
        try:
            from ..models.zone import Zone
            
            zone = db.query(Zone).filter(Zone.id == zone_id).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Update occupancy
            new_occupancy = max(0, (zone.current_occupancy or 0) + occupancy_change)
            zone.current_occupancy = new_occupancy
            
            # Update personnel count if needed
            zone.current_personnel_count = db.query(func.count()).filter(
                # This would need to be implemented based on your tracking logic
            ).scalar() or new_occupancy
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Zone {zone.name} occupancy updated to {new_occupancy}",
                "data": {
                    "zone_id": zone_id,
                    "zone_name": zone.name,
                    "new_occupancy": new_occupancy,
                    "max_capacity": zone.max_capacity,
                    "occupancy_percentage": (new_occupancy / zone.max_capacity * 100) if zone.max_capacity else 0
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating zone occupancy: {e}")
            return {
                "success": False,
                "error": f"Failed to update zone occupancy: {str(e)}"
            }
    
    async def get_zone_personnel_tracking(
        self, 
        db: Session, 
        zone_id: int,
        include_attendance: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive personnel tracking for a zone including attendance
        
        Args:
            db: Database session
            zone_id: Zone ID
            include_attendance: Whether to include attendance data
            
        Returns:
            Personnel tracking data with attendance information
        """
        try:
            # Import here to avoid circular imports
            from ..models.zone import Zone, ZonePersonnelAssignment
            from ..models.personnel import Personnel
            from ..models.events import Event, EventTypeEnum
            
            # Get zone information
            zone = db.query(Zone).filter(Zone.id == zone_id).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Get personnel assignments for this zone
            personnel_assignments = db.query(ZonePersonnelAssignment).filter(
                ZonePersonnelAssignment.zone_id == zone_id,
                ZonePersonnelAssignment.status == "ACTIVE"
            ).all()
            
            # Get personnel details
            personnel_ids = [pa.personnel_id for pa in personnel_assignments]
            personnel_list = db.query(Personnel).filter(
                Personnel.id.in_(personnel_ids),
                Personnel.is_active == True
            ).all()
            
            # Get current attendance status for each personnel
            attendance_data = {}
            if include_attendance:
                # Get latest check-in/check-out events for each personnel
                for person in personnel_list:
                    latest_event = db.query(Event).filter(
                        Event.personnel_id == person.id,
                        Event.event_type.in_([EventTypeEnum.CHECKIN, EventTypeEnum.CHECKOUT])
                    ).order_by(Event.timestamp.desc()).first()
                    
                    attendance_data[person.id] = {
                        "current_status": "CHECKED_IN" if latest_event and latest_event.event_type == EventTypeEnum.CHECKIN else "CHECKED_OUT",
                        "last_event": latest_event.event_type.value if latest_event else None,
                        "last_event_time": latest_event.timestamp.isoformat() if latest_event else None,
                        "location": person.current_zone_id
                    }
            
            # Build personnel tracking data
            tracked_personnel = []
            for person in personnel_list:
                assignment = next((pa for pa in personnel_assignments if pa.personnel_id == person.id), None)
                
                person_data = {
                    "id": person.id,
                    "badge_id": person.badge_id,
                    "full_name": person.full_name,
                    "company": person.company,
                    "position": person.position,
                    "department": person.department,
                    "phone": person.phone,
                    "email": person.email,
                    "current_zone_id": person.current_zone_id,
                    "assignment_details": {
                        "role": assignment.role if assignment else None,
                        "access_level": assignment.access_level if assignment else "STANDARD",
                        "is_primary_zone": assignment.is_primary_zone if assignment else False,
                        "assigned_at": assignment.assigned_at.isoformat() if assignment else None
                    },
                    "attendance": attendance_data.get(person.id, {}),
                    "location_status": "IN_ZONE" if person.current_zone_id == zone_id else "OUTSIDE_ZONE"
                }
                tracked_personnel.append(person_data)
            
            # Calculate zone statistics
            total_assigned = len(tracked_personnel)
            currently_in_zone = len([p for p in tracked_personnel if p["location_status"] == "IN_ZONE"])
            checked_in_count = len([p for p in tracked_personnel if p["attendance"].get("current_status") == "CHECKED_IN"])
            
            return {
                "success": True,
                "data": {
                    "zone_info": {
                        "id": zone.id,
                        "name": zone.name,
                        "code": zone.code,
                        "zone_type": zone.zone_type.value,
                        "status": zone.status.value,
                        "max_capacity": zone.max_capacity,
                        "current_occupancy": zone.current_occupancy,
                        "latitude": zone.latitude,
                        "longitude": zone.longitude,
                        "floor_plan_url": zone.floor_plan_url,
                        "map_type": zone.map_type
                    },
                    "personnel_tracking": {
                        "total_assigned": total_assigned,
                        "currently_in_zone": currently_in_zone,
                        "checked_in": checked_in_count,
                        "attendance_rate": (checked_in_count / total_assigned * 100) if total_assigned > 0 else 0,
                        "occupancy_rate": (currently_in_zone / zone.max_capacity * 100) if zone.max_capacity else 0,
                        "personnel": tracked_personnel
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting zone personnel tracking: {e}")
            return {
                "success": False,
                "error": f"Failed to get zone personnel tracking: {str(e)}"
            }
    
    async def update_zone_floor_plan(
        self,
        db: Session,
        zone_id: int,
        floor_plan_url: str,
        floor_plan_coordinates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update zone floor plan information
        
        Args:
            db: Database session
            zone_id: Zone ID
            floor_plan_url: URL to floor plan image
            floor_plan_coordinates: Floor plan coordinate mapping
            
        Returns:
            Updated zone information
        """
        try:
            # Import here to avoid circular imports
            from ..models.zone import Zone
            
            zone = db.query(Zone).filter(Zone.id == zone_id).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Update floor plan information
            zone.floor_plan_url = floor_plan_url
            zone.map_type = "floor_plan"
            if floor_plan_coordinates:
                zone.floor_plan_coordinates = floor_plan_coordinates
            
            zone.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                "success": True,
                "message": f"Zone {zone.name} floor plan updated successfully",
                "data": {
                    "zone_id": zone.id,
                    "zone_name": zone.name,
                    "floor_plan_url": zone.floor_plan_url,
                    "map_type": zone.map_type,
                    "updated_at": zone.updated_at.isoformat()
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating zone floor plan: {e}")
            return {
                "success": False,
                "error": f"Failed to update zone floor plan: {str(e)}"
            }
    
    async def get_zone_analytics(
        self,
        db: Session,
        zone_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive zone analytics and statistics
        
        Args:
            db: Database session
            zone_id: Zone ID (optional, if None returns all zones analytics)
            
        Returns:
            Zone analytics data
        """
        try:
            # Import here to avoid circular imports
            from ..models.zone import Zone, ZonePersonnelAssignment
            from ..models.personnel import Personnel
            from ..models.events import Event, EventTypeEnum
            
            if zone_id:
                # Get specific zone analytics
                zones = db.query(Zone).filter(Zone.id == zone_id).all()
            else:
                # Get all zones analytics
                zones = db.query(Zone).filter(Zone.is_active == True).all()
            
            analytics_data = []
            
            for zone in zones:
                # Get personnel assignments
                personnel_assignments = db.query(ZonePersonnelAssignment).filter(
                    ZonePersonnelAssignment.zone_id == zone.id,
                    ZonePersonnelAssignment.status == "ACTIVE"
                ).all()
                
                # Get personnel currently in zone
                personnel_in_zone = db.query(Personnel).filter(
                    Personnel.current_zone_id == zone.id,
                    Personnel.is_active == True
                ).all()
                
                # Get attendance events for last 24 hours
                from datetime import datetime, timedelta
                twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
                
                attendance_events = db.query(Event).filter(
                    Event.personnel_id.in_([pa.personnel_id for pa in personnel_assignments]),
                    Event.event_type.in_([EventTypeEnum.CHECKIN, EventTypeEnum.CHECKOUT]),
                    Event.timestamp >= twenty_four_hours_ago
                ).all()
                
                # Calculate statistics
                checkins = len([e for e in attendance_events if e.event_type == EventTypeEnum.CHECKIN])
                checkouts = len([e for e in attendance_events if e.event_type == EventTypeEnum.CHECKOUT])
                
                zone_analytics = {
                    "zone_info": {
                        "id": zone.id,
                        "name": zone.name,
                        "code": zone.code,
                        "zone_type": zone.zone_type.value,
                        "status": zone.status.value,
                        "state": zone.state
                    },
                    "personnel_stats": {
                        "total_assigned": len(personnel_assignments),
                        "currently_present": len(personnel_in_zone),
                        "max_capacity": zone.max_capacity,
                        "occupancy_rate": (len(personnel_in_zone) / zone.max_capacity * 100) if zone.max_capacity else 0
                    },
                    "attendance_stats": {
                        "checkins_24h": checkins,
                        "checkouts_24h": checkouts,
                        "net_change_24h": checkins - checkouts
                    },
                    "location_info": {
                        "latitude": zone.latitude,
                        "longitude": zone.longitude,
                        "has_gps": bool(zone.latitude and zone.longitude),
                        "has_floor_plan": bool(zone.floor_plan_url),
                        "map_type": zone.map_type
                    }
                }
                
                analytics_data.append(zone_analytics)
            
            return {
                "success": True,
                "data": analytics_data if zone_id else {"zones": analytics_data, "total_zones": len(analytics_data)},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting zone analytics: {e}")
            return {
                "success": False,
                "error": f"Failed to get zone analytics: {str(e)}"
            }
    
    async def update_zone_coordinates(
        self,
        db: Session,
        zone_id: int,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        gps_coordinates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update zone GPS coordinates
        
        Args:
            db: Database session
            zone_id: Zone ID
            latitude: GPS latitude
            longitude: GPS longitude
            gps_coordinates: Additional GPS coordinate data
            
        Returns:
            Updated zone information
        """
        try:
            # Import here to avoid circular imports
            from ..models.zone import Zone
            
            zone = db.query(Zone).filter(Zone.id == zone_id).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Update GPS coordinates
            if latitude:
                zone.latitude = latitude
            if longitude:
                zone.longitude = longitude
            
            zone.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                "success": True,
                "message": f"Zone {zone.name} coordinates updated successfully",
                "data": {
                    "zone_id": zone.id,
                    "zone_name": zone.name,
                    "latitude": zone.latitude,
                    "longitude": zone.longitude,
                    "updated_at": zone.updated_at.isoformat()
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating zone coordinates: {e}")
            return {
                "success": False,
                "error": f"Failed to update zone coordinates: {str(e)}"
            }

    async def get_personnel_monitoring(
        self,
        db: Session,
        zone_id: Optional[int] = None,
        include_attendance: bool = True
    ) -> Dict[str, Any]:
        """
        Get personnel monitoring data for zones with advanced attendance features
        
        Args:
            db: Database session
            zone_id: Specific zone ID (None for all zones)
            include_attendance: Whether to include attendance data
            
        Returns:
            Personnel monitoring data with attendance analytics
        """
        try:
            # Import here to avoid circular imports
            from ..models.zone import Zone, ZonePersonnelAssignment
            from ..models.personnel import Personnel
            from ..models.events import Event, EventTypeEnum
            from ..models.device import Device
            from datetime import datetime, timedelta
            
            # Get zones to query
            if zone_id:
                zones = db.query(Zone).filter(Zone.id == zone_id, Zone.is_active == True).all()
            else:
                zones = db.query(Zone).filter(Zone.is_active == True).all()
            
            personnel_data = []
            now = datetime.now(timezone.utc)
            twenty_four_hours_ago = now - timedelta(hours=24)
            
            for zone in zones:
                # Get personnel assignments for this zone
                personnel_assignments = db.query(ZonePersonnelAssignment).filter(
                    ZonePersonnelAssignment.zone_id == zone.id,
                    ZonePersonnelAssignment.status == "ACTIVE"
                ).all()
                
                for assignment in personnel_assignments:
                    # Get personnel details
                    personnel = db.query(Personnel).filter(
                        Personnel.id == assignment.personnel_id,
                        Personnel.is_active == True
                    ).first()
                    
                    if not personnel:
                        continue
                    
                    # Get attendance data if requested
                    attendance_data = {}
                    if include_attendance:
                        # Get latest check-in/check-out events
                        latest_checkin = db.query(Event).filter(
                            Event.personnel_id == personnel.id,
                            Event.event_type == EventTypeEnum.CHECKIN,
                            Event.timestamp >= twenty_four_hours_ago
                        ).order_by(Event.timestamp.desc()).first()
                        
                        latest_checkout = db.query(Event).filter(
                            Event.personnel_id == personnel.id,
                            Event.event_type == EventTypeEnum.CHECKOUT,
                            Event.timestamp >= twenty_four_hours_ago
                        ).order_by(Event.timestamp.desc()).first()
                        
                        # Get scan count for today
                        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        scan_count_today = db.query(Event).filter(
                            Event.personnel_id == personnel.id,
                            Event.timestamp >= today_start
                        ).count()
                        
                        # Get total scan count
                        total_scan_count = db.query(Event).filter(
                            Event.personnel_id == personnel.id
                        ).count()
                        
                        # Get latest event for location
                        latest_event = db.query(Event).filter(
                            Event.personnel_id == personnel.id
                        ).order_by(Event.timestamp.desc()).first()
                        
                        # Calculate attendance metrics
                        check_in_time = latest_checkin.timestamp.isoformat() if latest_checkin else None
                        check_out_time = latest_checkout.timestamp.isoformat() if latest_checkout else None
                        
                        # Determine current status
                        if latest_checkin and (not latest_checkout or latest_checkin.timestamp > latest_checkout.timestamp):
                            attendance_status = "present"
                            total_hours_today = ((now - latest_checkin.timestamp).total_seconds() / 3600) if latest_checkin else 0
                        else:
                            attendance_status = "absent" if not check_in_time else "early_departure"
                            total_hours_today = 0
                        
                        attendance_data = {
                            "check_in_time": check_in_time,
                            "check_out_time": check_out_time,
                            "total_hours_today": round(total_hours_today, 2),
                            "break_duration": 0.5,  # Default - could be calculated from break events
                            "overtime_hours": max(0, total_hours_today - 8) if total_hours_today > 8 else 0,
                            "attendance_status": attendance_status,
                            "late_arrival": latest_checkin and latest_checkin.timestamp.hour > 8,  # Assuming 8 AM start
                            "early_departure": latest_checkout and latest_checkout.timestamp.hour < 17,  # Assuming 5 PM end
                            "productivity_score": 85,  # Could be calculated based on various factors
                            "attendance_percentage": 95.5  # Could be calculated from historical data
                        }
                    
                    # Get location history
                    location_history = []
                    recent_events = db.query(Event).filter(
                        Event.personnel_id == personnel.id,
                        Event.timestamp >= twenty_four_hours_ago
                    ).order_by(Event.timestamp.desc()).limit(10).all()
                    
                    for event in recent_events:
                        location_history.append({
                            "timestamp": event.timestamp.isoformat(),
                            "location": zone.name,
                            "event_type": event.event_type.value.lower(),
                            "reader_id": event.device_id if hasattr(event, 'device_id') else None
                        })
                    
                    # Get alerts (safety violations, attendance issues, etc.)
                    alerts = []
                    
                    # Check for late arrival
                    if include_attendance and attendance_data.get("late_arrival"):
                        alerts.append({
                            "type": "attendance",
                            "message": "Late arrival detected",
                            "timestamp": attendance_data.get("check_in_time"),
                            "severity": "low"
                        })
                    
                    # Check for extended time in high-risk areas
                    if zone.hazard_level in ["HIGH", "CRITICAL"] and attendance_data.get("total_hours_today", 0) > 6:
                        alerts.append({
                            "type": "safety",
                            "message": "Extended time in high-risk area",
                            "timestamp": now.isoformat(),
                            "severity": "medium"
                        })
                    
                    # Build personnel monitoring data
                    person_data = {
                        "id": personnel.id,
                        "full_name": personnel.full_name,
                        "badge_id": personnel.badge_id,
                        "email": personnel.email,
                        "phone": personnel.phone,
                        "department": personnel.department,
                        "role": personnel.position,
                        "photo_url": f"/api/v1/personnel/{personnel.id}/photo",
                        "status": "active" if personnel.is_active else "inactive",
                        "zone_id": zone.id,
                        "zone_name": zone.name,
                        "zone_type": zone.zone_type.value if zone.zone_type else "UNKNOWN",
                        "last_scan_time": latest_event.timestamp.isoformat() if latest_event else None,
                        "last_scan_location": zone.name,
                        "reader_name": f"{zone.name} Reader",
                        "scan_count_today": scan_count_today,
                        "total_scan_count": total_scan_count,
                        "attendance": attendance_data,
                        "location_history": location_history,
                        "alerts": alerts
                    }
                    
                    personnel_data.append(person_data)
            
            # Calculate zone-wise attendance statistics
            zone_attendance_stats = {}
            for personnel in personnel_data:
                personnel_zone_id = personnel["zone_id"]
                if personnel_zone_id not in zone_attendance_stats:
                    zone_attendance_stats[personnel_zone_id] = {
                        "zone_name": personnel["zone_name"],
                        "total_personnel": 0,
                        "present_count": 0,
                        "absent_count": 0,
                        "late_count": 0,
                        "early_departure_count": 0,
                        "average_productivity": 0,
                        "total_hours_today": 0,
                        "attendance_percentage": 0
                    }
                
                stats = zone_attendance_stats[personnel_zone_id]
                stats["total_personnel"] += 1
                
                if personnel.get("attendance"):
                    attendance = personnel["attendance"]
                    if attendance["attendance_status"] == "present":
                        stats["present_count"] += 1
                    elif attendance["attendance_status"] == "absent":
                        stats["absent_count"] += 1
                        
                    if attendance["late_arrival"]:
                        stats["late_count"] += 1
                        
                    if attendance["early_departure"]:
                        stats["early_departure_count"] += 1
                        
                    stats["average_productivity"] += attendance["productivity_score"]
                    stats["total_hours_today"] += attendance["total_hours_today"]
            
            # Calculate averages
            for stats in zone_attendance_stats.values():
                if stats["total_personnel"] > 0:
                    stats["average_productivity"] = stats["average_productivity"] / stats["total_personnel"]
                    stats["attendance_percentage"] = (stats["present_count"] / stats["total_personnel"]) * 100
            
            return {
                "success": True,
                "data": personnel_data,
                "total_count": len(personnel_data),
                "zone_id": zone_id,
                "include_attendance": include_attendance,
                "zone_attendance_stats": zone_attendance_stats,
                "summary_statistics": {
                    "total_personnel": len(personnel_data),
                    "present_today": len([p for p in personnel_data if p.get("attendance", {}).get("attendance_status") == "present"]),
                    "absent_today": len([p for p in personnel_data if p.get("attendance", {}).get("attendance_status") == "absent"]),
                    "late_arrivals": len([p for p in personnel_data if p.get("attendance", {}).get("late_arrival")]),
                    "early_departures": len([p for p in personnel_data if p.get("attendance", {}).get("early_departure")])
                },
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting personnel monitoring: {e}")
            return {
                "success": False,
                "error": f"Failed to get personnel monitoring: {str(e)}"
            }

    async def assign_reader_to_zone(self, db: Session, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign a reader to a zone
        
        Args:
            db: Database session
            assignment_data: Reader assignment data
            
        Returns:
            Assignment result
        """
        try:
            from ..models.zone import Zone
            from ..models.device import Device, DeviceStatus
            from ..models.zone_reader_assignment import ZoneReaderAssignment
            
            zone_id = assignment_data.get("zone_id")
            reader_id = assignment_data.get("reader_id")
            mode = assignment_data.get("mode", "entry_exit")
            
            if not zone_id or not reader_id:
                return {
                    "success": False,
                    "error": "Zone ID and Reader ID are required"
                }
            
            # Check if zone exists
            zone = db.query(Zone).filter(Zone.id == zone_id, Zone.is_active == True).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {zone_id} not found"
                }
            
            # Check if reader exists and is available
            reader = db.query(Device).filter(Device.id == reader_id).first()
            if not reader:
                return {
                    "success": False,
                    "error": f"Reader with ID {reader_id} not found"
                }
            
            # Check if reader is already assigned to this zone
            existing_assignment = db.query(ZoneReaderAssignment).filter(
                ZoneReaderAssignment.zone_id == zone_id,
                ZoneReaderAssignment.reader_id == reader_id,
                ZoneReaderAssignment.status == "active"
            ).first()
            
            if existing_assignment:
                return {
                    "success": False,
                    "error": f"Reader {reader_id} is already assigned to zone {zone_id}"
                }
            
            # Create reader assignment record
            assignment = ZoneReaderAssignment(
                zone_id=zone_id,
                reader_id=reader_id,
                mode=mode,
                assigned_at=datetime.now(timezone.utc),
                status="active",
                notes=assignment_data.get("notes", "")
            )
            
            db.add(assignment)
            
            # Update reader status to indicate it's assigned
            reader.zone_id = zone_id
            reader.status = DeviceStatus.ONLINE  # Assuming assignment means it should be online
            
            db.commit()
            db.refresh(assignment)
            
            return {
                "success": True,
                "message": f"Reader {reader_id} assigned to zone {zone_id} successfully",
                "data": {
                    "assignment_id": assignment.id,
                    "zone_id": zone_id,
                    "reader_id": reader_id,
                    "mode": mode,
                    "assigned_at": assignment.assigned_at.isoformat(),
                    "status": "active"
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error assigning reader to zone: {e}")
            return {
                "success": False,
                "error": f"Failed to assign reader to zone: {str(e)}"
            }

    # Zone Reader Assignment Management
    async def get_zone_reader_assignments(
        self,
        db: Session,
        zone_id: Optional[int] = None,
        reader_id: Optional[int] = None,
        assignment_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get zone reader assignments with filtering options
        
        Args:
            db: Database session
            zone_id: Filter by zone ID
            reader_id: Filter by reader ID
            assignment_status: Filter by assignment status
            
        Returns:
            Zone reader assignments data
        """
        try:
            from sqlalchemy import text
            
            # Use raw SQL to avoid model issues
            base_query = """
                SELECT zra.id, zra.zone_id, zra.reader_id, zra.assignment_type, 
                       zra.status, zra.is_primary, zra.assigned_at, zra.unassigned_at,
                       zra.expires_at, zra.access_level, zra.notes, zra.assigned_by,
                       z.name as zone_name, z.code as zone_code,
                       d.device_id, d.name as reader_name, d.status as reader_status,
                       d.ip_address, d.location
                FROM zone_reader_assignments zra
                LEFT JOIN zones z ON zra.zone_id = z.id
                LEFT JOIN devices d ON zra.reader_id = d.id
                WHERE 1=1
            """
            
            params = {}
            
            if zone_id:
                base_query += " AND zra.zone_id = :zone_id"
                params["zone_id"] = zone_id
            
            if reader_id:
                base_query += " AND zra.reader_id = :reader_id"
                params["reader_id"] = reader_id
            
            if assignment_status:
                base_query += " AND zra.status = :assignment_status"
                params["assignment_status"] = assignment_status
            
            result = db.execute(text(base_query), params)
            assignments = []
            for row in result.fetchall():
                row_dict = {}
                for i, column in enumerate(row._fields):
                    value = row[i]
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    row_dict[column] = value
                assignments.append(row_dict)
            
            return {
                "success": True,
                "assignments": assignments,
                "total_count": len(assignments)
            }
            
        except Exception as e:
            logger.error(f"Error getting zone reader assignments: {e}")
            return {
                "success": False,
                "error": f"Failed to get zone reader assignments: {str(e)}"
            }
    
    async def create_zone_reader_assignment(
        self,
        db: Session,
        assignment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new zone reader assignment
        
        Args:
            db: Database session
            assignment_data: Assignment creation data
            
        Returns:
            Creation result
        """
        try:
            from ..models.zone_reader_assignment import ZoneReaderAssignment
            from ..models.zone import Zone
            from ..models.device import Device
            from ..models.device import DeviceStatus
            
            # Validate required fields
            if not assignment_data.get("reader_id") or not assignment_data.get("zone_id"):
                return {
                    "success": False,
                    "error": "Reader ID and Zone ID are required"
                }
            
            # Check if zone exists
            zone = db.query(Zone).filter(Zone.id == assignment_data["zone_id"]).first()
            if not zone:
                return {
                    "success": False,
                    "error": f"Zone with ID {assignment_data['zone_id']} not found"
                }
            
            # Check if reader exists
            reader = db.query(Device).filter(Device.id == assignment_data["reader_id"]).first()
            if not reader:
                return {
                    "success": False,
                    "error": f"Reader with ID {assignment_data['reader_id']} not found"
                }
            
            # Check if assignment already exists
            existing_assignment = db.query(ZoneReaderAssignment).filter(
                ZoneReaderAssignment.reader_id == assignment_data["reader_id"],
                ZoneReaderAssignment.zone_id == assignment_data["zone_id"],
                ZoneReaderAssignment.status == "active"
            ).first()
            
            if existing_assignment:
                return {
                    "success": False,
                    "error": f"Reader is already assigned to this zone"
                }
            
            # Create new assignment
            new_assignment = ZoneReaderAssignment(
                reader_id=assignment_data["reader_id"],
                zone_id=assignment_data["zone_id"],
                mode=assignment_data.get("mode", "entry_exit"),
                assigned_at=datetime.now(timezone.utc),
                status="active",
                notes=assignment_data.get("notes", "")
            )
            
            db.add(new_assignment)
            
            # Update reader zone assignment
            reader.zone_id = assignment_data["zone_id"]
            reader.status = DeviceStatus.ONLINE  # Set to online when assigned
            
            db.commit()
            db.refresh(new_assignment)
            
            logger.info(f"Created zone reader assignment: {new_assignment.id}")
            
            return {
                "success": True,
                "data": {
                    "id": new_assignment.id,
                    "reader_id": new_assignment.reader_id,
                    "zone_id": new_assignment.zone_id,
                    "mode": new_assignment.mode,
                    "assignment_date": new_assignment.assigned_at.isoformat(),
                    "status": new_assignment.status,
                    "notes": new_assignment.notes
                },
                "message": "Zone reader assignment created successfully"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating zone reader assignment: {e}")
            return {
                "success": False,
                "error": f"Failed to create zone reader assignment: {str(e)}"
            }
    
    async def update_zone_reader_assignment(
        self,
        db: Session,
        assignment_id: int,
        assignment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing zone reader assignment
        
        Args:
            db: Database session
            assignment_id: Assignment ID
            assignment_data: Assignment update data
            
        Returns:
            Update result
        """
        try:
            from ..models.zone_reader_assignment import ZoneReaderAssignment
            from ..models.zone import Zone
            from ..models.device import Device
            
            # Get existing assignment
            assignment = db.query(ZoneReaderAssignment).filter(ZoneReaderAssignment.id == assignment_id).first()
            if not assignment:
                return {
                    "success": False,
                    "error": f"Assignment with ID {assignment_id} not found"
                }
            
            # Update fields if provided
            if "mode" in assignment_data:
                assignment.mode = assignment_data["mode"]
            
            if "status" in assignment_data:
                assignment.status = assignment_data["status"]
            
            if "notes" in assignment_data:
                assignment.notes = assignment_data["notes"]
            
            # If reassigning to a different zone
            if "zone_id" in assignment_data and assignment_data["zone_id"] != assignment.zone_id:
                # Check if new zone exists
                new_zone = db.query(Zone).filter(Zone.id == assignment_data["zone_id"]).first()
                if not new_zone:
                    return {
                        "success": False,
                        "error": f"Zone with ID {assignment_data['zone_id']} not found"
                    }
                
                # Update reader zone assignment
                reader = db.query(Device).filter(Device.id == assignment.reader_id).first()
                if reader:
                    reader.zone_id = assignment_data["zone_id"]
                
                assignment.zone_id = assignment_data["zone_id"]
            
            assignment.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(assignment)
            
            logger.info(f"Updated zone reader assignment {assignment_id}: {assignment_data}")
            
            return {
                "success": True,
                "data": {
                    "id": assignment.id,
                    "reader_id": assignment.reader_id,
                    "zone_id": assignment.zone_id,
                    "mode": assignment.mode,
                    "status": assignment.status,
                    "notes": assignment.notes,
                    "assignment_date": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                    "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None
                },
                "message": "Zone reader assignment updated successfully"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating zone reader assignment: {e}")
            return {
                "success": False,
                "error": f"Failed to update zone reader assignment: {str(e)}"
            }
    
    async def get_zone_reader_assignment_statistics(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get zone reader assignment statistics
        
        Args:
            db: Database session
            
        Returns:
            Reader assignment statistics
        """
        try:
            from ..models.zone_reader_assignment import ZoneReaderAssignment
            from ..models.device import Device, DeviceStatus
            from ..models.zone import Zone
            from sqlalchemy import func
            
            # Get total readers
            total_readers = db.query(Device).count()
            
            # Get assigned readers (those with active assignments)
            assigned_readers = db.query(ZoneReaderAssignment).filter(
                ZoneReaderAssignment.status == "active"
            ).distinct(ZoneReaderAssignment.reader_id).count()
            
            unassigned_readers = total_readers - assigned_readers
            
            # Get active zones
            active_zones = db.query(Zone).filter(Zone.is_active == True).count()
            
            # Get reader model distribution
            reader_models = db.query(
                Device.model,
                func.count(Device.id).label('count')
            ).group_by(Device.model).all()

            reader_model_dict = {str(model or "Unknown"): count for model, count in reader_models}
            
            # Get reader status distribution
            reader_status = db.query(
                Device.status,
                func.count(Device.id).label('count')
            ).group_by(Device.status).all()
            
            reader_status_dict = {str(status.value): count for status, count in reader_status}
            
            return {
                "success": True,
                "data": {
                    "total_readers": total_readers,
                    "assigned_readers": assigned_readers,
                    "unassigned_readers": unassigned_readers,
                    "total_zones": active_zones,
                    "reader_models": reader_model_dict,
                    "reader_status": reader_status_dict
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting reader assignment statistics: {e}")
            return {
                "success": False,
                "error": f"Failed to get reader assignment statistics: {str(e)}"
            }
    
    async def get_available_readers_for_assignment(
        self,
        db: Session,
        zone_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get available readers for zone assignment
        
        Args:
            db: Database session
            zone_id: Filter by zone (exclude readers already assigned to this zone)
            
        Returns:
            Available readers list
        """
        try:
            from sqlalchemy import text
            
            # Use raw SQL to avoid model issues with missing columns
            base_query = """
                SELECT id, device_id, name, device_type, status, ip_address, location 
                FROM devices 
                WHERE status != 'MAINTENANCE'
            """
            
            params = {}
            
            if zone_id:
                # Exclude readers already assigned to this zone
                base_query += " AND id NOT IN (SELECT reader_id FROM zone_reader_assignments WHERE zone_id = :zone_id)"
                params["zone_id"] = zone_id
            
            result = db.execute(text(base_query), params)
            readers = []
            for row in result.fetchall():
                readers.append({
                    "id": row[0],
                    "device_id": row[1], 
                    "name": row[2],
                    "device_type": row[3],
                    "status": row[4],
                    "ip_address": row[5],
                    "location": row[6]
                })
            
            return {
                "success": True,
                "data": readers,
                "total_count": len(readers)
            }
            
        except Exception as e:
            logger.error(f"Error getting available readers: {e}")
            return {
                "success": False,
                "error": f"Failed to get available readers: {str(e)}"
            }
    
    async def bulk_create_zone_reader_assignments(
        self,
        db: Session,
        assignments_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple zone reader assignments in bulk
        
        Args:
            db: Database session
            assignments_data: List of assignment creation data
            
        Returns:
            Bulk creation result
        """
    async def bulk_create_zone_reader_assignments(
        self,
        db: Session,
        assignments_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple zone reader assignments in bulk
        
        Args:
            db: Database session
            assignments_data: List of assignment creation data
            
        Returns:
            Bulk creation result
        """
        try:
            from ..models.zone_reader_assignment import ZoneReaderAssignment
            from ..models.zone import Zone
            from ..models.device import Device, DeviceStatus
            
            created_assignments = []
            errors = []
            
            for assignment_data in assignments_data:
                try:
                    # Validate required fields
                    if not assignment_data.get("reader_id") or not assignment_data.get("zone_id"):
                        errors.append(f"Missing reader_id or zone_id in assignment data")
                        continue
                    
                    # Check if zone exists
                    zone = db.query(Zone).filter(Zone.id == assignment_data["zone_id"]).first()
                    if not zone:
                        errors.append(f"Zone {assignment_data['zone_id']} not found")
                        continue
                    
                    # Check if reader exists
                    reader = db.query(Device).filter(Device.id == assignment_data["reader_id"]).first()
                    if not reader:
                        errors.append(f"Reader {assignment_data['reader_id']} not found")
                        continue
                    
                    # Check if assignment already exists
                    existing_assignment = db.query(ZoneReaderAssignment).filter(
                        ZoneReaderAssignment.reader_id == assignment_data["reader_id"],
                        ZoneReaderAssignment.zone_id == assignment_data["zone_id"],
                        ZoneReaderAssignment.status == "active"
                    ).first()
                    
                    if existing_assignment:
                        errors.append(f"Reader {assignment_data['reader_id']} already assigned to zone {assignment_data['zone_id']}")
                        continue
                    
                    # Create new assignment
                    new_assignment = ZoneReaderAssignment(
                        reader_id=assignment_data["reader_id"],
                        zone_id=assignment_data["zone_id"],
                        mode=assignment_data.get("mode", "entry_exit"),
                        assigned_at=datetime.now(timezone.utc),
                        status="active",
                        notes=assignment_data.get("notes", "")
                    )
                    
                    db.add(new_assignment)
                    
                    # Update reader zone assignment
                    reader.zone_id = assignment_data["zone_id"]
                    reader.status = DeviceStatus.ONLINE
                    
                    created_assignments.append({
                        "id": new_assignment.id,  # Will be set after commit
                        "reader_id": new_assignment.reader_id,
                        "zone_id": new_assignment.zone_id,
                        "mode": new_assignment.mode,
                        "assignment_date": new_assignment.assigned_at.isoformat(),
                        "status": new_assignment.status,
                        "notes": new_assignment.notes
                    })
                    
                except Exception as e:
                    errors.append(f"Error creating assignment for reader {assignment_data.get('reader_id', 'unknown')}: {str(e)}")
            
            # Commit all changes
            if created_assignments:
                db.commit()
                
                # Refresh assignments to get their IDs
                for i, assignment_data in enumerate(assignments_data):
                    if i < len(created_assignments):
                        assignment = db.query(ZoneReaderAssignment).filter(
                            ZoneReaderAssignment.reader_id == assignment_data["reader_id"],
                            ZoneReaderAssignment.zone_id == assignment_data["zone_id"]
                        ).first()
                        if assignment:
                            created_assignments[i]["id"] = assignment.id
            
            logger.info(f"Created {len(created_assignments)} zone reader assignments")
            
            return {
                "success": len(errors) == 0,
                "data": created_assignments,
                "message": f"Successfully created {len(created_assignments)} zone reader assignments",
                "errors": errors if errors else None
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating bulk zone reader assignments: {e}")
            return {
                "success": False,
                "error": f"Failed to create bulk zone reader assignments: {str(e)}"
            }

    async def get_zone_reader_status(self, db: Session, zone_id: int) -> Dict[str, Any]:
        """
        Get reader status for a specific zone
        
        Args:
            db: Database session
            zone_id: Zone ID
            
        Returns:
            Reader status data
        """
        try:
            from ..models.zone_reader_assignment import ZoneReaderAssignment
            from ..models.device import Device, DeviceStatus
            from ..models.events import Event
            from sqlalchemy import func
            
            # Get all reader assignments for this zone
            assignments = db.query(ZoneReaderAssignment).filter(
                ZoneReaderAssignment.zone_id == zone_id,
                ZoneReaderAssignment.status == "active"
            ).all()
            
            reader_status_data = []
            
            for assignment in assignments:
                # Get reader details
                reader = db.query(Device).filter(Device.id == assignment.reader_id).first()
                if not reader:
                    continue
                
                # Get scan count for this reader in the last 24 hours
                from datetime import timedelta
                twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
                
                scan_count = db.query(Event).filter(
                    Event.device_id == reader.id,
                    Event.timestamp >= twenty_four_hours_ago
                ).count()
                
                # Get last scan time
                last_scan = db.query(Event).filter(
                    Event.device_id == reader.id
                ).order_by(Event.timestamp.desc()).first()
                
                reader_data = {
                    "id": reader.id,
                    "name": reader.name or f"Reader {reader.id}",
                    "ip_address": reader.ip_address,
                    "model": reader.model or "Unknown",
                    "status": reader.status.value if reader.status else "unknown",
                    "last_scan_time": last_scan.timestamp.isoformat() if last_scan else None,
                    "scan_count": scan_count,
                    "zone_id": zone_id,
                    "mode": assignment.mode,
                    "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None
                }
                
                reader_status_data.append(reader_data)
            
            return {
                "success": True,
                "data": reader_status_data,
                "total_count": len(reader_status_data),
                "zone_id": zone_id
            }
            
        except Exception as e:
            logger.error(f"Error getting zone reader status: {e}")
            return {
                "success": False,
                "error": f"Failed to get zone reader status: {str(e)}"
            }

    # ── Personnel-location views ─────────────────────────────────────────────
    # These four are called by api/personnel.py but had never been written, so
    # /location-summary, /zone-capacity, /location-analytics and /by-location all
    # returned 500 ("'ZoneService' object has no attribute ..."). Zone occupancy is
    # derived from personnel.current_zone_id, which access-control readers maintain.

    async def get_current_location_summary(self, db: Session) -> Dict[str, Any]:
        """Where everyone currently is, one row per zone plus an unassigned bucket."""
        try:
            rows = db.execute(text("""
                SELECT z.id, z.name, z.code, z.zone_type,
                       COALESCE(z.max_capacity, 0)          AS max_capacity,
                       COUNT(p.id) FILTER (WHERE p.is_active) AS headcount
                FROM zones z
                LEFT JOIN personnel p ON p.current_zone_id = z.id
                WHERE COALESCE(z.is_active, TRUE)
                GROUP BY z.id, z.name, z.code, z.zone_type, z.max_capacity
                ORDER BY z.name
            """)).fetchall()
            unassigned = db.execute(text(
                "SELECT COUNT(*) FROM personnel WHERE is_active AND current_zone_id IS NULL"
            )).scalar() or 0
            on_pob = db.execute(text(
                "SELECT COUNT(*) FROM personnel WHERE is_active AND is_pob"
            )).scalar() or 0
            zones = [{
                "zone_id": r.id, "zone_name": r.name, "zone_code": r.code,
                "zone_type": r.zone_type, "headcount": int(r.headcount or 0),
                "max_capacity": int(r.max_capacity or 0),
            } for r in rows]
            return {
                "success": True,
                "total_personnel": sum(z["headcount"] for z in zones) + int(unassigned),
                "on_pob": int(on_pob),
                "unassigned": int(unassigned),
                "zones": zones,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"get_current_location_summary failed: {e}")
            return {"success": False, "error": str(e), "zones": []}

    async def get_zone_capacity_status(
        self, db: Session, zone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Occupancy against max_capacity, flagging zones at or over their limit.

        `zone` optionally narrows to a single zone by name or code — the API
        exposes it as a query parameter.
        """
        try:
            params = {}
            narrow = ""
            if zone:
                narrow = " AND (LOWER(z.name) = LOWER(:zone) OR LOWER(z.code) = LOWER(:zone))"
                params["zone"] = zone
            rows = db.execute(text(f"""
                SELECT z.id, z.name, z.code, COALESCE(z.max_capacity, 0) AS max_capacity,
                       COUNT(p.id) FILTER (WHERE p.is_active) AS headcount
                FROM zones z
                LEFT JOIN personnel p ON p.current_zone_id = z.id
                WHERE COALESCE(z.is_active, TRUE){narrow}
                GROUP BY z.id, z.name, z.code, z.max_capacity
                ORDER BY z.name
            """), params).fetchall()
            zones = []
            for r in rows:
                cap, head = int(r.max_capacity or 0), int(r.headcount or 0)
                # A zone with no configured capacity cannot be over it — report
                # utilisation as None rather than dividing by zero.
                pct = round(head / cap * 100, 1) if cap > 0 else None
                zones.append({
                    "zone_id": r.id, "zone_name": r.name, "zone_code": r.code,
                    "headcount": head, "max_capacity": cap,
                    "utilization_percent": pct,
                    "status": ("unlimited" if cap == 0 else
                               "over_capacity" if head > cap else
                               "at_capacity" if head == cap else
                               "near_capacity" if pct is not None and pct >= 85 else "ok"),
                })
            return {
                "success": True,
                "zones": zones,
                "over_capacity": [z for z in zones if z["status"] == "over_capacity"],
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"get_zone_capacity_status failed: {e}")
            return {"success": False, "error": str(e), "zones": []}

    async def get_location_analytics(self, db: Session, hours: int = 24) -> Dict[str, Any]:
        """Zone movement over a window, derived from access-control punches."""
        try:
            since = datetime.utcnow() - timedelta(hours=int(hours))
            movements = db.execute(text("""
                SELECT COALESCE(z.name, t.area_alias, 'Unknown') AS zone_name,
                       COUNT(*) AS movements,
                       COUNT(DISTINCT t.emp_code) AS unique_personnel
                FROM iclock_transaction t
                LEFT JOIN iclock_terminal term ON term.sn = t.terminal_sn
                LEFT JOIN zones z ON z.id = term.zone_id
                WHERE t.punch_time >= :since
                GROUP BY 1 ORDER BY movements DESC
            """), {"since": since}).fetchall()
            busiest = db.execute(text("""
                SELECT date_trunc('hour', punch_time) AS hour, COUNT(*) AS movements
                FROM iclock_transaction WHERE punch_time >= :since
                GROUP BY 1 ORDER BY movements DESC LIMIT 1
            """), {"since": since}).fetchone()
            return {
                "success": True,
                "window_hours": int(hours),
                "since": since.isoformat(),
                "by_zone": [{"zone_name": r.zone_name, "movements": int(r.movements),
                             "unique_personnel": int(r.unique_personnel)} for r in movements],
                "total_movements": sum(int(r.movements) for r in movements),
                "busiest_hour": busiest.hour.isoformat() if busiest and busiest.hour else None,
                "busiest_hour_movements": int(busiest.movements) if busiest else 0,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"get_location_analytics failed: {e}")
            return {"success": False, "error": str(e), "by_zone": []}

    async def get_personnel_by_location(
        self, db: Session, location: Optional[str] = None,
        zone: Optional[str] = None, status: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Personnel filtered by zone name/code and/or status."""
        try:
            clauses, params = ["p.is_active"], {}
            if zone:
                clauses.append("(LOWER(z.name) = LOWER(:zone) OR LOWER(z.code) = LOWER(:zone))")
                params["zone"] = zone
            if location:
                clauses.append("LOWER(COALESCE(z.name, '')) LIKE LOWER(:loc)")
                params["loc"] = f"%{location}%"
            if status is not None:
                clauses.append("UPPER(COALESCE(p.status, '')) = UPPER(:st)")
                params["st"] = getattr(status, "value", str(status))
            rows = db.execute(text(f"""
                SELECT p.id, p.emp_code, p.full_name, p.department, p.status,
                       p.is_pob, z.name AS zone_name, z.code AS zone_code, p.last_seen
                FROM personnel p
                LEFT JOIN zones z ON z.id = p.current_zone_id
                WHERE {' AND '.join(clauses)}
                ORDER BY p.emp_code
            """), params).fetchall()
            return [{
                "id": r.id, "emp_code": r.emp_code, "full_name": r.full_name,
                "department": r.department, "status": r.status, "is_pob": r.is_pob,
                "zone_name": r.zone_name, "zone_code": r.zone_code,
                "last_seen": r.last_seen.isoformat() if r.last_seen else None,
            } for r in rows]
        except Exception as e:
            logger.error(f"get_personnel_by_location failed: {e}")
            return []
