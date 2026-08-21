"""
Biometric Management API for Oil & Gas Personnel Management
Handles biometric enrollment, device management, and access control
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.database import get_db
from ..services.biometric_service import BiometricService
from ..models.personnel import Personnel
from pydantic import BaseModel

router = APIRouter(prefix="/biometric", tags=["biometric"])

# Pydantic models for request/response
class BiometricEnrollment(BaseModel):
    personnel_id: int
    biometric_data: Dict[str, Any]
    device_id: Optional[str] = None

class BiometricRevocation(BaseModel):
    personnel_id: int
    reason: str

class DeviceSync(BaseModel):
    device_id: str
    personnel_id: int

# Build the service PER REQUEST, bound to that request's session.
# A module-level singleton shared one never-closed session across every
# request, so one failing call broke the next unrelated one.
def _svc(db: Session) -> BiometricService:
    return BiometricService(db)

@router.post("/enroll")
async def enroll_biometric(
    enrollment_data: BiometricEnrollment,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enroll personnel in biometric system
    
    Args:
        enrollment_data: Biometric enrollment data
        db: Database session
        
    Returns:
        Enrollment result
    """
    try:
        result = await _svc(db).enroll_personnel_biometric(
            personnel_id=enrollment_data.personnel_id,
            biometric_data=enrollment_data.biometric_data
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll biometric: {str(e)}"
        )

@router.post("/revoke")
async def revoke_biometric_access(
    revocation_data: BiometricRevocation,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Revoke biometric access for personnel
    
    Args:
        revocation_data: Biometric revocation data
        db: Database session
        
    Returns:
        Revocation result
    """
    try:
        result = await _svc(db).revoke_biometric_access(
            personnel_id=revocation_data.personnel_id,
            reason=revocation_data.reason
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke biometric access: {str(e)}"
        )

@router.get("/personnel/{personnel_id}/status")
async def get_biometric_status(
    personnel_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get biometric status for personnel
    
    Args:
        personnel_id: Personnel ID
        db: Database session
        
    Returns:
        Biometric status information
    """
    try:
        result = await _svc(db).get_biometric_status(personnel_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get biometric status: {str(e)}"
        )

@router.get("/analytics")
async def get_biometric_analytics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive biometric analytics
    
    Args:
        db: Database session
        
    Returns:
        Biometric analytics data
    """
    try:
        result = await _svc(db).get_biometric_analytics()
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get biometric analytics: {str(e)}"
        )

@router.post("/sync/zkteco")
async def sync_with_zkteco_device(
    sync_data: DeviceSync,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync biometric data with ZKTeco device
    
    Args:
        sync_data: Device sync data
        db: Database session
        
    Returns:
        Sync result
    """
    try:
        result = await _svc(db).sync_with_zkteco_device(
            device_id=sync_data.device_id,
            personnel_id=sync_data.personnel_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync with ZKTeco device: {str(e)}"
        )

@router.get("/device/{device_id}/status")
async def get_device_biometric_status(
    device_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get biometric status for a specific device
    
    Args:
        device_id: Device ID
        db: Database session
        
    Returns:
        Device biometric status
    """
    try:
        result = await _svc(db).get_device_biometric_status(device_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device biometric status: {str(e)}"
        )

@router.get("/dashboard")
async def get_biometric_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get biometric dashboard data
    
    Args:
        db: Database session
        
    Returns:
        Dashboard data
    """
    try:
        # Get analytics
        analytics = await _svc(db).get_biometric_analytics()
        
        if not analytics["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get biometric analytics"
            )
        
        # Get recent enrollments (inline to avoid FastAPI Query resolution issues)
        from ..models.device import AccessLog, Device
        try:
            recent_logs = db.query(AccessLog).filter(
                AccessLog.event_type == 'BIOMETRIC_ENROLLMENT',
                AccessLog.access_granted == True
            ).order_by(AccessLog.timestamp.desc()).limit(10).all()
            recent_enrollments = [
                {
                    "id": log.id,
                    "personnel_id": log.personnel_id,
                    "personnel_name": log.personnel.full_name if log.personnel else "Unknown",
                    "device_id": log.device_id,
                    "enrolled_at": log.timestamp.isoformat(),
                    "biometric_type": log.biometric_data.get('type', 'Unknown') if log.biometric_data else 'Unknown'
                }
                for log in recent_logs
            ]
        except Exception:
            db.rollback()
            recent_enrollments = []

        # Get device status summary (inline)
        try:
            total_devices = db.query(Device).count()
            online_devices = db.query(Device).filter(Device.status == 'online').count()
            offline_devices = db.query(Device).filter(Device.status == 'offline').count()
            device_status_summary = {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "offline_devices": offline_devices,
                "online_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0,
            }
        except Exception:
            db.rollback()
            device_status_summary = {}
        
        dashboard_data = {
            "overview": analytics["overview"],
            "compliance_impact": analytics["compliance_impact"],
            "recent_enrollments": recent_enrollments,
            "device_status": device_status_summary,
            "trends": analytics["trends"]
        }
        
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get biometric dashboard: {str(e)}"
        )

@router.get("/enrollments/recent")
async def get_recent_enrollments(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent biometric enrollments
    
    Args:
        limit: Maximum number of enrollments to return
        db: Database session
        
    Returns:
        Recent enrollments
    """
    try:
        from ..models.device import AccessLog
        
        recent_logs = db.query(AccessLog).filter(
            AccessLog.event_type == 'BIOMETRIC_ENROLLMENT',
            AccessLog.access_granted == True
        ).order_by(AccessLog.timestamp.desc()).limit(limit).all()
        
        enrollments = []
        for log in recent_logs:
            enrollments.append({
                "id": log.id,
                "personnel_id": log.personnel_id,
                "personnel_name": log.personnel.full_name if log.personnel else "Unknown",
                "device_id": log.device_id,
                "enrolled_at": log.timestamp.isoformat(),
                "biometric_type": log.biometric_data.get('type', 'Unknown') if log.biometric_data else 'Unknown'
            })
        
        return enrollments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent enrollments: {str(e)}"
        )

@router.get("/devices/summary")
async def get_device_status_summary(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get device status summary
    
    Args:
        db: Database session
        
    Returns:
        Device status summary
    """
    try:
        from ..models.device import Device
        
        total_devices = db.query(Device).count()
        online_devices = db.query(Device).filter(Device.status == 'online').count()
        offline_devices = db.query(Device).filter(Device.status == 'offline').count()
        maintenance_devices = db.query(Device).filter(Device.status == 'maintenance').count()
        error_devices = db.query(Device).filter(Device.status == 'error').count()
        
        # Get device type distribution
        from sqlalchemy import func
        device_types = db.query(
            Device.device_type,
            func.count(Device.id).label('count')
        ).group_by(Device.device_type).all()
        
        type_distribution = {
            device_type: count for device_type, count in device_types
        }
        
        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "maintenance_devices": maintenance_devices,
            "error_devices": error_devices,
            "online_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0,
            "type_distribution": type_distribution
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device status summary: {str(e)}"
        )

@router.get("/compliance/impact")
async def get_compliance_impact(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get biometric compliance impact analysis
    
    Args:
        db: Database session
        
    Returns:
        Compliance impact data
    """
    try:
        # Get compliance scores for enrolled vs not enrolled personnel
        enrolled_personnel = db.query(Personnel).filter(Personnel.biometric_enrolled == True).all()
        not_enrolled_personnel = db.query(Personnel).filter(Personnel.biometric_enrolled == False).all()
        
        enrolled_scores = [p.compliance_score for p in enrolled_personnel]
        not_enrolled_scores = [p.compliance_score for p in not_enrolled_personnel]
        
        avg_enrolled_score = sum(enrolled_scores) / len(enrolled_scores) if enrolled_scores else 0
        avg_not_enrolled_score = sum(not_enrolled_scores) / len(not_enrolled_scores) if not_enrolled_scores else 0
        
        # Get compliance distribution
        high_compliance_enrolled = sum(1 for score in enrolled_scores if score >= 90)
        high_compliance_not_enrolled = sum(1 for score in not_enrolled_scores if score >= 90)
        
        return {
            "enrolled_personnel": len(enrolled_personnel),
            "not_enrolled_personnel": len(not_enrolled_personnel),
            "average_scores": {
                "enrolled": round(avg_enrolled_score, 1),
                "not_enrolled": round(avg_not_enrolled_score, 1)
            },
            "compliance_difference": round(avg_enrolled_score - avg_not_enrolled_score, 1),
            "high_compliance_percentage": {
                "enrolled": (high_compliance_enrolled / len(enrolled_scores) * 100) if enrolled_scores else 0,
                "not_enrolled": (high_compliance_not_enrolled / len(not_enrolled_scores) * 100) if not_enrolled_scores else 0
            },
            "impact_analysis": {
                "biometric_enrollment_improves_compliance": avg_enrolled_score > avg_not_enrolled_score,
                "improvement_percentage": round(((avg_enrolled_score - avg_not_enrolled_score) / avg_not_enrolled_score * 100) if avg_not_enrolled_score > 0 else 0, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance impact: {str(e)}"
        )
