"""
Resignation Management API
REST API endpoints for employee resignation workflow and separation process
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import logging

from ..core.database import get_db
from ..services.resignation_service import resignation_service
from ..schemas.resignation import (
    ResignationCreate, ResignationUpdate, ResignationResponse, ResignationTaskCreate,
    ResignationTaskResponse, ResignationDocumentCreate, ResignationDocumentResponse,
    ResignationTemplateCreate, ResignationTemplateResponse, ResignationStatisticsResponse,
    ResignationSearchResponse, BulkResignationAction, BulkResignationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resignation", tags=["Resignation Management"])


@router.post("", response_model=dict)
async def create_resignation(
    resignation: ResignationCreate,
    db: Session = Depends(get_db)
):
    """
    Create new resignation
    
    Args:
        resignation: Resignation creation data
        db: Database session
        
    Returns:
        Created resignation details
    """
    try:
        result = await resignation_service.create_resignation(
            resignation.dict(), db, created_by=1  # TODO: Get actual user ID
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Resignation created successfully"
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create resignation")
            )
    except Exception as e:
        logger.error(f"Error in create_resignation: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/", response_model=dict)
async def get_resignations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for reason or detailed reason"),
    status: Optional[str] = Query(None, description="Filter by resignation status"),
    resignation_type: Optional[str] = Query(None, description="Filter by resignation type"),
    personnel_id: Optional[int] = Query(None, description="Filter by personnel ID"),
    db: Session = Depends(get_db)
):
    """
    Get resignations with filtering and pagination
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term
        status: Filter by resignation status
        resignation_type: Filter by resignation type
        personnel_id: Filter by personnel ID
        db: Database session
        
    Returns:
        Paginated list of resignations
    """
    try:
        result = await resignation_service.get_resignations(
            db, skip, limit, search, status, resignation_type, personnel_id
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
                detail=result.get("error", "Failed to get resignations")
            )
    except Exception as e:
        logger.error(f"Error in get_resignations: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{resignation_id}", response_model=dict)
async def get_resignation_by_id(
    resignation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get resignation by ID
    
    Args:
        resignation_id: Resignation ID
        db: Database session
        
    Returns:
        Resignation details
    """
    try:
        result = await resignation_service.get_resignation_by_id(resignation_id, db)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Resignation not found")
            )
    except Exception as e:
        logger.error(f"Error in get_resignation_by_id: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{resignation_id}", response_model=dict)
async def update_resignation(
    resignation_id: int,
    resignation: ResignationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update existing resignation
    
    Args:
        resignation_id: Resignation ID
        resignation: Resignation update data
        db: Database session
        
    Returns:
        Updated resignation details
    """
    try:
        result = await resignation_service.update_resignation(
            resignation_id, resignation.dict(exclude_unset=True), db, updated_by=1
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Resignation updated successfully"
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update resignation")
            )
    except Exception as e:
        logger.error(f"Error in update_resignation: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{resignation_id}/approve")
async def approve_resignation(
    resignation_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Approve resignation
    
    Args:
        resignation_id: Resignation ID
        notes: Approval notes
        db: Database session
        
    Returns:
        Approval result
    """
    try:
        result = await resignation_service.approve_resignation(
            resignation_id, approved_by=1, notes=notes, db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to approve resignation"
            )
    except Exception as e:
        logger.error(f"Error in approve_resignation: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{resignation_id}/reject")
async def reject_resignation(
    resignation_id: int,
    rejection_reason: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Reject resignation
    
    Args:
        resignation_id: Resignation ID
        rejection_reason: Rejection reason
        notes: Additional notes
        db: Database session
        
    Returns:
        Rejection result
    """
    try:
        result = await resignation_service.reject_resignation(
            resignation_id, rejection_reason, rejected_by=1, notes=notes, db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Failed to reject resignation"
            )
    except Exception as e:
        logger.error(f"Error in reject_resignation: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{resignation_id}/tasks", response_model=dict)
async def get_resignation_tasks(
    resignation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get resignation tasks
    
    Args:
        resignation_id: Resignation ID
        db: Database session
        
    Returns:
        List of resignation tasks
    """
    try:
        from ..models.resignation import ResignationTask
        
        tasks = db.query(ResignationTask).filter(
            ResignationTask.resignation_id == resignation_id
        ).order_by(ResignationTask.created_at).all()
        
        result_tasks = []
        for task in tasks:
            task_data = {
                "id": task.id,
                "resignation_id": task.resignation_id,
                "task_name": task.task_name,
                "task_type": task.task_type,
                "description": task.description,
                "is_required": task.is_required,
                "is_completed": task.is_completed,
                "completion_date": task.completion_date,
                "completed_by": task.completed_by,
                "completion_notes": task.completion_notes,
                "checklist_items": task.checklist_items,
                "due_date": task.due_date,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
            result_tasks.append(task_data)
        
        return {
            "success": True,
            "data": result_tasks
        }
        
    except Exception as e:
        logger.error(f"Error in get_resignation_tasks: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{resignation_id}/tasks", response_model=dict)
async def create_resignation_task(
    resignation_id: int,
    task: ResignationTaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create resignation task
    
    Args:
        resignation_id: Resignation ID
        task: Task creation data
        db: Database session
        
    Returns:
        Created task details
    """
    try:
        from ..models.resignation import ResignationTask
        
        resignation_task = ResignationTask(
            resignation_id=resignation_id,
            task_name=task.task_name,
            task_type=task.task_type,
            description=task.description,
            is_required=task.is_required,
            checklist_items=task.checklist_items,
            due_date=task.due_date
        )
        
        db.add(resignation_task)
        db.commit()
        db.refresh(resignation_task)
        
        return {
            "success": True,
            "data": {
                "id": resignation_task.id,
                "resignation_id": resignation_task.resignation_id,
                "task_name": resignation_task.task_name
            },
            "message": "Task created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in create_resignation_task: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{resignation_id}/documents", response_model=dict)
async def upload_resignation_document(
    resignation_id: int,
    document_type: str = Query(..., description="Document type"),
    document_name: str = Query(..., description="Document name"),
    description: Optional[str] = Query(None, description="Document description"),
    file: UploadFile = File(..., description="Document file"),
    is_required: Optional[bool] = Query(True, description="Document is required"),
    db: Session = Depends(get_db)
):
    """
    Upload resignation document
    
    Args:
        resignation_id: Resignation ID
        document_type: Document type
        document_name: Document name
        description: Document description
        file: Document file
        is_required: Document is required
        db: Database session
        
    Returns:
        Uploaded document details
    """
    try:
        from ..models.resignation import ResignationDocument
        import os
        
        # Save file (simplified for demo)
        file_path = f"/media/resignations/{resignation_id}/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document record
        document = ResignationDocument(
            resignation_id=resignation_id,
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
                "document_path": document.document_path,
                "file_size": document.file_size
            },
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in upload_resignation_document: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{resignation_id}/documents", response_model=dict)
async def get_resignation_documents(
    resignation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get resignation documents
    
    Args:
        resignation_id: Resignation ID
        db: Database session
        
    Returns:
        List of resignation documents
    """
    try:
        from ..models.resignation import ResignationDocument
        
        documents = db.query(ResignationDocument).filter(
            ResignationDocument.resignation_id == resignation_id
        ).order_by(desc(ResignationDocument.uploaded_at)).all()
        
        result_documents = []
        for doc in documents:
            doc_data = {
                "id": doc.id,
                "resignation_id": doc.resignation_id,
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
        logger.error(f"Error in get_resignation_documents: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/statistics", response_model=dict)
async def get_resignation_statistics(
    db: Session = Depends(get_db)
):
    """
    Get resignation statistics
    
    Args:
        db: Database session
        
    Returns:
        Resignation statistics
    """
    try:
        result = await resignation_service.get_resignation_statistics(db)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to get statistics")
            )
    except Exception as e:
        logger.error(f"Error in get_resignation_statistics: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/bulk-action", response_model=dict)
async def bulk_resignation_action(
    action: BulkResignationAction,
    db: Session = Depends(get_db)
):
    """
    Perform bulk action on multiple resignations
    
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
        
        for resignation_id in action.resignation_ids:
            try:
                if action.action == "APPROVE":
                    result = await resignation_service.approve_resignation(
                        resignation_id, approved_by=1, notes=action.notes, db=db
                    )
                elif action.action == "REJECT":
                    result = await resignation_service.reject_resignation(
                        resignation_id, action.rejection_reason, rejected_by=1, notes=action.notes, db=db
                    )
                elif action.action == "CANCEL":
                    # Implement cancel logic
                    result = {"success": True, "message": "Resignation cancelled"}
                else:
                    result = {"success": False, "error": f"Unknown action: {action.action}"}
                
                if result["success"]:
                    successful_actions += 1
                    action_results.append({
                        "resignation_id": resignation_id,
                        "status": "success",
                        "message": result.get("message", "Action completed")
                    })
                else:
                    failed_actions += 1
                    errors.append({
                        "resignation_id": resignation_id,
                        "error": result.get("error", "Action failed")
                    })
                    
            except Exception as e:
                failed_actions += 1
                errors.append({
                    "resignation_id": resignation_id,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_resignations": len(action.resignation_ids),
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "action_results": action_results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk_resignation_action: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/types", response_model=dict)
async def get_resignation_types():
    """
    Get available resignation types
    
    Returns:
        List of resignation types
    """
    return {
        "success": True,
        "data": [
            {"value": "VOLUNTARY", "label": "Voluntary Resignation"},
            {"value": "INVOLUNTARY", "label": "Involuntary Resignation"},
            {"value": "RETIREMENT", "label": "Retirement"},
            {"value": "TERMINATION", "label": "Termination"},
            {"value": "CONTRACT_END", "label": "Contract End"}
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
            {"value": "EXIT_INTERVIEW", "label": "Exit Interview"},
            {"value": "HANDOVER", "label": "Handover Process"},
            {"value": "FINANCIAL", "label": "Financial Clearance"},
            {"value": "ASSET_RETURN", "label": "Asset Return"},
            {"value": "SYSTEM_ACCESS", "label": "System Access Revocation"}
        ]
    }
