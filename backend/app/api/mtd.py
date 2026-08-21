"""
MTD (Medical, Training, Development) API Endpoints
POB Version 2.0 - HSE Compliance Module
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from pydantic import BaseModel, Field

from ..services.mtd_service import mtd_service
from ..core.database import get_db
from ..core.dependencies import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/api/mtd", tags=["MTD"])


# ===== Pydantic Models =====

class MedicalRecordCreate(BaseModel):
    person_type: int = Field(..., description="0=employee,1=visitor")
    emp_id: Optional[int] = None
    visitor_id: Optional[int] = None
    blood_group: Optional[str] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    disabilities: Optional[str] = None
    fit_status: int = Field(default=0, description="0=fit,1=restricted,2=unfit")
    restrictions: Optional[str] = None
    doctor_name: Optional[str] = None
    last_checkup: Optional[date] = None
    next_due: Optional[date] = None


class CertTypeCreate(BaseModel):
    cert_name: str
    validity_days: int
    is_critical: bool = False
    required_for_dept: List[int] = []
    required_for_position: List[int] = []
    required_for_vendor: List[int] = []
    description: Optional[str] = None


class CertificationCreate(BaseModel):
    person_type: int = Field(..., description="0=employee,1=visitor")
    emp_id: Optional[int] = None
    visitor_id: Optional[int] = None
    cert_type_id: int
    cert_no: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: date


class PPETypeCreate(BaseModel):
    ppe_name: str
    lifespan_days: Optional[int] = None
    requires_calibration: bool = False
    calib_interval_days: Optional[int] = None
    description: Optional[str] = None


class PPEIssueCreate(BaseModel):
    emp_id: int
    ppe_type_id: int
    serial_no: Optional[str] = None
    issue_date: Optional[date] = None
    condition_out: int = Field(default=1, description="0=new,1=good,2=fair")
    last_calib_date: Optional[date] = None


class PPEReturnCreate(BaseModel):
    condition_in: int = Field(..., description="0=new,1=good,2=fair")
    return_date: Optional[date] = None


class InductionTemplateCreate(BaseModel):
    template_name: str
    video_path: Optional[str] = None
    slides_path: Optional[str] = None
    quiz_questions: List[Dict[str, Any]] = []
    passing_score: int = 80
    validity_days: int = 365
    required_for_type: Optional[int] = None
    description: Optional[str] = None


class InductionTakeCreate(BaseModel):
    person_type: int = Field(..., description="0=employee,1=visitor")
    emp_id: Optional[int] = None
    visitor_id: Optional[int] = None
    template_id: int
    score: int
    trainer_emp_id: Optional[int] = None
    quiz_answers: List[Dict[str, Any]] = []


# ===== MEDICAL RECORDS =====

@router.get("/medical/")
async def get_medical_records(
    person_type: Optional[int] = Query(None),
    emp_id: Optional[int] = Query(None),
    visitor_id: Optional[int] = Query(None),
    fit_status: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get medical records with filters"""
    try:
        records = await mtd_service.get_medical_records(
            person_type=person_type,
            emp_id=emp_id,
            visitor_id=visitor_id,
            fit_status=fit_status,
            db=db
        )
        
        # Log audit for medical record access
        for record in records:
            await mtd_service._create_audit_log(
                user_id=current_user.id,
                record_type="medical_record",
                record_id=record["id"],
                action="view",
                details=f"Viewed medical record for {record.get('employee', {}).get('full_name', 'Unknown') if record.get('employee') else record.get('visitor', {}).get('full_name', 'Unknown')}",
                db=db
            )
        
        return {"success": True, "data": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medical")
async def create_medical_record(
    medical_data: MedicalRecordCreate,
    cert_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create or update medical record"""
    try:
        # Handle file upload
        if cert_file:
            cert_data = await cert_file.read()
            medical_data_dict = medical_data.dict()
            medical_data_dict['cert_file'] = cert_data
        else:
            medical_data_dict = medical_data.dict()
        
        result = await mtd_service.create_medical_record(
            medical_data=medical_data_dict,
            db=db,
            current_user=current_user
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/medical/{record_id}/audit/")
async def get_medical_audit_log(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit log for medical record"""
    try:
        from ..models.mtd import MTDAuditLog
        
        audit_logs = db.query(MTDAuditLog).filter(
            MTDAuditLog.record_type == "medical_record",
            MTDAuditLog.record_id == record_id
        ).order_by(MTDAuditLog.access_time.desc()).all()
        
        logs = []
        for log in audit_logs:
            logs.append({
                "access_time": log.access_time.isoformat(),
                "user_id": log.user_id,
                "action": log.action,
                "action_text": log.action_text,
                "details": log.details,
                "ip_address": log.ip_address
            })
        
        return {"success": True, "data": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== CERTIFICATION MANAGEMENT =====

@router.get("/cert-types/")
async def get_certification_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all certification types"""
    try:
        from ..models.mtd import MTDCertType
        
        cert_types = db.query(MTDCertType).all()
        
        result = []
        for cert_type in cert_types:
            result.append({
                "id": cert_type.id,
                "cert_name": cert_type.cert_name,
                "validity_days": cert_type.validity_days,
                "is_critical": cert_type.is_critical,
                "required_for_dept": cert_type.required_for_dept or [],
                "required_for_position": cert_type.required_for_position or [],
                "required_for_vendor": cert_type.required_for_vendor or [],
                "description": cert_type.description
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cert-types")
async def create_certification_type(
    cert_type_data: CertTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create certification type"""
    try:
        result = await mtd_service.create_cert_type(
            cert_type_data=cert_type_data.dict(),
            db=db,
            current_user=current_user
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cert-types/{cert_type_id}")
async def update_certification_type(
    cert_type_id: int,
    cert_type_data: CertTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update certification type"""
    try:
        from ..models.mtd import MTDCertType
        
        cert_type = db.query(MTDCertType).filter(MTDCertType.id == cert_type_id).first()
        if not cert_type:
            raise HTTPException(status_code=404, detail="Certification type not found")
        
        for key, value in cert_type_data.dict().items():
            if hasattr(cert_type, key):
                setattr(cert_type, key, value)
        
        db.commit()
        
        return {"success": True, "message": "Certification type updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cert-types/{cert_type_id}")
async def delete_certification_type(
    cert_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete certification type"""
    try:
        from ..models.mtd import MTDCertType
        
        cert_type = db.query(MTDCertType).filter(MTDCertType.id == cert_type_id).first()
        if not cert_type:
            raise HTTPException(status_code=404, detail="Certification type not found")
        
        db.delete(cert_type)
        db.commit()
        
        return {"success": True, "message": "Certification type deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/certifications/")
async def get_certifications(
    person_type: Optional[int] = Query(None),
    emp_id: Optional[int] = Query(None),
    visitor_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    expiring_days: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get certifications with filters"""
    try:
        certifications = await mtd_service.get_certifications(
            person_type=person_type,
            emp_id=emp_id,
            visitor_id=visitor_id,
            status=status,
            expiring_days=expiring_days,
            db=db
        )
        
        return {"success": True, "data": certifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/certifications")
async def assign_certification(
    cert_data: CertificationCreate,
    cert_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign certification to employee/visitor"""
    try:
        # Handle file upload
        if cert_file:
            cert_data_bytes = await cert_file.read()
            cert_data_dict = cert_data.dict()
            cert_data_dict['cert_file'] = cert_data_bytes
        else:
            cert_data_dict = cert_data.dict()
        
        result = await mtd_service.assign_certification(
            cert_data=cert_data_dict,
            db=db,
            current_user=current_user
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/certifications/{cert_id}")
async def update_certification(
    cert_id: int,
    cert_data: CertificationCreate,
    cert_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update certification"""
    try:
        from ..models.mtd import MTDCertification, MTDCertType
        
        certification = db.query(MTDCertification).filter(MTDCertification.id == cert_id).first()
        if not certification:
            raise HTTPException(status_code=404, detail="Certification not found")
        
        # Update fields
        for key, value in cert_data.dict().items():
            if key not in ['cert_file'] and hasattr(certification, key):
                setattr(certification, key, value)
        
        # Recalculate expiry if issue date changed
        if cert_data.issue_date:
            cert_type = db.query(MTDCertType).filter(MTDCertType.id == certification.cert_type_id).first()
            if cert_type:
                certification.expiry_date = cert_data.issue_date + timedelta(days=cert_type.validity_days)
                
                # Update status
                if certification.expiry_date < date.today():
                    certification.status = 2  # Expired
                elif certification.expiry_date < date.today() + timedelta(days=30):
                    certification.status = 1  # Expiring
                else:
                    certification.status = 0  # Valid
        
        # Handle file upload
        if cert_file:
            cert_data_bytes = await cert_file.read()
            cert_path = await mtd_service._save_uploaded_file(
                cert_data_bytes,
                "certifications",
                f"cert_{certification.person_type}_{certification.emp_id or certification.visitor_id}_{certification.cert_type_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            certification.cert_path = cert_path
        
        certification.verified_by = current_user.id
        certification.verified_time = datetime.utcnow()
        
        db.commit()
        
        return {"success": True, "message": "Certification updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/certifications/{cert_id}")
async def delete_certification(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete certification"""
    try:
        from ..models.mtd import MTDCertification
        
        certification = db.query(MTDCertification).filter(MTDCertification.id == cert_id).first()
        if not certification:
            raise HTTPException(status_code=404, detail="Certification not found")
        
        db.delete(certification)
        db.commit()
        
        return {"success": True, "message": "Certification deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/certifications/matrix/")
async def get_certification_matrix(
    dept_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get certification matrix (employees vs certifications)"""
    try:
        from ..models.mtd import MTDCertType, MTDCertification
        from ..models.personnel import Personnel
        
        # Get personnel
        query = db.query(Personnel)
        if dept_id:
            query = query.filter(Personnel.dept_id == dept_id)
        personnel_list = query.all()
        
        # Get certification types
        cert_types = db.query(MTDCertType).all()
        
        # Build matrix
        matrix = []
        for person in personnel_list:
            row = {
                "personnel_id": person.id,
                "badge_id": person.badge_id,
                "full_name": person.full_name,
                "company": person.company,
                "certifications": {}
            }
            
            # Get person's certifications
            person_certs = db.query(MTDCertification).filter(
                MTDCertification.emp_id == person.id
            ).all()
            
            cert_map = {cert.cert_type_id: cert for cert in person_certs}
            
            for cert_type in cert_types:
                cert = cert_map.get(cert_type.id)
                row["certifications"][cert_type.cert_name] = {
                    "has_cert": cert is not None,
                    "status": cert.status if cert else None,
                    "status_text": cert.status_text if cert else None,
                    "expiry_date": cert.expiry_date.isoformat() if cert and cert.expiry_date else None,
                    "days_to_expiry": cert.days_to_expiry if cert else None,
                    "is_critical": cert_type.is_critical
                }
            
            matrix.append(row)
        
        return {
            "success": True,
            "data": {
                "personnel_count": len(personnel_list),
                "cert_types": [{"id": ct.id, "name": ct.cert_name, "is_critical": ct.is_critical} for ct in cert_types],
                "matrix": matrix
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== PPE MANAGEMENT =====

@router.get("/ppe-types/")
async def get_ppe_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all PPE types"""
    try:
        from ..models.mtd import MTDPPEType
        
        ppe_types = db.query(MTDPPEType).all()
        
        result = []
        for ppe_type in ppe_types:
            result.append({
                "id": ppe_type.id,
                "ppe_name": ppe_type.ppe_name,
                "lifespan_days": ppe_type.lifespan_days,
                "requires_calibration": ppe_type.requires_calibration,
                "calib_interval_days": ppe_type.calib_interval_days,
                "description": ppe_type.description
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ppe-types")
async def create_ppe_type(
    ppe_data: PPETypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create PPE type"""
    try:
        result = await mtd_service.create_ppe_type(
            ppe_data=ppe_data.dict(),
            db=db,
            current_user=current_user
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ppe-issues/")
async def get_ppe_issues(
    emp_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get PPE issues with filters"""
    try:
        from ..models.mtd import MTDPPEIssue, MTDPPEType

        query = db.query(MTDPPEIssue).join(MTDPPEType)
        
        if emp_id:
            query = query.filter(MTDPPEIssue.emp_id == emp_id)
        if status is not None:
            query = query.filter(MTDPPEIssue.status == status)
        
        issues = query.order_by(desc(MTDPPEIssue.issue_date)).all()
        
        result = []
        for issue in issues:
            result.append({
                "id": issue.id,
                "emp_id": issue.emp_id,
                "ppe_type": {
                    "id": issue.ppe_type.id,
                    "ppe_name": issue.ppe_type.ppe_name
                },
                "serial_no": issue.serial_no,
                "issue_date": issue.issue_date.isoformat(),
                "due_return_date": issue.due_return_date.isoformat() if issue.due_return_date else None,
                "return_date": issue.return_date.isoformat() if issue.return_date else None,
                "condition_out": issue.condition_out,
                "condition_text": issue.condition_text,
                "condition_in": issue.condition_in,
                "last_calib_date": issue.last_calib_date.isoformat() if issue.last_calib_date else None,
                "next_calib_date": issue.next_calib_date.isoformat() if issue.next_calib_date else None,
                "status": issue.status,
                "status_text": issue.status_text,
                "is_overdue": issue.is_overdue,
                "calibration_due": issue.calibration_due,
                "notes": issue.notes
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ppe-issues")
async def issue_ppe(
    ppe_data: PPEIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Issue PPE to employee"""
    try:
        result = await mtd_service.issue_ppe(
            issue_data=ppe_data.dict(),
            db=db,
            current_user=current_user
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ppe-issues/{issue_id}/return")
async def return_ppe(
    issue_id: int,
    return_data: PPEReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Return issued PPE"""
    try:
        result = await mtd_service.return_ppe(
            ppe_issue_id=issue_id,
            return_data=return_data.dict(),
            db=db,
            current_user=current_user
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ppe-issues/expiring/")
async def get_ppe_calibration_due(
    days: int = Query(default=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get PPE items requiring calibration"""
    try:
        from ..models.mtd import MTDPPEIssue, MTDPPEType

        calib_threshold = date.today() + timedelta(days=days)

        ppe_items = db.query(MTDPPEIssue).join(MTDPPEType).filter(
            and_(
                MTDPPEIssue.next_calib_date <= calib_threshold,
                MTDPPEIssue.next_calib_date >= date.today(),
                MTDPPEIssue.status == 0  # Still issued
            )
        ).all()
        
        result = []
        for item in ppe_items:
            result.append({
                "id": item.id,
                "emp_id": item.emp_id,
                "ppe_name": item.ppe_type.ppe_name,
                "serial_no": item.serial_no,
                "next_calib_date": item.next_calib_date.isoformat(),
                "days_to_calib": (item.next_calib_date - date.today()).days,
                "person_name": item.employee.full_name if item.employee else "Unknown"
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== INDUCTION MANAGEMENT =====

@router.get("/induction-templates/")
async def get_induction_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all induction templates"""
    try:
        from ..models.mtd import MTDInductionTemplate
        
        templates = db.query(MTDInductionTemplate).filter(MTDInductionTemplate.is_active == True).all()
        
        result = []
        for template in templates:
            result.append({
                "id": template.id,
                "template_name": template.template_name,
                "video_path": template.video_path,
                "slides_path": template.slides_path,
                "quiz_questions": template.quiz_questions or [],
                "passing_score": template.passing_score,
                "validity_days": template.validity_days,
                "required_for_type": template.required_for_type,
                "description": template.description
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/induction-templates")
async def create_induction_template(
    template_data: InductionTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create induction template"""
    try:
        result = await mtd_service.create_induction_template(
            template_data=template_data.dict(),
            db=db,
            current_user=current_user
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/induction-records/")
async def get_induction_records(
    person_type: Optional[int] = Query(None),
    emp_id: Optional[int] = Query(None),
    visitor_id: Optional[int] = Query(None),
    valid: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get induction records with filters"""
    try:
        from ..models.mtd import MTDInductionRecord, MTDInductionTemplate

        query = db.query(MTDInductionRecord).join(MTDInductionTemplate)
        
        if person_type is not None:
            query = query.filter(MTDInductionRecord.person_type == person_type)
        if emp_id:
            query = query.filter(MTDInductionRecord.emp_id == emp_id)
        if visitor_id:
            query = query.filter(MTDInductionRecord.visitor_id == visitor_id)
        
        records = query.order_by(desc(MTDInductionRecord.taken_date)).all()
        
        result = []
        for record in records:
            if valid is None or record.is_valid == valid:
                result.append({
                    "id": record.id,
                    "person_type": record.person_type,
                    "emp_id": record.emp_id,
                    "visitor_id": record.visitor_id,
                    "template": {
                        "id": record.template.id,
                        "template_name": record.template.template_name
                    },
                    "taken_date": record.taken_date.isoformat(),
                    "score": record.score,
                    "passed": record.passed,
                    "valid_until": record.valid_until.isoformat() if record.valid_until else None,
                    "days_to_expiry": record.days_to_expiry,
                    "is_valid": record.is_valid,
                    "signed_doc": record.signed_doc,
                    "trainer_emp_id": record.trainer_emp_id,
                    "completion_time": record.completion_time.isoformat() if record.completion_time else None
                })
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/induction-records/take")
async def take_induction(
    induction_data: InductionTakeCreate,
    signed_doc: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Record induction completion"""
    try:
        # Handle file upload
        if signed_doc:
            doc_data = await signed_doc.read()
            induction_dict = induction_data.dict()
            induction_dict['signed_doc'] = doc_data
        else:
            induction_dict = induction_data.dict()
        
        result = await mtd_service.take_induction(
            induction_data=induction_dict,
            db=db,
            current_user=current_user
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== DASHBOARD AND ALERTS =====

@router.get("/dashboard/expiring/")
async def get_expiring_items(
    days: int = Query(default=30),
    types: Optional[str] = Query(None, description="Comma-separated: medical,cert,ppe,induction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get items expiring within specified days"""
    try:
        type_list = None
        if types:
            type_list = [t.strip() for t in types.split(',')]
        
        result = await mtd_service.get_expiring_items(
            days=days,
            types=type_list,
            db=db
        )
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard/notify")
async def notify_expiring_items(
    record_ids: List[int],
    background_tasks: BackgroundTasks,
    channel: str = Query(..., description="email|sms"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send notifications for expiring items"""
    try:
        # This would integrate with email/SMS service
        # For now, just return success
        background_tasks.add_task(
            send_expiry_notifications,
            record_ids=record_ids,
            channel=channel,
            user_id=current_user.id
        )
        
        return {"success": True, "message": f"Notifications queued for {len(record_ids)} items"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/compliance/")
async def get_compliance_dashboard(
    dept_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get compliance dashboard"""
    try:
        compliance_report = await mtd_service.get_compliance_report(
            dept_id=dept_id,
            db=db
        )
        
        return {"success": True, "data": compliance_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== COMPLIANCE ENFORCEMENT =====

@router.get("/compliance/matrix/")
async def get_requirement_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get position vs certification requirements matrix"""
    try:
        from ..models.mtd import MTDCertType
        from ..models.position import Position
        
        cert_types = db.query(MTDCertType).all()
        positions = db.query(Position).all()
        
        matrix = []
        for position in positions:
            row = {
                "position_id": position.id,
                "position_name": position.position_name,
                "requirements": {}
            }
            
            for cert_type in cert_types:
                is_required = (
                    (cert_type.required_for_position and position.id in cert_type.required_for_position) or
                    (cert_type.required_for_dept and position.dept_id in cert_type.required_for_dept)
                )
                row["requirements"][cert_type.cert_name] = {
                    "required": is_required,
                    "is_critical": cert_type.is_critical
                }
            
            matrix.append(row)
        
        return {
            "success": True,
            "data": {
                "cert_types": [{"id": ct.id, "name": ct.cert_name, "is_critical": ct.is_critical} for ct in cert_types],
                "positions": [{"id": p.id, "name": p.position_name} for p in positions],
                "matrix": matrix
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/non-compliant/")
async def get_non_compliant_personnel(
    record_type: Optional[str] = Query(None, description="medical,cert,ppe,induction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get non-compliant personnel"""
    try:
        compliance_report = await mtd_service.get_compliance_report(db=db)
        
        # Filter by record type if specified
        if record_type:
            filtered_list = []
            for person in compliance_report["non_compliant_list"]:
                filtered_items = [item for item in person["missing_items"] if record_type.lower() in item.lower()]
                if filtered_items:
                    filtered_person = person.copy()
                    filtered_person["missing_items"] = filtered_items
                    filtered_list.append(filtered_person)
            compliance_report["non_compliant_list"] = filtered_list
        
        return {"success": True, "data": compliance_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/enforce")
async def enforce_compliance(
    emp_ids: List[int],
    background_tasks: BackgroundTasks,
    action: str = Query(..., description="suspend|notify"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Enforce compliance actions"""
    try:
        from ..models.personnel import Personnel
        
        results = []
        
        for emp_id in emp_ids:
            employee = db.query(Personnel).filter(Personnel.id == emp_id).first()
            if not employee:
                continue
            
            if action == "suspend":
                employee.status = 2  # Suspended
                db.commit()
                
                # Log compliance action
                from ..models.mtd import MTDComplianceLog
                compliance_log = MTDComplianceLog(
                    emp_id=emp_id,
                    record_type="enforcement",
                    status=2,  # Non-compliant
                    action_taken="Suspended",
                    details="Employee suspended due to compliance enforcement",
                    created_by=current_user.id
                )
                db.add(compliance_log)
                
                results.append({
                    "emp_id": emp_id,
                    "action": "suspended",
                    "message": f"{employee.full_name} suspended"
                })
            
            elif action == "notify":
                # Queue notification
                background_tasks.add_task(
                    send_compliance_notification,
                    emp_id=emp_id,
                    user_id=current_user.id
                )
                
                results.append({
                    "emp_id": emp_id,
                    "action": "notified",
                    "message": f"Notification queued for {employee.full_name}"
                })
        
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== NEW HIRE SETUP =====

class NewHireSetupRequest(BaseModel):
    emp_id: int
    hire_date: Optional[date] = None


@router.post("/compliance/setup-new-hire")
async def setup_new_hire_mtd(
    payload: NewHireSetupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Auto-create pending MTD records when a new employee is registered.
    Creates:
      - A baseline medical record (fit_status=0, next_due = hire_date + 6 months)
      - An induction record stub for every template required for employees
    Returns a summary of what was created.
    """
    try:
        from ..models.mtd import MTDMedicalRecord, MTDInductionTemplate, MTDInductionRecord
        from ..models.personnel import Personnel
        from datetime import timedelta

        employee = db.query(Personnel).filter(Personnel.id == payload.emp_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        created = []

        # ── Medical record ────────────────────────────────────────────────────
        existing_medical = db.query(MTDMedicalRecord).filter(
            MTDMedicalRecord.emp_id == payload.emp_id,
            MTDMedicalRecord.person_type == 0
        ).first()

        if not existing_medical:
            base_date = payload.hire_date or date.today()
            medical = MTDMedicalRecord(
                person_type=0,
                emp_id=payload.emp_id,
                fit_status=0,
                blood_group=employee.blood_group or None,
                medical_conditions=employee.medical_conditions or None,
                last_checkup=base_date,
                next_due=base_date + timedelta(days=180),
                doctor_name="Pending — initial medical required",
            )
            db.add(medical)
            created.append("medical_record")

        # ── Induction records ─────────────────────────────────────────────────
        templates = db.query(MTDInductionTemplate).filter(
            or_(
                MTDInductionTemplate.required_for_type == 0,   # employees
                MTDInductionTemplate.required_for_type == None  # all types
            )
        ).all()

        for tmpl in templates:
            existing_ind = db.query(MTDInductionRecord).filter(
                MTDInductionRecord.emp_id == payload.emp_id,
                MTDInductionRecord.template_id == tmpl.id
            ).first()
            if not existing_ind:
                ind = MTDInductionRecord(
                    person_type=0,
                    emp_id=payload.emp_id,
                    template_id=tmpl.id,
                    score=0,
                    passed=False,
                    completed_at=None,
                    trainer_emp_id=None,
                )
                db.add(ind)
                created.append(f"induction:{tmpl.template_name}")

        db.commit()

        return {
            "success": True,
            "data": {
                "emp_id": payload.emp_id,
                "emp_name": employee.full_name,
                "created": created,
                "message": f"{len(created)} MTD record(s) initialised for {employee.full_name}"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ===== VISITOR MTD =====

@router.post("/visitor/medical")
async def create_visitor_medical(
    visitor_id: int,
    medical_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create simplified medical record for visitor"""
    try:
        visitor_medical = {
            "person_type": 1,  # Visitor
            "visitor_id": visitor_id,
            "blood_group": medical_data.get("blood_group"),
            "allergies": medical_data.get("allergies"),
            "medical_conditions": medical_data.get("medical_conditions"),
            "fit_status": 0,  # Assume fit for visitors
            "doctor_name": "Visitor Registration",
            "last_checkup": date.today()
        }
        
        result = await mtd_service.create_medical_record(
            medical_data=visitor_medical,
            db=db,
            current_user=current_user
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visitor/induction")
async def create_visitor_induction(
    visitor_id: int,
    induction_data: Dict[str, Any],
    signed_doc: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create induction record for visitor"""
    try:
        # Handle file upload
        if signed_doc:
            doc_data = await signed_doc.read()
            induction_data['signed_doc'] = doc_data
        
        visitor_induction = {
            "person_type": 1,  # Visitor
            "visitor_id": visitor_id,
            "template_id": induction_data.get("template_id"),
            "score": induction_data.get("score", 0),
            "quiz_answers": induction_data.get("quiz_answers", [])
        }
        
        result = await mtd_service.take_induction(
            induction_data=visitor_induction,
            db=db,
            current_user=current_user
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== BACKGROUND TASKS =====

async def send_expiry_notifications(record_ids: List[int], channel: str, user_id: int):
    """Background task to send expiry notifications"""
    # This would integrate with email/SMS service
    print(f"Sending {channel} notifications for {len(record_ids)} expiring items")
    pass

async def send_compliance_notification(emp_id: int, user_id: int):
    """Background task to send compliance notifications"""
    # This would integrate with email/SMS service
    print(f"Sending compliance notification for employee {emp_id}")
    pass
