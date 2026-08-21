"""
Resignation Management Service
Handles employee resignation workflow and separation process
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio

from ..core.database import get_db
from ..models.resignation import (
    Resignation, ResignationTask, ResignationDocument, ResignationTemplate, ResignationNotification
)
from ..models.personnel import Personnel
from ..models.biotime_models import IClockTerminal

logger = logging.getLogger(__name__)


class ResignationService:
    """Service for resignation management operations"""
    
    def __init__(self):
        self.active_workflows = {}
        
    async def create_resignation(
        self,
        resignation_data: dict,
        db: Session,
        created_by: int
    ) -> Dict[str, Any]:
        """Create new resignation"""
        try:
            # Verify personnel exists and is active
            personnel = db.query(Personnel).filter(Personnel.id == resignation_data["personnel_id"]).first()
            if not personnel:
                return {"success": False, "error": "Personnel not found"}
            
            # Check if resignation already exists
            existing = db.query(Resignation).filter(
                and_(
                    Resignation.personnel_id == resignation_data["personnel_id"],
                    Resignation.status.in_(["PENDING", "APPROVED", "PROCESSING"])
                )
            ).first()
            
            if existing:
                return {"success": False, "error": "Active resignation already exists for this personnel"}
            
            # Create resignation
            resignation = Resignation(
                personnel_id=resignation_data["personnel_id"],
                resignation_type=resignation_data["resignation_type"],
                resignation_date=resignation_data["resignation_date"],
                last_working_day=resignation_data["last_working_day"],
                reason=resignation_data["reason"],
                detailed_reason=resignation_data.get("detailed_reason"),
                exit_interview_date=resignation_data.get("exit_interview_date"),
                handover_checklist=resignation_data.get("handover_checklist"),
                financial_clearance_notes=resignation_data.get("financial_clearance_notes"),
                assets_return_checklist=resignation_data.get("assets_return_checklist"),
                created_by=created_by,
                notes=resignation_data.get("notes")
            )
            
            db.add(resignation)
            db.commit()
            db.refresh(resignation)
            
            # Create default tasks based on template
            await self._create_default_tasks(resignation.id, db)
            
            # Update personnel status to indicate resignation process
            personnel.status = "INACTIVE"  # Or appropriate status
            db.commit()
            
            # Send notifications
            await self._send_notification(
                resignation.id, "CREATED", 
                f"Resignation initiated for {personnel.full_name}",
                [created_by, personnel.user_id if personnel.user_id else None],
                db
            )
            
            logger.info(f"Created resignation for personnel {resignation_data['personnel_id']}")
            
            return {
                "success": True,
                "data": {
                    "id": resignation.id,
                    "personnel_id": resignation.personnel_id,
                    "status": resignation.status.value
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating resignation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_resignation(
        self,
        resignation_id: int,
        update_data: dict,
        db: Session,
        updated_by: int
    ) -> Dict[str, Any]:
        """Update existing resignation"""
        try:
            resignation = db.query(Resignation).filter(Resignation.id == resignation_id).first()
            
            if not resignation:
                return {"success": False, "error": "Resignation not found"}
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(resignation, field):
                    setattr(resignation, field, value)
            
            resignation.updated_by = updated_by
            db.commit()
            
            # Handle status changes
            if "status" in update_data:
                await self._handle_status_change(resignation, db)
            
            logger.info(f"Updated resignation {resignation_id}")
            
            return {
                "success": True,
                "data": {
                    "id": resignation.id,
                    "status": resignation.status.value
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating resignation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def approve_resignation(
        self,
        resignation_id: int,
        approved_by: int,
        notes: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Approve resignation"""
        try:
            resignation = db.query(Resignation).filter(Resignation.id == resignation_id).first()
            
            if not resignation:
                return {"success": False, "error": "Resignation not found"}
            
            # Update approval
            resignation.status = "APPROVED"
            resignation.approved_by = approved_by
            resignation.approved_at = datetime.utcnow()
            resignation.notes = notes
            db.commit()
            
            # Send device sync command
            await self._send_device_command(
                resignation.personnel_id, 
                "DATA DELETE USERINFO",
                f"Delete user {resignation.personnel.badge_id} from device",
                db
            )
            
            # Send notifications
            await self._send_notification(
                resignation_id, "APPROVED",
                f"Resignation approved for {resignation.personnel.full_name}",
                [approved_by, resignation.personnel.user_id if resignation.personnel.user_id else None],
                db
            )
            
            logger.info(f"Approved resignation {resignation_id}")
            
            return {
                "success": True,
                "message": "Resignation approved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error approving resignation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def reject_resignation(
        self,
        resignation_id: int,
        rejection_reason: str,
        rejected_by: int,
        notes: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Reject resignation"""
        try:
            resignation = db.query(Resignation).filter(Resignation.id == resignation_id).first()
            
            if not resignation:
                return {"success": False, "error": "Resignation not found"}
            
            # Update rejection
            resignation.status = "REJECTED"
            resignation.approved_by = rejected_by
            rejection_reason = rejection_reason
            resignation.notes = notes
            db.commit()
            
            # Send notifications
            await self._send_notification(
                resignation_id, "REJECTED",
                f"Resignation rejected for {resignation.personnel.full_name}",
                [rejected_by, resignation.personnel.user_id if resignation.personnel.user_id else None],
                db
            )
            
            logger.info(f"Rejected resignation {resignation_id}")
            
            return {
                "success": True,
                "message": "Resignation rejected successfully"
            }
            
        except Exception as e:
            logger.error(f"Error rejecting resignation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_resignations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        resignation_type: Optional[str] = None,
        personnel_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get resignations with filtering and pagination"""
        try:
            query = db.query(Resignation)
            
            # Apply filters
            if search:
                query = query.filter(
                    or_(
                        Resignation.reason.ilike(f"%{search}%"),
                        Resignation.detailed_reason.ilike(f"%{search}%")
                    )
                )
            
            if status:
                query = query.filter(Resignation.status == status)
            
            if resignation_type:
                query = query.filter(Resignation.resignation_type == resignation_type)
            
            if personnel_id:
                query = query.filter(Resignation.personnel_id == personnel_id)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            resignations = query.order_by(desc(Resignation.created_at)).offset(skip).limit(limit).all()
            
            # Enhance with personnel data
            result_resignations = []
            for resignation in resignations:
                resignation_data = {
                    "id": resignation.id,
                    "personnel_id": resignation.personnel_id,
                    "resignation_type": resignation.resignation_type.value,
                    "status": resignation.status.value,
                    "resignation_date": resignation.resignation_date,
                    "last_working_day": resignation.last_working_day,
                    "reason": resignation.reason,
                    "detailed_reason": resignation.detailed_reason,
                    "exit_interview_date": resignation.exit_interview_date,
                    "handover_completed": resignation.handover_completed,
                    "financial_clearance_completed": resignation.financial_clearance_completed,
                    "assets_returned": resignation.assets_returned,
                    "system_access_revoked": resignation.system_access_revoked,
                    "device_access_removed": resignation.device_access_removed,
                    "created_at": resignation.created_at,
                    "updated_at": resignation.updated_at,
                    "notes": resignation.notes
                }
                
                # Add personnel info as nested employee object (matches frontend shape)
                if resignation.personnel:
                    p = resignation.personnel
                    resignation_data["employee"] = {
                        "id": p.id,
                        "emp_code": p.emp_code,
                        "badge_id": p.badge_id,
                        "full_name": p.full_name or f"{p.first_name or ''} {p.last_name or ''}".strip(),
                        "first_name": p.first_name,
                        "last_name": p.last_name,
                        "company": p.company,
                        "department": p.department,
                        "role": p.role,
                        "position": p.position,
                    }
                else:
                    resignation_data["employee"] = {}
                
                # Calculate completion percentage
                resignation_data["completion_percentage"] = self._calculate_completion_percentage(resignation, db)
                resignation_data["tasks_completed"] = self._count_completed_tasks(resignation.id, db)
                resignation_data["total_tasks"] = self._count_total_tasks(resignation.id, db)
                
                result_resignations.append(resignation_data)
            
            return {
                "success": True,
                "data": result_resignations,
                "total_count": total_count,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting resignations: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_resignation_by_id(
        self,
        resignation_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get resignation by ID"""
        try:
            resignation = db.query(Resignation).filter(Resignation.id == resignation_id).first()
            
            if not resignation:
                return {"success": False, "error": "Resignation not found"}
            
            # Enhance with related data
            resignation_data = {
                "id": resignation.id,
                "personnel_id": resignation.personnel_id,
                "resignation_type": resignation.resignation_type.value,
                "status": resignation.status.value,
                "resignation_date": resignation.resignation_date,
                "last_working_day": resignation.last_working_day,
                "reason": resignation.reason,
                "detailed_reason": resignation.detailed_reason,
                
                # Exit interview
                "exit_interview_date": resignation.exit_interview_date,
                "exit_interview_conducted_by": resignation.exit_interview_conducted_by,
                "exit_interview_notes": resignation.exit_interview_notes,
                
                # Handover process
                "handover_completed": resignation.handover_completed,
                "handover_date": resignation.handover_date,
                "handover_conducted_by": resignation.handover_conducted_by,
                "handover_notes": resignation.handover_notes,
                "handover_checklist": resignation.handover_checklist,
                
                # Financial clearance
                "financial_clearance_completed": resignation.financial_clearance_completed,
                "financial_clearance_date": resignation.financial_clearance_date,
                "financial_clearance_conducted_by": resignation.financial_clearance_conducted_by,
                "financial_clearance_notes": resignation.financial_clearance_notes,
                
                # Asset return
                "assets_returned": resignation.assets_returned,
                "assets_return_date": resignation.assets_return_date,
                "assets_return_conducted_by": resignation.assets_return_conducted_by,
                "assets_return_notes": resignation.assets_return_notes,
                "assets_return_checklist": resignation.assets_return_checklist,
                
                # System access
                "system_access_revoked": resignation.system_access_revoked,
                "system_access_revoked_date": resignation.system_access_revoked_date,
                "system_access_revoked_by": resignation.system_access_revoked_by,
                "device_access_removed": resignation.device_access_removed,
                
                # Final approval
                "approved_by": resignation.approved_by,
                "approved_at": resignation.approved_at,
                "rejection_reason": resignation.rejection_reason,
                
                # Completion
                "completed_at": resignation.completed_at,
                "completed_by": resignation.completed_by,
                
                # Audit
                "created_by": resignation.created_by,
                "created_at": resignation.created_at,
                "updated_at": resignation.updated_at,
                "notes": resignation.notes
            }
            
            # Add personnel info as nested employee object
            if resignation.personnel:
                p = resignation.personnel
                resignation_data["employee"] = {
                    "id": p.id,
                    "emp_code": p.emp_code,
                    "badge_id": p.badge_id,
                    "full_name": p.full_name or f"{p.first_name or ''} {p.last_name or ''}".strip(),
                    "first_name": p.first_name,
                    "last_name": p.last_name,
                    "company": p.company,
                    "department": p.department,
                    "role": p.role,
                    "position": p.position,
                }
            else:
                resignation_data["employee"] = {}

            # Calculate completion percentage
            resignation_data["completion_percentage"] = self._calculate_completion_percentage(resignation, db)
            resignation_data["tasks_completed"] = self._count_completed_tasks(resignation.id, db)
            resignation_data["total_tasks"] = self._count_total_tasks(resignation.id, db)
            
            return {
                "success": True,
                "data": resignation_data
            }
            
        except Exception as e:
            logger.error(f"Error getting resignation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_resignation_statistics(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """Get resignation statistics"""
        try:
            # Total resignations
            total_resignations = db.query(Resignation).count()
            
            # By status
            pending_resignations = db.query(Resignation).filter(Resignation.status == "PENDING").count()
            approved_resignations = db.query(Resignation).filter(Resignation.status == "APPROVED").count()
            processing_resignations = db.query(Resignation).filter(Resignation.status == "PROCESSING").count()
            completed_resignations = db.query(Resignation).filter(Resignation.status == "COMPLETED").count()
            
            # By type
            type_results = db.query(
                Resignation.resignation_type, func.count(Resignation.id)
            ).group_by(Resignation.resignation_type).all()
            
            resignations_by_type = {}
            for res_type, count in type_results:
                resignations_by_type[res_type.value] = count
            
            # By month
            month_results = db.query(
                func.date_trunc('month', Resignation.created_at).label('month'),
                func.count(Resignation.id).label('count')
            ).group_by(func.date_trunc('month', Resignation.created_at)).all()
            
            resignations_by_month = {}
            for month, count in month_results:
                resignations_by_month[str(month)] = count
            
            # Average processing time (simulated)
            average_processing_days = 15.5  # Simulated average
            
            return {
                "success": True,
                "data": {
                    "total_resignations": total_resignations,
                    "pending_resignations": pending_resignations,
                    "approved_resignations": approved_resignations,
                    "processing_resignations": processing_resignations,
                    "completed_resignations": completed_resignations,
                    "resignations_by_type": resignations_by_type,
                    "resignations_by_month": resignations_by_month,
                    "average_processing_days": average_processing_days
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting resignation statistics: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _create_default_tasks(self, resignation_id: int, db: Session):
        """Create default tasks for resignation"""
        try:
            default_tasks = [
                {
                    "task_name": "Exit Interview",
                    "task_type": "EXIT_INTERVIEW",
                    "description": "Conduct exit interview with departing employee",
                    "is_required": True,
                    "due_date": datetime.utcnow() + timedelta(days=3)
                },
                {
                    "task_name": "Handover Process",
                    "task_type": "HANDOVER",
                    "description": "Complete handover of responsibilities and duties",
                    "is_required": True,
                    "due_date": datetime.utcnow() + timedelta(days=7)
                },
                {
                    "task_name": "Financial Clearance",
                    "task_type": "FINANCIAL",
                    "description": "Complete financial clearance process",
                    "is_required": True,
                    "due_date": datetime.utcnow() + timedelta(days=10)
                },
                {
                    "task_name": "Asset Return",
                    "task_type": "ASSET_RETURN",
                    "description": "Return company assets and equipment",
                    "is_required": True,
                    "due_date": datetime.utcnow() + timedelta(days=14)
                },
                {
                    "task_name": "System Access Revocation",
                    "task_type": "SYSTEM_ACCESS",
                    "description": "Revoke system and device access",
                    "is_required": True,
                    "due_date": datetime.utcnow() + timedelta(days=1)
                }
            ]
            
            for task_data in default_tasks:
                task = ResignationTask(
                    resignation_id=resignation_id,
                    task_name=task_data["task_name"],
                    task_type=task_data["task_type"],
                    description=task_data["description"],
                    is_required=task_data["is_required"],
                    due_date=task_data["due_date"]
                )
                
                db.add(task)
            
            db.commit()
            logger.info(f"Created default tasks for resignation {resignation_id}")
            
        except Exception as e:
            logger.error(f"Error creating default tasks: {str(e)}")
    
    async def _handle_status_change(self, resignation: Resignation, db: Session):
        """Handle resignation status changes"""
        try:
            if resignation.status.value == "APPROVED":
                # Mark resignation as processing
                resignation.status = "PROCESSING"
                db.commit()
                
                # Update personnel status
                if resignation.personnel:
                    resignation.personnel.status = "INACTIVE"
                    db.commit()
                
                # Send device command
                await self._send_device_command(
                    resignation.personnel_id,
                    "DATA DELETE USERINFO",
                    f"Delete user {resignation.personnel.badge_id} from device",
                    db
                )
            
            elif resignation.status.value == "COMPLETED":
                # Ensure all access is revoked
                resignation.system_access_revoked = True
                resignation.system_access_revoked_date = datetime.utcnow()
                resignation.completed_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Completed resignation process for personnel {resignation.personnel_id}")
            
        except Exception as e:
            logger.error(f"Error handling status change: {str(e)}")
    
    async def _send_device_command(self, personnel_id: int, command: str, message: str, db: Session = None):
        """Send command to device for personnel"""
        try:
            # Get devices assigned to personnel
            devices = db.query(IClockTerminal).all()
            
            for device in devices:
                # Simulate sending command to device
                logger.info(f"Sending command '{command}' to device {device.sn}: {message}")
                
                # In real implementation, this would:
                # 1. Create command in iclock_devcmd table
                # 2. Device would pick up command on next poll
                # 3. Execute command and update status
                
        except Exception as e:
            logger.error(f"Error sending device command: {str(e)}")
    
    async def _send_notification(self, resignation_id: int, notification_type: str, message: str, recipients: List[int], db: Session = None):
        """Send notification for resignation event"""
        try:
            for recipient_id in recipients:
                notification = ResignationNotification(
                    resignation_id=resignation_id,
                    notification_type=notification_type,
                    recipient_id=recipient_id,
                    title=f"Resignation {notification_type}",
                    message=message,
                    sent_via="IN_APP",
                    sent_at=datetime.utcnow()
                )
                
                db.add(notification)
            
            db.commit()
            logger.info(f"Sent notification for resignation {resignation_id}: {notification_type}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
    
    def _calculate_completion_percentage(self, resignation: Resignation, db: Session = None) -> float:
        """Calculate resignation completion percentage"""
        try:
            if not resignation:
                return 0.0
            
            # Define task weights
            task_weights = {
                "EXIT_INTERVIEW": 15,
                "HANDOVER": 25,
                "FINANCIAL": 20,
                "ASSET_RETURN": 20,
                "SYSTEM_ACCESS": 20
            }
            
            # Get completed tasks
            completed_tasks = db.query(ResignationTask).filter(
                and_(
                    ResignationTask.resignation_id == resignation.id,
                    ResignationTask.is_completed == True
                )
            ).all()
            
            total_weight = 0
            completed_weight = 0
            
            for task in completed_tasks:
                weight = task_weights.get(task.task_type, 0)
                total_weight += weight
                completed_weight += weight
            
            return (completed_weight / total_weight * 100) if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating completion percentage: {str(e)}")
            return 0.0
    
    def _count_completed_tasks(self, resignation_id: int, db: Session) -> int:
        """Count completed tasks for resignation"""
        try:
            return db.query(ResignationTask).filter(
                and_(
                    ResignationTask.resignation_id == resignation_id,
                    ResignationTask.is_completed == True
                )
            ).count()
        except Exception as e:
            logger.error(f"Error counting completed tasks: {str(e)}")
            return 0
    
    def _count_total_tasks(self, resignation_id: int, db: Session) -> int:
        """Count total tasks for resignation"""
        try:
            return db.query(ResignationTask).filter(
                ResignationTask.resignation_id == resignation_id
            ).count()
        except Exception as e:
            logger.error(f"Error counting total tasks: {str(e)}")
            return 0


# Create service instance
resignation_service = ResignationService()
