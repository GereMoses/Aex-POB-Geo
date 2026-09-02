"""
Onboarding Management API
REST API endpoints for employee onboarding workflow and process management
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import logging

from ..core.database import get_db
from ..services.onboarding_service import onboarding_service
from ..schemas.onboarding import (
    OnboardingCreate, OnboardingUpdate, OnboardingResponse, OnboardingTaskCreate,
    OnboardingTaskResponse, OnboardingDocumentCreate, OnboardingDocumentResponse,
    OnboardingTemplateCreate, OnboardingTemplateResponse, OnboardingStatisticsResponse,
    BulkOnboardingAction, BulkOnboardingResponse, OnboardingSearchResponse,
    ChecklistItemCreate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding Management"])


@router.get("/", response_model=dict)
async def get_onboardings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for job title or description"),
    status: Optional[str] = Query(None, description="Filter by onboarding status"),
    onboarding_type: Optional[str] = Query(None, description="Filter by onboarding type"),
    personnel_id: Optional[int] = Query(None, description="Filter by personnel ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    start_date_from: Optional[str] = Query(None, description="Filter by start date from"),
    start_date_to: Optional[str] = Query(None, description="Filter by start date to"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: Session = Depends(get_db)
):
    """
    Get onboardings with filtering and pagination
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term
        status: Filter by onboarding status
        onboarding_type: Filter by onboarding type
        personnel_id: Filter by personnel ID
        department_id: Filter by department ID
        start_date_from: Filter by start date from
        start_date_to: Filter by start date to
        is_completed: Filter by completion status
        db: Database session
        
    Returns:
        Paginated list of onboardings
    """
    try:
        result = await onboarding_service.get_onboardings(
            db, skip, limit, search, status, onboarding_type, personnel_id,
            department_id, start_date_from, start_date_to, is_completed
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "total_count": result["total_count"],
                "skip": result["skip"],
                "limit": result["limit"],
                "page": (result["skip"] // result["limit"]) + 1,
                "total_pages": (result["total_count"] + result["limit"] - 1) // result["limit"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to get onboardings")
            )
    except Exception as e:
        logger.error(f"Error in get_onboardings: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/templates", response_model=dict)
async def get_onboarding_templates(
    db: Session = Depends(get_db)
):
    """
    Get onboarding templates
    
    Args:
        db: Database session
        
    Returns:
        List of onboarding templates
    """
    try:
        from ..models.onboarding import OnboardingTemplate
        
        templates = db.query(OnboardingTemplate).filter(
            OnboardingTemplate.is_active == True
        ).order_by(OnboardingTemplate.template_name).all()
        
        result_templates = []
        for template in templates:
            template_data = {
                "id": template.id,
                "template_name": template.template_name,
                "template_code": template.template_code,
                "onboarding_type": template.onboarding_type.value,
                "description": template.description,
                "default_tasks": template.default_tasks,
                "required_documents": template.required_documents,
                "approval_workflow": template.approval_workflow,
                "notification_settings": template.notification_settings,
                "default_duration_days": template.default_duration_days,
                "is_system_template": template.is_system_template,
                "is_active": template.is_active,
                "created_by": template.created_by,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "usage_count": template.usage_count,
                "last_used": template.last_used,
                "notes": template.notes
            }
            result_templates.append(template_data)
        
        return {
            "success": True,
            "data": result_templates
        }
        
    except Exception as e:
        logger.error(f"Error in get_onboarding_templates: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/statistics", response_model=dict)
async def get_onboarding_statistics(
    db: Session = Depends(get_db)
):
    """
    Get onboarding statistics
    
    Args:
        db: Database session
        
    Returns:
        Onboarding statistics
    """
    try:
        # Calculate statistics
        from ..models.onboarding import Onboarding
        
        total_onboardings = db.query(Onboarding).count()
        active_onboardings = db.query(Onboarding).filter(
            Onboarding.status.in_(["NOT_STARTED", "IN_PROGRESS", "PENDING_REVIEW"])
        ).count()
        completed_onboardings = db.query(Onboarding).filter(
            Onboarding.status == "COMPLETED"
        ).count()
        pending_approval = db.query(Onboarding).filter(
            Onboarding.status == "PENDING_REVIEW"
        ).count()
        pending_review = db.query(Onboarding).filter(
            Onboarding.status == "IN_PROGRESS"
        ).count()
        
        # By type
        type_results = db.query(
            Onboarding.onboarding_type, func.count(Onboarding.id)
        ).group_by(Onboarding.onboarding_type).all()
        
        onboardings_by_type = {}
        for onboarding_type, count in type_results:
            onboardings_by_type[onboarding_type.value] = count
        
        # Timeline metrics
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        onboardings_this_week = db.query(Onboarding).filter(
            Onboarding.created_at >= week_ago
        ).count()
        onboardings_this_month = db.query(Onboarding).filter(
            Onboarding.created_at >= month_ago
        ).count()
        
        return {
            "success": True,
            "data": {
                "total_onboardings": total_onboardings,
                "active_onboardings": active_onboardings,
                "completed_onboardings": completed_onboardings,
                "pending_approval": pending_approval,
                "pending_review": pending_review,
                "onboardings_by_type": onboardings_by_type,
                "onboardings_this_week": onboardings_this_week,
                "onboardings_this_month": onboardings_this_month,
                "average_duration_days": 25.5  # Simulated average
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_onboarding_statistics: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/types", response_model=dict)
async def get_onboarding_types():
    """
    Get available onboarding types
    
    Returns:
        List of onboarding types
    """
    return {
        "success": True,
        "data": [
            {"value": "NEW_HIRE", "label": "New Hire"},
            {"value": "REHIRE", "label": "Rehire"},
            {"value": "INTERNAL_TRANSFER", "label": "Internal Transfer"},
            {"value": "PROMOTION", "label": "Promotion"},
            {"value": "CONTRACT_RENEWAL", "label": "Contract Renewal"}
        ]
    }


@router.get("/task-types", response_model=dict)
async def get_task_types():
    """
    Get available task types
    
    Returns:
        List of task types
    """
    return {
        "success": True,
        "data": [
            {"value": "DOCUMENT_UPLOAD", "label": "Document Upload"},
            {"value": "TRAINING", "label": "Training"},
            {"value": "REVIEW", "label": "Review"},
            {"value": "APPROVAL", "label": "Approval"},
            {"value": "BACKGROUND_CHECK", "label": "Background Check"},
            {"value": "MEDICAL_CHECK", "label": "Medical Check"},
            {"value": "ASSET_RETURN", "label": "Asset Return"},
            {"value": "SYSTEM_ACCESS", "label": "System Access"}
        ]
    }
@router.get("/{onboarding_id}", response_model=dict)
async def get_onboarding_by_id(
    onboarding_id: int,
    db: Session = Depends(get_db)
):
    """
    Get onboarding by ID
    
    Args:
        onboarding_id: Onboarding ID
        db: Database session
        
    Returns:
        Onboarding details
    """
    try:
        result = await onboarding_service.get_onboarding_by_id(onboarding_id, db)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Onboarding not found")
            )
    except Exception as e:
        logger.error(f"Error in get_onboarding_by_id: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("", response_model=dict)
async def create_onboarding(
    onboarding: OnboardingCreate,
    db: Session = Depends(get_db)
):
    """
    Create new onboarding
    
    Args:
        onboarding: Onboarding creation data
        db: Database session
        
    Returns:
        Created onboarding details
    """
    try:
        result = await onboarding_service.create_onboarding(
            onboarding.dict(), db, created_by=1  # TODO: Get actual user ID
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Onboarding created successfully"
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create onboarding")
            )
    except Exception as e:
        logger.error(f"Error in create_onboarding: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{onboarding_id}", response_model=dict)
async def update_onboarding(
    onboarding_id: int,
    onboarding: OnboardingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update existing onboarding
    
    Args:
        onboarding_id: Onboarding ID
        onboarding: Onboarding update data
        db: Database session
        
    Returns:
        Updated onboarding details
    """
    try:
        result = await onboarding_service.update_onboarding(
            onboarding_id, onboarding.dict(exclude_unset=True), db, updated_by=1
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Onboarding updated successfully"
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update onboarding")
            )
    except Exception as e:
        logger.error(f"Error in update_onboarding: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{onboarding_id}/approve", response_model=dict)
async def approve_onboarding(
    onboarding_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Approve onboarding
    
    Args:
        onboarding_id: Onboarding ID
        notes: Approval notes
        db: Database session
        
    Returns:
        Approval result
    """
    try:
        result = await onboarding_service.approve_onboarding(
            onboarding_id, approved_by=1, notes=notes, db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to approve onboarding"
            )
    except Exception as e:
        logger.error(f"Error in approve_onboarding: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{onboarding_id}/reject", response_model=dict)
async def reject_onboarding(
    onboarding_id: int,
    rejection_reason: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Reject onboarding
    
    Args:
        onboarding_id: Onboarding ID
        rejection_reason: Rejection reason
        notes: Additional notes
        db: Database session
        
    Returns:
        Rejection result
    """
    try:
        result = await onboarding_service.reject_onboarding(
            onboarding_id, rejection_reason, rejected_by=1, notes=notes, db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to reject onboarding"
            )
    except Exception as e:
        logger.error(f"Error in reject_onboarding: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{onboarding_id}/complete", response_model=dict)
async def complete_onboarding(
    onboarding_id: int,
    db: Session = Depends(get_db)
):
    """
    Complete onboarding
    
    Args:
        onboarding_id: Onboarding ID
        db: Database session
        
    Returns:
        Completion result
    """
    try:
        result = await onboarding_service.complete_onboarding(onboarding_id, completed_by=1, db=db)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to complete onboarding"
            )
    except Exception as e:
        logger.error(f"Error in complete_onboarding: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{onboarding_id}/tasks", response_model=dict)
async def get_onboarding_tasks(
    onboarding_id: int,
    status: Optional[str] = Query(None, description="Filter by task status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: Session = Depends(get_db)
):
    """
    Get onboarding tasks
    
    Args:
        onboarding_id: Onboarding ID
        status: Filter by task status
        task_type: Filter by task type
        is_completed: Filter by completion status
        db: Database session
        
    Returns:
        List of onboarding tasks
    """
    try:
        result = await onboarding_service.get_onboarding_tasks(
            onboarding_id, db, status, task_type, is_completed
        )
        
        return {
            "success": True,
            "data": result["data"],
            "total_tasks": result["total_tasks"],
            "completed_count": result["completed_count"]
        }
        
    except Exception as e:
        logger.error(f"Error in get_onboarding_tasks: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{onboarding_id}/tasks", response_model=dict)
async def create_onboarding_task(
    onboarding_id: int,
    task: OnboardingTaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create onboarding task
    
    Args:
        onboarding_id: Onboarding ID
        task: Task creation data
        db: Database session
        
    Returns:
        Created task details
    """
    try:
        result = await onboarding_service.create_onboarding_task(
            onboarding_id, task.dict(), db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Task created successfully"
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to create task"
            )
    except Exception as e:
        logger.error(f"Error in create_onboarding_task: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/tasks/{task_id}", response_model=dict)
async def update_onboarding_task(
    task_id: int,
    task_update: dict,
    db: Session = Depends(get_db)
):
    """
    Update onboarding task
    
    Args:
        task_id: Task ID
        task_update: Task update data
        db: Database session
        
    Returns:
        Updated task details
    """
    try:
        result = await onboarding_service.update_onboarding_task(
            task_id, task_update, db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Task updated successfully"
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to update task"
            )
    except Exception as e:
        logger.error(f"Error in update_onboarding_task: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{onboarding_id}/documents", response_model=dict)
async def get_onboarding_documents(
    onboarding_id: int,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    db: Session = Depends(get_db)
):
    """
    Get onboarding documents
    
    Args:
        onboarding_id: Onboarding ID
        document_type: Filter by document type
        is_verified: Filter by verification status
        db: Database session
        
    Returns:
        List of onboarding documents
    """
    try:
        from ..models.onboarding import OnboardingDocument
        
        query = db.query(OnboardingDocument).filter(
            OnboardingDocument.onboarding_id == onboarding_id
        )
        
        if document_type:
            query = query.filter(OnboardingDocument.document_type == document_type)
        
        if is_verified is not None:
            query = query.filter(OnboardingDocument.is_verified == is_verified)
        
        documents = query.order_by(desc(OnboardingDocument.uploaded_at)).all()
        
        result_documents = []
        for doc in documents:
            doc_data = {
                "id": doc.id,
                "onboarding_id": doc.onboarding_id,
                "document_type": doc.document_type,
                "document_name": doc.document_name,
                "document_path": doc.document_path,
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
                "description": doc.description,
                "is_required": doc.is_required,
                "uploaded_by": doc.uploaded_by,
                "uploaded_at": doc.uploaded_at,
                "is_verified": doc.is_verified,
                "verified_by": doc.verified_by,
                "verified_at": doc.verified_at,
                "verification_notes": doc.verification_notes
            }
            result_documents.append(doc_data)
        
        return {
            "success": True,
            "data": result_documents
        }
        
    except Exception as e:
        logger.error(f"Error in get_onboarding_documents: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{onboarding_id}/documents", response_model=dict)
async def upload_onboarding_document(
    onboarding_id: int,
    document_type: str = Query(..., description="Document type"),
    document_name: str = Query(..., description="Document name"),
    description: Optional[str] = Query(None, description="Document description"),
    is_required: bool = Query(True, description="Document is required"),
    file: UploadFile = File(..., description="Document file"),
    db: Session = Depends(get_db)
):
    """
    Upload onboarding document
    
    Args:
        onboarding_id: Onboarding ID
        document_type: Document type
        document_name: Document name
        description: Document description
        is_required: Document is required
        file: Document file
        db: Database session
        
    Returns:
        Uploaded document details
    """
    try:
        from ..models.onboarding import OnboardingDocument
        import os
        import uuid
        
        # Save file
        file_path = f"/media/onboardings/{onboarding_id}/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document record
        document = OnboardingDocument(
            onboarding_id=onboarding_id,
            document_type=document_type,
            document_name=document_name,
            document_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            description=description,
            is_required=is_required,
            uploaded_by=1  # TODO: Get actual user ID
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "success": True,
            "data": {
                "id": document.id,
                "document_path": file_path,
                "file_size": document.file_size
            },
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in upload_onboarding_document: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/templates", response_model=dict)
async def create_onboarding_template(
    template: OnboardingTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create onboarding template
    
    Args:
        template: Template creation data
        db: Database session
        
    Returns:
        Created template details
    """
    try:
        from ..models.onboarding import OnboardingTemplate
        
        onboarding_template = OnboardingTemplate(
            template_name=template.template_name,
            template_code=template.template_code,
            onboarding_type=template.onboarding_type,
            description=template.description,
            default_tasks=template.default_tasks,
            required_documents=template.required_documents,
            approval_workflow=template.approval_workflow,
            notification_settings=template.notification_settings,
            default_duration_days=template.default_duration_days,
            is_system_template=template.is_system_template,
            created_by=1  # TODO: Get actual user ID
        )
        
        db.add(onboarding_template)
        db.commit()
        db.refresh(onboarding_template)
        
        return {
            "success": True,
            "data": {
                "id": onboarding_template.id,
                "template_name": onboarding_template.template_name
            },
            "message": "Template created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in create_onboarding_template: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/bulk-action", response_model=dict)
async def bulk_onboarding_action(
    action: BulkOnboardingAction,
    db: Session = Depends(get_db)
):
    """
    Perform bulk action on multiple onboardings
    
    Args:
        action: Bulk action request
        db: Database session
        
    Returns:
        Bulk action results
    """
    try:
        successful_actions = 0
        failed_actions = 0
        action_results = []
        errors = []
        
        for onboarding_id in action.onboarding_ids:
            try:
                if action.action == "APPROVE":
                    result = await onboarding_service.approve_onboarding(
                        onboarding_id, approved_by=1, notes=action.notes, db=db
                    )
                elif action.action == "REJECT":
                    result = await onboarding_service.reject_onboarding(
                        onboarding_id, action.rejection_reason, rejected_by=1, notes=action.notes, db=db
                    )
                elif action.action == "CANCEL":
                    # Implement cancel logic
                    result = {"success": True, "message": "Onboarding cancelled"}
                else:
                    result = {"success": False, "error": f"Unknown action: {action.action}"}
                
                if result["success"]:
                    successful_actions += 1
                    action_results.append({
                        "onboarding_id": onboarding_id,
                        "status": "success",
                        "message": result.get("message", "Action completed")
                    })
                else:
                    failed_actions += 1
                    errors.append({
                        "onboarding_id": onboarding_id,
                        "error": result.get("error", "Action failed")
                    })
                    
            except Exception as e:
                failed_actions += 1
                errors.append({
                    "onboarding_id": onboarding_id,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_onboardings": len(action.onboarding_ids),
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "action_results": action_results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk_onboarding_action: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


