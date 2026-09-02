"""
Custom Attributes API
REST API endpoints for dynamic custom fields management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..services.custom_attributes_service import custom_attributes_service
from ..schemas.custom_attributes import (
    CustomAttributeCreate, CustomAttributeUpdate, CustomAttributeResponse, CustomAttributeValueCreate,
    CustomAttributeValueResponse, AttributeTemplateCreate, AttributeTemplateResponse,
    BulkAttributeCreate, BulkAttributeResponse, AttributeSearchResponse,
    AttributeValidationRequest, AttributeValidationResponse, FileUploadResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-attributes", tags=["Custom Attributes"])


@router.get("/", response_model=dict)
async def get_attributes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for name or code"),
    category: Optional[str] = Query(None, description="Filter by category"),
    attribute_type: Optional[str] = Query(None, description="Filter by attribute type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get custom attributes with filtering and pagination
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term
        category: Filter by category
        attribute_type: Filter by attribute type
        is_active: Filter by active status
        db: Database session
        
    Returns:
        Paginated list of attributes
    """
    try:
        result = await custom_attributes_service.get_attributes(
            db, skip, limit, search, category, attribute_type, is_active
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to get attributes")
            )
    except Exception as e:
        logger.error(f"Error in get_attributes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/templates", response_model=dict)
async def get_attribute_templates(
    db: Session = Depends(get_db)
):
    """
    Get attribute templates
    
    Args:
        db: Database session
        
    Returns:
        List of attribute templates
    """
    try:
        from ..models.custom_attributes import AttributeTemplate
        
        templates = db.query(AttributeTemplate).filter(
            AttributeTemplate.is_active == True
        ).order_by(AttributeTemplate.template_name).all()
        
        result_templates = []
        for template in templates:
            template_data = {
                "id": template.id,
                "template_name": template.template_name,
                "template_code": template.template_code,
                "description": template.description,
                "attributes": template.attributes,
                "category": template.category,
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
        logger.error(f"Error in get_attribute_templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/types", response_model=dict)
async def get_attribute_types():
    """
    Get available attribute types
    
    Returns:
        List of attribute types
    """
    return {
        "success": True,
        "data": [
            {"value": "TEXT", "label": "Text"},
            {"value": "NUMBER", "label": "Number"},
            {"value": "DATE", "label": "Date"},
            {"value": "BOOLEAN", "label": "Boolean"},
            {"value": "SELECT", "label": "Select"},
            {"value": "MULTI_SELECT", "label": "Multi-Select"},
            {"value": "FILE", "label": "File"},
            {"value": "EMAIL", "label": "Email"},
            {"value": "PHONE", "label": "Phone"},
            {"value": "URL", "label": "URL"}
        ]
    }


@router.get("/categories", response_model=dict)
async def get_attribute_categories():
    """
    Get available attribute categories
    
    Returns:
        List of attribute categories
    """
    return {
        "success": True,
        "data": [
            {"value": "PERSONAL", "label": "Personal Information"},
            {"value": "PROFESSIONAL", "label": "Professional"},
            {"value": "MEDICAL", "label": "Medical"},
            {"value": "EMERGENCY", "label": "Emergency Contact"},
            {"value": "SYSTEM", "label": "System Information"},
            {"value": "CUSTOM", "label": "Custom Fields"}
        ]
    }
@router.get("/{attribute_id}", response_model=dict)
async def get_attribute_by_id(
    attribute_id: int,
    db: Session = Depends(get_db)
):
    """
    Get attribute by ID
    
    Args:
        attribute_id: Attribute ID
        db: Database session
        
    Returns:
        Attribute details
    """
    try:
        result = await custom_attributes_service.get_attribute_by_id(attribute_id, db)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Attribute not found")
            )
    except Exception as e:
        logger.error(f"Error in get_attribute_by_id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("", response_model=dict)
async def create_attribute(
    attribute: CustomAttributeCreate,
    db: Session = Depends(get_db)
):
    """
    Create new custom attribute
    
    Args:
        attribute: Attribute creation data
        db: Database session
        
    Returns:
        Created attribute details
    """
    try:
        result = await custom_attributes_service.create_attribute(
            attribute.dict(), db, created_by=1  # TODO: Get actual user ID
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Attribute created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create attribute")
            )
    except Exception as e:
        logger.error(f"Error in create_attribute: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{attribute_id}", response_model=dict)
async def update_attribute(
    attribute_id: int,
    attribute: CustomAttributeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update existing attribute
    
    Args:
        attribute_id: Attribute ID
        attribute: Attribute update data
        db: Database session
        
    Returns:
        Updated attribute details
    """
    try:
        result = await custom_attributes_service.update_attribute(
            attribute_id, attribute.dict(exclude_unset=True), db, updated_by=1
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": "Attribute updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update attribute")
            )
    except Exception as e:
        logger.error(f"Error in update_attribute: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{attribute_id}", response_model=dict)
async def delete_attribute(
    attribute_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete attribute (soft delete)
    
    Args:
        attribute_id: Attribute ID
        db: Database session
        
    Returns:
        Deletion result
    """
    try:
        result = await custom_attributes_service.delete_attribute(attribute_id, db)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to delete attribute")
            )
    except Exception as e:
        logger.error(f"Error in delete_attribute: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/personnel/{personnel_id}/attributes", response_model=dict)
async def get_personnel_attributes(
    personnel_id: int,
    attribute_ids: Optional[List[int]] = Query(None, description="Filter by attribute IDs"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    Get personnel's custom attribute values
    
    Args:
        personnel_id: Personnel ID
        attribute_ids: Filter by attribute IDs
        category: Filter by category
        db: Database session
        
    Returns:
        List of attribute values
    """
    try:
        result = await custom_attributes_service.get_personnel_attributes(
            personnel_id, db, attribute_ids, category
        )
        
        return {
            "success": True,
            "data": result["data"]
        }
        
    except Exception as e:
        logger.error(f"Error in get_personnel_attributes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/personnel/{personnel_id}/attributes", response_model=dict)
async def set_personnel_attribute(
    personnel_id: int,
    attribute_value: CustomAttributeValueCreate,
    db: Session = Depends(get_db)
):
    """
    Set personnel attribute value
    
    Args:
        personnel_id: Personnel ID
        attribute_value: Attribute value data
        db: Database session
        
    Returns:
        Created/updated attribute value details
    """
    try:
        result = await custom_attributes_service.set_personnel_attribute(
            personnel_id, attribute_value.attribute_id, attribute_value.dict(), db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to set attribute value")
            )
    except Exception as e:
        logger.error(f"Error in set_personnel_attribute: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/personnel/{personnel_id}/attributes/file", response_model=dict)
async def upload_personnel_attribute_file(
    personnel_id: int,
    attribute_id: int,
    file: UploadFile = File(..., description="Attribute value file"),
    db: Session = Depends(get_db)
):
    """
    Upload file for personnel attribute
    
    Args:
        personnel_id: Personnel ID
        attribute_id: Attribute ID
        file: File to upload
        db: Database session
        
    Returns:
        File upload result
    """
    try:
        from ..models.custom_attributes import CustomAttributeValue
        import os
        import uuid
        
        # Save file
        file_path = f"/media/custom-attributes/{personnel_id}/{attribute_id}/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create attribute value record
        attribute_value = CustomAttributeValue(
            personnel_id=personnel_id,
            attribute_id=attribute_id,
            file_path=file_path,
            file_name=file.filename,
            file_size=len(content),
            mime_type=file.content_type,
            created_by=1,  # TODO: Get actual user ID
            is_valid=True
        )
        
        db.add(attribute_value)
        db.commit()
        db.refresh(attribute_value)
        
        return {
            "success": True,
            "data": {
                "id": attribute_value.id,
                "file_path": file_path,
                "file_size": attribute_value.file_size
            },
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in upload_personnel_attribute_file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/templates", response_model=dict)
async def create_attribute_template(
    template: AttributeTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create attribute template
    
    Args:
        template: Template creation data
        db: Database session
        
    Returns:
        Created template details
    """
    try:
        from ..models.custom_attributes import AttributeTemplate
        
        attribute_template = AttributeTemplate(
            template_name=template.template_name,
            template_code=template.template_code,
            description=template.description,
            attributes=template.attributes,
            category=template.category,
            is_system_template=template.is_system_template,
            created_by=1,  # TODO: Get actual user ID
        )
        
        db.add(attribute_template)
        db.commit()
        db.refresh(attribute_template)
        
        return {
            "success": True,
            "data": {
                "id": attribute_template.id,
                "template_name": attribute_template.template_name
            },
            "message": "Template created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in create_attribute_template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


