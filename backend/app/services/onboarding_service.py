"""
Onboarding Management Service
Handles employee onboarding workflow and process management
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio

from ..core.database import get_db
from ..models.onboarding import (
    Onboarding, OnboardingTask, OnboardingDocument, OnboardingTemplate, OnboardingNotification, OnboardingChecklist,
    OnboardingStatus, OnboardingType, TaskType, TaskPriority
)
from ..models.personnel import Personnel
from ..models.department import Department
from ..models.position import Position
from ..models.custom_attributes import CustomAttribute, CustomAttributeValue

logger = logging.getLogger(__name__)


class OnboardingService:
    """Service for onboarding management operations"""
    
    def __init__(self):
        self.active_workflows = {}
        
    async def create_onboarding(
        self,
        onboarding_data: dict,
        db: Session,
        created_by: int
    ) -> Dict[str, Any]:
        """Create new onboarding"""
        try:
            # Verify personnel exists
            personnel = db.query(Personnel).filter(Personnel.id == onboarding_data["personnel_id"]).first()
            if not personnel:
                return {"success": False, "error": "Personnel not found"}
            
            # Check if active onboarding already exists
            existing = db.query(Onboarding).filter(
                and_(
                    Onboarding.personnel_id == onboarding_data["personnel_id"],
                    Onboarding.status.in_(["NOT_STARTED", "IN_PROGRESS", "PENDING_REVIEW", "APPROVED"])
                )
            ).first()
            
            if existing:
                return {"success": False, "error": "Active onboarding already exists for this personnel"}
            
            # Create onboarding
            onboarding = Onboarding(
                personnel_id=onboarding_data["personnel_id"],
                onboarding_type=onboarding_data["onboarding_type"],
                status=OnboardingStatus.NOT_STARTED,
                start_date=onboarding_data["start_date"],
                planned_end_date=onboarding_data["planned_end_date"],
                job_title=onboarding_data["job_title"],
                job_description=onboarding_data["job_description"],
                department_id=onboarding_data.get("department_id"),
                position_id=onboarding_data.get("position_id"),
                reporting_to=onboarding_data.get("reporting_to"),
                buddy_id=onboarding_data.get("buddy_id"),
                manager_id=onboarding_data.get("manager_id"),
                template_id=onboarding_data.get("template_id"),
                template_data=onboarding_data.get("template_data"),
                custom_fields=onboarding_data.get("custom_fields"),
                created_by=created_by
            )
            
            db.add(onboarding)
            db.commit()
            db.refresh(onboarding)
            
            # Create default tasks based onboarding template
            if onboarding.template_id:
                await self._create_default_tasks(onboarding.id, db)
            
            # Update personnel status to indicate onboarding process
            if personnel:
                personnel.status = "INACTIVE"  # Or appropriate status
                db.commit()
            
            # Send notifications
            await self._send_notification(
                onboarding.id, "CREATED",
                f"Onboarding initiated for {personnel.full_name}",
                [created_by, personnel.user_id if personnel.user_id else None]
            )
            
            logger.info(f"Created onboarding for personnel {onboarding_data['personnel_id']}")
            
            return {
                "success": True,
                "data": {
                    "id": onboarding.id,
                    "status": onboarding.status.value,
                    "onboarding_type": onboarding.onboarding_type.value
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating onboarding: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_onboarding(
        self,
        onboarding_id: int,
        update_data: dict,
        db: Session,
        updated_by: int
    ) -> Dict[str, Any]:
        """Update existing onboarding"""
        try:
            onboarding = db.query(Onboarding).filter(Onboarding.id == onboarding_id).first()
            
            if not onboarding:
                return {"success": False, "error": "Onboarding not found"}
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(onboarding, field):
                    setattr(onboarding, field, value)
            
            onboarding.updated_by = updated_by
            db.commit()
            
            # Handle status changes
            if "status" in update_data:
                await self._handle_status_change(onboarding, db)
            
            logger.info(f"Updated onboarding {onboarding_id}")
            
            return {
                "success": True,
                "data": {
                    "id": onboarding.id,
                    "status": onboarding.status.value
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating onboarding: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def approve_onboarding(
        self,
        onboarding_id: int,
        approved_by: int,
        notes: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Approve onboarding"""
        try:
            onboarding = db.query(Onboarding).filter(Onboarding.id == onboarding_id).first()
            
            if not onboarding:
                return {"success": False, "error": "Onboarding not found"}
            
            # Check if can be approved
            if onboarding.status not in ["PENDING_REVIEW", "IN_PROGRESS"]:
                return {"success": False, "error": "Onboarding not ready for approval"}
            
            # Update approval
            onboarding.status = OnboardingStatus.APPROVED
            onboarding.approved_by = approved_by
            onboarding.approved_at = datetime.utcnow()
            db.commit()
            
            # Send notifications
            await self._send_notification(
                onboarding.id, "APPROVED",
                f"Onboarding approved for {onboarding.personnel.full_name}",
                [approved_by, onboarding.personnel.user_id if onboarding.personnel.user_id else None]
            )
            
            logger.info(f"Approved onboarding {onboarding_id}")
            
            return {
                "success": True,
                "message": "Onboarding approved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error approving onboarding: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def reject_onboarding(
        self,
        onboarding_id: int,
        rejection_reason: str,
        rejected_by: int,
        notes: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Reject onboarding"""
        try:
            onboarding = db.query(Onboarding).filter(Onboarding.id == onboarding_id).first()
            
            if not onboarding:
                return {"success": False, "error": "Onboarding not found"}
            
            # Update rejection
            onboarding.status = OnboardingStatus.REJECTED
            onboarding.rejection_reason = rejection_reason
            onboarding.approved_by = rejected_by
            onboarding.rejected_at = datetime.utcnow()
            db.commit()
            
            # Send notifications
            await self._send_notification(
                onboarding.id, "REJECTED",
                f"Onboarding rejected for {onboarding.personnel.full_name}: {rejection_reason}",
                [rejected_by, onboarding.personnel.user_id if onboarding.personnel.user_id else None]
            )
            
            logger.info(f"Rejected onboarding {onboarding_id}")
            
            return {
                "success": True,
                "message": f"Onboarding rejected: {rejection_reason}"
            }
            
        except Exception as e:
            logger.error(f"Error rejecting onboarding: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_onboardings(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        onboarding_type: Optional[str] = None,
        personnel_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date_from: Optional[str] = None,
        start_date_to: Optional[str] = None,
        is_completed: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get onboardings with filtering and pagination"""
        try:
            query = db.query(Onboarding)
            
            # Apply filters
            if search:
                query = query.filter(
                    or_(
                        Onboarding.job_title.ilike(f"%{search}%"),
                        Onboarding.job_description.ilike(f"%{search}%")
                    )
                )
            
            if status:
                query = query.filter(Onboarding.status == status)
            
            if onboarding_type:
                query = query.filter(Onboarding.onboarding_type == onboarding_type)
            
            if personnel_id:
                query = query.filter(Onboarding.personnel_id == personnel_id)
            
            if department_id:
                query = query.filter(Onboarding.department_id == department_id)
            
            if start_date_from:
                query = query.filter(Onboarding.start_date >= start_date_from)
            
            if start_date_to:
                query = query.filter(Onboarding.start_date <= start_date_to)
            
            if is_completed is not None:
                query = query.filter(Onboarding.status == "COMPLETED")
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            onboardings = query.order_by(desc(Onboarding.created_at)).offset(skip).limit(limit).all()
            
            # Enhance with related data
            result_onboardings = []
            for onboarding in onboardings:
                onboarding_data = {
                    "id": onboarding.id,
                    "personnel_id": onboarding.personnel_id,
                    "onboarding_type": onboarding.onboarding_type.value,
                    "status": onboarding.status.value,
                    "start_date": onboarding.start_date,
                    "planned_end_date": onboarding.planned_end_date,
                    "actual_end_date": onboarding.actual_end_date,
                    "job_title": onboarding.job_title,
                    "job_description": onboarding.job_description,
                    "department_id": onboarding.department_id,
                    "position_id": onboarding.position_id,
                    "reporting_to": onboarding.reporting_to,
                    "buddy_id": onboarding.buddy_id,
                    "manager_id": onboarding.manager_id,
                    "template_id": onboarding.template_id,
                    "completion_percentage": onboarding.completion_percentage,
                    "last_progress_update": onboarding.last_progress_update,
                    "created_at": onboarding.created_at,
                    "updated_at": onboarding.updated_at,
                    "notes": onboarding.notes
                }
                
                # Add personnel info as nested employee object
                if onboarding.personnel:
                    p = onboarding.personnel
                    onboarding_data["employee"] = {
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
                    onboarding_data["employee"] = {}

                result_onboardings.append(onboarding_data)
            
            return {
                "success": True,
                "data": result_onboardings,
                "total_count": total_count,
                "skip": skip,
                "limit": limit,
                "page": (skip // limit) + 1,
                "total_pages": (total_count + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Error getting onboardings: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_onboarding_by_id(
        self,
        onboarding_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get onboarding by ID"""
        try:
            onboarding = db.query(Onboarding).filter(Onboarding.id == onboarding_id).first()
            
            if not onboarding:
                return {"success": False, "error": "onboarding not found"}
            
            # Enhance with related data
            onboarding_data = {
                "id": onboarding.id,
                "personnel_id": onboarding.personnel_id,
                "onboarding_type": onboarding.onboarding_type.value,
                "status": onboarding.status.value,
                "start_date": onboarding.start_date,
                "planned_end_date": onboarding.planned_end_date,
                "actual_end_date": onboarding.actual_end_date,
                "job_title": onboarding.job_title,
                "job_description": onboarding.job_description,
                "department_id": onboarding.department_id,
                "position_id": onboarding.position_id,
                "reporting_to": onboarding.reporting_to,
                "buddy_id": onboarding.buddy_id,
                "manager_id": onboarding.manager_id,
                "template_id": onboarding.template_id,
                "completion_percentage": onboarding.completion_percentage,
                "last_progress_update": onboarding.last_progress_update,
                "created_at": onboarding.created_at,
                "updated_at": onboarding.updated_at,
                "notes": onboarding.notes
            }
            
            # Add personnel info as nested employee object
            if onboarding.personnel:
                p = onboarding.personnel
                onboarding_data["employee"] = {
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
                onboarding_data["employee"] = {}

            return {
                "success": True,
                "data": onboarding_data
            }

        except Exception as e:
            logger.error(f"Error getting onboarding by ID: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_onboarding_tasks(
        self,
        onboarding_id: int,
        db: Session,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        is_completed: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get onboarding tasks"""
        try:
            from ..models.onboarding import OnboardingTask
            
            query = db.query(OnboardingTask).filter(
                OnboardingTask.onboarding_id == onboarding_id
            )
            
            if status:
                query = query.filter(OnboardingTask.status == status)
            
            if task_type:
                query = query.filter(OnboardingTask.task_type == task_type)
            
            # Get completed tasks count
            completed_count = query.filter(
                and_(
                    OnboardingTask.onboarding_id == onboarding_id,
                    OnboardingTask.is_completed == True
                )
            ).count()
            
            # Get total tasks count
            total_tasks = query.count()
            
            # Apply sorting
            tasks = query.order_by(OnboardingTask.due_date, OnboardingTask.sort_order).all()
            
            result_tasks = []
            for task in tasks:
                task_data = {
                    "id": task.id,
                    "onboarding_id": task.onboarding_id,
                    "task_name": task.task_name,
                    "task_type": task.task_type,
                    "description": task.description,
                    "is_required": task.is_required,
                    "due_date": task.due_date,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "completion_date": task.completion_date,
                    "completed_by": task.completed_by,
                    "completion_notes": task.completion_notes,
                    "checklist_items": task.checklist_items,
                    "completed_items": task.completed_items,
                    "depends_on_tasks": task.depends_on,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "notes": task.notes
                }
                
                result_tasks.append(task_data)
            
            return {
                "success": True,
                "data": result_tasks,
                "total_tasks": total_tasks,
                "completed_count": completed_count
            }
            
        except Exception as e:
            logger.error(f"Error getting onboarding tasks: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_onboarding_task(
        self,
        task_data: dict,
        db: Session,
        created_by: int = 1
    ) -> Dict[str, Any]:
        """Create onboarding task"""
        try:
            from ..models.onboarding import OnboardingTask
            
            # Create task
            task = OnboardingTask(
                onboarding_id=task_data["onboarding_id"],
                task_name=task_data["task_name"],
                task_type=task_data["task_type"],
                description=task_data.get("description"),
                is_required=task_data.get("is_required", True),
                due_date=task_data.get("due_date"),
                priority=task_data.get("priority", TaskPriority.MEDIUM),
                checklist_items=task_data.get("checklist_items"),
                depends_on_tasks=task_data.get("depends_on_tasks", []),
                created_by=created_by
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            logger.info(f"Created onboarding task {task_data['task_name']} for onboarding {task_data['onboarding_id']}")
            
            return {
                "success": True,
                "data": {
                    "id": task.id,
                    "task_name": task.task_name,
                    "onboarding_id": task.onboarding_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating onboarding task: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_onboarding_task(
        self,
        task_id: int,
        update_data: dict,
        db: Session,
        updated_by: int = 1
    ) -> Dict[str, Any]:
        """Update onboarding task"""
        try:
            from ..models.onboarding import OnboardingTask
            
            task = db.query(OnboardingTask).filter(OnboardingTask.id == task_id).first()
            
            if not task:
                return {"success": False, "error": "Task not found"}
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(task, field):
                    setattr(task, field, value)
            
            task.updated_by = updated_by
            db.commit()
            
            # Handle completion
            if update_data.get("is_completed") and not task.completion_date:
                task.completion_date = datetime.utcnow()
                task.completed_by = updated_by
                db.commit()
            
            logger.info(f"Updated onboarding task {task_id}")
            
            return {
                "success": True,
                "data": {
                    "id": task.id,
                    "status": task.status,
                    "completion_date": task.completion_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating onboarding task: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def complete_onboarding(
        self,
        onboarding_id: int,
        completed_by: int = 1,
        db: Session = None
    ) -> Dict[str, Any]:
        """Complete onboarding"""
        try:
            onboarding = db.query(Onboarding).filter(Onboarding.id == onboarding_id).first()
            
            if not onboarding:
                return {"success": False, "error": "Onboarding not found"}
            
            # Update status to completed
            onboarding.status = OnboardingStatus.COMPLETED
            onboarding.actual_end_date = datetime.utcnow()
            onboarding.completed_at = datetime.utcnow()
            onboarding.completed_by = completed_by
            db.commit()
            
            # Update personnel status
            if onboarding.personnel:
                onboarding.personnel.status = "ACTIVE"  # Or appropriate status
                db.commit()
            
            # Send notifications
            await self._send_notification(
                onboarding.id, "COMPLETED",
                f"Onboarding completed for {onboarding.personnel.full_name}",
                [completed_by, onboarding.personnel.user_id if onboarding.personnel.user_id else None]
            )
            
            logger.info(f"Completed onboarding {onboarding_id}")
            
            return {
                "success": True,
                "message": "Onboarding completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error completing onboarding: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _create_default_tasks(
        self,
        onboarding_id: int,
        db: Session
    ) -> None:
        """Create default tasks based onboarding template"""
        try:
            from ..models.onboarding import Onboarding, OnboardingTask, OnboardingTemplate

            onboarding = db.query(Onboarding).filter(Onboarding.id == onboarding_id).first()
            if not onboarding:
                return

            if onboarding.template_id:
                template = db.query(OnboardingTemplate).filter(
                    OnboardingTemplate.id == onboarding.template_id
                ).first()
                
                if template and template.default_tasks:
                    for task_data in template.default_tasks:
                        task = OnboardingTask(
                            onboarding_id=onboarding_id,
                            task_name=task_data["task_name"],
                            task_type=task_data["task_type"],
                            description=task_data["description"],
                            is_required=task_data["is_required"],
                            due_date=datetime.utcnow() + timedelta(days=task_data.get("due_days", 7)),
                            priority=task_data.get("priority", TaskPriority.MEDIUM),
                            checklist_items=task_data.get("checklist_items", []),
                            created_by=1
                        )
                        
                        db.add(task)
                    
                    db.commit()
                    logger.info(f"Created {len(template.default_tasks)} default tasks for onboarding {onboarding_id}")
            
        except Exception as e:
            logger.error(f"Error creating default tasks: {str(e)}")
    
    async def _handle_status_change(
        self,
        onboarding: Onboarding,
        db: Session
    ) -> None:
        """Handle onboarding status changes"""
        try:
            if onboarding.status == OnboardingStatus.APPROVED:
                # Update personnel status
                if onboarding.personnel:
                    onboarding.personnel.status = "ACTIVE"
                    db.commit()
                
                # Send device sync command
                await self._send_device_command(
                    onboarding.personnel_id,
                    "DATA UPDATE USERINFO",
                    f"Update user {onboarding.personnel.badge_id} on device"
                )
                
            elif onboarding.status == OnboardingStatus.COMPLETED:
                # Ensure all tasks are completed
                await self._check_all_tasks_completed(onboarding.id, db)
                
                # Update personnel status
                if onboarding.personnel:
                    onboarding.personnel.status = "ACTIVE"
                    db.commit()
                
                logger.info(f"Onboarding completed for personnel {onboarding.personnel_id}")
            
            elif onboarding.status == OnboardingStatus.CANCELLED:
                # Update personnel status
                if onboarding.personnel:
                    onboarding.personnel.status = "ACTIVE"
                    db.commit()
                
                logger.info(f"Onboarding cancelled for personnel {onboarding.personnel_id}")
            
        except Exception as e:
            logger.error(f"Error handling status change: {str(e)}")
    
    async def _send_notification(
        self,
        onboarding_id: int,
        notification_type: str,
        message: str,
        recipients: List[int],
        db: Session = None
    ) -> None:
        """Send notification"""
        try:
            from ..models.onboarding import OnboardingNotification
            
            for recipient_id in recipients:
                notification = OnboardingNotification(
                    onboarding_id=onboarding_id,
                    notification_type=notification_type,
                    recipient_id=recipient_id,
                    title=f"Onboarding {notification_type}",
                    message=message,
                    sent_via="IN_APP",
                    sent_at=datetime.utcnow()
                )
                
                db.add(notification)
            
            db.commit()
            logger.info(f"Sent notification for onboarding {onboarding_id}: {notification_type}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
    
    def _check_all_tasks_completed(
        self,
        onboarding_id: int,
        db: Session
    ) -> bool:
        """Check if all tasks are completed"""
        try:
            from ..models.onboarding import OnboardingTask
            
            uncompleted_tasks = db.query(OnboardingTask).filter(
                and_(
                    OnboardingTask.onboarding_id == onboarding_id,
                    or_(
                        OnboardingTask.is_completed == False
                    )
                )
            ).count()
            
            return uncompleted_tasks == 0
        
        except Exception as e:
            logger.error(f"Error checking task completion: {str(e)}")
            return False
    
    def _get_completion_percentage(
        self,
        onboarding_id: int,
        db: Session
    ) -> float:
        """Calculate onboarding completion percentage"""
        try:
            from ..models.onboarding import OnboardingTask
            
            # Get all tasks for this onboarding
            total_tasks = db.query(OnboardingTask).filter(
                OnboardingTask.onboarding_id == onboarding_id
            ).count()
            
            if total_tasks == 0:
                return 0.0
            
            # Get completed tasks count
            completed_tasks = db.query(OnboardingTask).filter(
                and_(
                    OnboardingTask.onboarding_id == onboarding_id,
                    OnboardingTask.is_completed == True
                )).count()
            
            if completed_tasks == 0:
                return 0.0
            
            # Calculate weighted completion percentage
            task_weights = {
                "DOCUMENT_UPLOAD": 10,
                "TRAINING": 15,
                "REVIEW": 20,
                "APPROVAL": 25,
                "BACKGROUND_CHECK": 10,
                "MEDICAL_CHECK": 15,
                "ASSET_RETURN": 15,
                "SYSTEM_ACCESS": 5
            }
            
            total_weight = 0
            completed_weight = 0
            
            for task in completed_tasks:
                task_weight = task_weights.get(task.task_type, 0)
                total_weight += task_weight
                completed_weight += task_weight
            
            return (completed_weight / total_weight * 100) if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating completion percentage: {str(e)}")
            return 0.0
    
    def _get_last_used_date(
        self,
        template_id: int,
        db: Session
    ) -> Optional[datetime]:
        """Get last used date for template"""
        try:
            from ..models.onboarding import OnboardingTemplate
            
            template = db.query(OnboardingTemplate).filter(
                OnboardingTemplate.id == template_id
            ).first()
            
            if template:
                return template.last_used
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error getting last used date: {str(e)}")
            return None


# Create service instance
onboarding_service = OnboardingService()
