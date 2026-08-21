"""
Personnel QR Code Generation API Endpoints

This module provides REST API endpoints for generating and managing personnel QR codes,
including badge QR codes, access control QR codes, and verification endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..services.qr_service import qr_service

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["qr-codes"])


@router.post("/generate")
async def generate_qr_code(
    personnel_id: int,
    qr_type: str = "BADGE",
    size: str = "MEDIUM",
    include_logo: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate QR code for personnel"""
    try:
        # Check if user has permission to generate QR codes
        if not await _check_permission(current_user.personnel_id, "personnel.read", db):
            raise HTTPException(status_code=403, detail="Insufficient permissions to generate QR codes")
        
        result = await qr_service.generate_personnel_qr_code(
            personnel_id, qr_type, size, include_logo, db
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QR code: {str(e)}")


@router.post("/bulk-generate")
async def bulk_generate_qr_codes(
    personnel_ids: List[int],
    qr_type: str = "BADGE",
    size: str = "MEDIUM",
    include_logo: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate QR codes for multiple personnel"""
    try:
        # Check if user has permission to generate QR codes
        if not await _check_permission(current_user.personnel_id, "personnel.read", db):
            raise HTTPException(status_code=403, detail="Insufficient permissions to generate QR codes")
        
        result = await qr_service.generate_bulk_qr_codes(
            personnel_ids, qr_type, size, include_logo, db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk generate QR codes: {str(e)}")


@router.post("/validate")
async def validate_qr_code(
    qr_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate QR code data"""
    try:
        # No special permission required for validation
        result = await qr_service.validate_qr_code(qr_data, db)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate QR code: {str(e)}")


@router.get("/types")
async def get_qr_code_types(
    current_user: User = Depends(get_current_user)
):
    """Get available QR code types"""
    try:
        return {"success": True, "data": qr_service.qr_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR code types: {str(e)}")


@router.get("/sizes")
async def get_qr_code_sizes(
    current_user: User = Depends(get_current_user)
):
    """Get available QR code sizes"""
    try:
        return {"success": True, "data": qr_service.sizes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR code sizes: {str(e)}")


@router.get("/personnel/{personnel_id}/qr-codes")
async def get_personnel_qr_codes(
    personnel_id: int,
    qr_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get QR codes for personnel"""
    try:
        # Check if user has permission to view personnel QR codes
        if not await _check_permission(current_user.personnel_id, "personnel.read", db):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view personnel QR codes")
        
        # This would typically query a QR code tracking table
        # For now, return placeholder data
        return {"success": True, "data": {"qr_codes": [], "personnel_id": personnel_id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personnel QR codes: {str(e)}")


@router.get("/usage-statistics")
async def get_qr_code_usage_statistics(
    personnel_id: Optional[int] = Query(None),
    qr_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get QR code usage statistics"""
    try:
        # Check if user has permission to view statistics
        if not await _check_permission(current_user.personnel_id, "reports.read", db):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view usage statistics")
        
        stats = await qr_service.get_qr_code_usage_statistics(personnel_id, qr_type, db)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage statistics: {str(e)}")


@router.get("/download/{personnel_id}")
async def download_qr_code(
    personnel_id: int,
    qr_type: str = "BADGE",
    size: str = "MEDIUM",
    include_logo: bool = True,
    format: str = "png",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download QR code as image file"""
    try:
        # Check if user has permission to generate QR codes
        if not await _check_permission(current_user.personnel_id, "personnel.read", db):
            raise HTTPException(status_code=403, detail="Insufficient permissions to download QR codes")
        
        # Generate QR code
        result = await qr_service.generate_personnel_qr_code(
            personnel_id, qr_type, size, include_logo, db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to generate QR code")
        
        qr_data = result["qr_code"]
        
        # Return base64 image for download
        return JSONResponse(
            content={
                "success": True,
                "qr_code": qr_data,
                "filename": f"qr_{personnel_id}_{qr_type.lower()}.{format}",
                "content_type": f"image/{format}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download QR code: {str(e)}")


@router.post("/batch-download")
async def batch_download_qr_codes(
    personnel_ids: List[int],
    qr_type: str = "BADGE",
    size: str = "MEDIUM",
    include_logo: bool = True,
    format: str = "png",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download multiple QR codes as a zip file"""
    try:
        # Check if user has permission to generate QR codes
        if not await _check_permission(current_user.personnel_id, "personnel.read", db):
            raise HTTPException(status_code=403, detail="Insufficient permissions to download QR codes")
        
        # Generate QR codes
        result = await qr_service.generate_bulk_qr_codes(
            personnel_ids, qr_type, size, include_logo, db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to generate QR codes")
        
        # Return QR codes for batch download
        return {
            "success": True,
            "data": {
                "qr_codes": result["qr_codes"],
                "filename": f"batch_qr_codes_{qr_type.lower()}.zip",
                "total_files": len(result["qr_codes"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch download QR codes: {str(e)}")


@router.get("/templates")
async def get_qr_templates(
    current_user: User = Depends(get_current_user)
):
    """Get QR code templates and settings"""
    try:
        templates = {
            "badge": {
                "name": "Personnel Badge",
                "qr_type": "BADGE",
                "description": "Standard personnel identification badge with photo and basic info",
                "recommended_size": "MEDIUM",
                "include_logo": True,
                "expiry_days": 365
            },
            "access": {
                "name": "Access Control",
                "qr_type": "ACCESS",
                "description": "Access control QR with permissions and role information",
                "recommended_size": "SMALL",
                "include_logo": True,
                "expiry_days": 180
            },
            "emergency": {
                "name": "Emergency Contact",
                "qr_type": "EMERGENCY",
                "description": "Emergency contact information with medical details",
                "recommended_size": "LARGE",
                "include_logo": False,
                "expiry_days": None  # Never expires
            },
            "training": {
                "name": "Training Verification",
                "qr_type": "TRAINING",
                "description": "Training record and certification verification",
                "recommended_size": "MEDIUM",
                "include_logo": True,
                "expiry_days": 90
            }
        }
        
        return {"success": True, "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR templates: {str(e)}")


@router.post("/verify-scan")
async def verify_qr_scan(
    qr_data: Dict[str, Any],
    location: Optional[str] = None,
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify QR code scan and log the scan"""
    try:
        # Validate QR code
        validation_result = await qr_service.validate_qr_code(qr_data, db)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "validation": validation_result,
                "scan_logged": False
            }
        
        # Log the scan (in production, this would go to a scan tracking table)
        scan_log = {
            "scan_id": f"scan_{datetime.now().timestamp()}",
            "personnel_id": validation_result["personnel"]["id"],
            "qr_type": validation_result["qr_type"],
            "location": location,
            "device_id": device_id,
            "scanned_by": current_user.username,
            "scan_timestamp": datetime.now().isoformat(),
            "validation_result": validation_result
        }
        
        return {
            "success": True,
            "validation": validation_result,
            "scan_logged": True,
            "scan_log": scan_log
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify QR scan: {str(e)}")


@router.get("/personnel/{personnel_id}/emergency-qr")
async def get_emergency_qr_code(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emergency QR code for personnel (never expires)"""
    try:
        # Emergency QR codes can be accessed by anyone with personnel read permission
        if not await _check_permission(current_user.personnel_id, "personnel.read", db):
            raise HTTPException(status_code=403, detail="Insufficient permissions to access emergency QR codes")
        
        result = await qr_service.generate_personnel_qr_code(
            personnel_id, "EMERGENCY", "MEDIUM", True, db
        )
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate emergency QR code: {str(e)}")


@router.get("/templates")
async def get_qr_code_templates(
    current_user: User = Depends(get_current_user)
):
    """Get QR code templates and settings"""
    try:
        templates = {
            "badge": {
                "name": "Personnel Badge",
                "description": "Standard personnel identification badge",
                "qr_type": "BADGE",
                "recommended_size": "MEDIUM",
                "include_logo": True,
                "expiry_days": 365
            },
            "access": {
                "name": "Access Control",
                "description": "Access control verification QR code",
                "qr_type": "ACCESS",
                "recommended_size": "SMALL",
                "include_logo": False,
                "expiry_days": 30
            },
            "location": {
                "name": "Location Check",
                "description": "Location check-in/out QR code",
                "qr_type": "LOCATION",
                "recommended_size": "SMALL",
                "include_logo": False,
                "expiry_days": 7
            },
            "emergency": {
                "name": "Emergency Info",
                "description": "Emergency contact information QR code",
                "qr_type": "EMERGENCY",
                "recommended_size": "MEDIUM",
                "include_logo": True,
                "expiry_days": None  # Never expires
            },
            "training": {
                "name": "Training Verification",
                "description": "Training record verification QR code",
                "qr_type": "TRAINING",
                "recommended_size": "MEDIUM",
                "include_logo": True,
                "expiry_days": 90
            },
            "certification": {
                "name": "Certification Verification",
                "description": "Certification status verification QR code",
                "qr_type": "CERTIFICATION",
                "recommended_size": "MEDIUM",
                "include_logo": True,
                "expiry_days": 180
            }
        }
        
        return {"success": True, "data": templates}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR code templates: {str(e)}")


async def _check_permission(personnel_id: int, permission: str, db: Session) -> bool:
    """Helper function to check user permission"""
    try:
        from ..services.role_permission_service import role_permission_service
        return await role_permission_service.check_permission(personnel_id, permission, db)
    except Exception as e:
        logger.warning(f"Permission check failed for personnel {personnel_id} perm={permission}: {e}")
        return False


# Import datetime for scan logging
from datetime import datetime
