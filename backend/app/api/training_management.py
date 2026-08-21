from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.training_management import TrainingCourse, TrainingEnrollment
from ..models.personnel import Personnel
from ..schemas.training_management import (
    TrainingCourseCreate, TrainingCourseUpdate, TrainingCourseResponse,
    TrainingEnrollmentCreate, TrainingEnrollmentUpdate, TrainingEnrollmentResponse,
    TrainingCompleteRequest, ComplianceRecord,
    TRAINING_CATEGORIES, TRAINING_STATUSES,
)
from ..models.user import User

router = APIRouter()

# ── Oil & Gas standard course catalogue ───────────────────────────────────────
OG_STANDARD_COURSES = [
    # Safety / Emergency
    {"course_code": "BOSIET",   "course_name": "Basic Offshore Safety Induction & Emergency Training", "category": "safety",        "duration_hours": 40, "is_mandatory": True,  "valid_period_months": 48, "description": "OPITO-accredited. Covers survival techniques, firefighting, first aid, HUET, and helicopter safety. Required for all offshore personnel."},
    {"course_code": "FOET",     "course_name": "Further Offshore Emergency Training",                  "category": "safety",        "duration_hours": 16, "is_mandatory": True,  "valid_period_months": 48, "description": "OPITO refresher for BOSIET holders. Renews offshore emergency response competency."},
    {"course_code": "HUET",     "course_name": "Helicopter Underwater Escape Training",                "category": "safety",        "duration_hours": 8,  "is_mandatory": True,  "valid_period_months": 48, "description": "Escape from submerged helicopter including inverted escape and EBS use."},
    {"course_code": "H2S-SA",   "course_name": "H₂S Safety Awareness",                                "category": "safety",        "duration_hours": 8,  "is_mandatory": True,  "valid_period_months": 24, "description": "Hydrogen Sulfide hazard recognition, detection, and emergency response. Mandatory at all H₂S risk sites."},
    {"course_code": "FIRE-FP",  "course_name": "Fire Fighting & Prevention",                          "category": "safety",        "duration_hours": 16, "is_mandatory": True,  "valid_period_months": 24, "description": "Fire prevention, use of extinguishers, hose reel, and foam systems. Evacuation procedures."},
    {"course_code": "MUSTER",   "course_name": "Emergency Muster & Evacuation Procedures",            "category": "safety",        "duration_hours": 4,  "is_mandatory": True,  "valid_period_months": 12, "description": "Muster station drill, lifeboat/life raft deployment, TEMPSC operations."},
    {"course_code": "CONFINED", "course_name": "Confined Space Entry",                                "category": "safety",        "duration_hours": 16, "is_mandatory": False, "valid_period_months": 24, "description": "Atmospheric testing, permit-to-work in confined spaces, emergency rescue."},
    {"course_code": "WAH",      "course_name": "Working at Height",                                   "category": "safety",        "duration_hours": 8,  "is_mandatory": False, "valid_period_months": 24, "description": "Fall arrest systems, scaffolding inspection, harness use and inspection."},
    {"course_code": "MANUAL",   "course_name": "Manual Handling",                                     "category": "safety",        "duration_hours": 4,  "is_mandatory": True,  "valid_period_months": 24, "description": "Safe lifting techniques, ergonomics, musculoskeletal injury prevention."},
    # Compliance / Regulatory
    {"course_code": "PTW",      "course_name": "Permit to Work System",                               "category": "compliance",    "duration_hours": 8,  "is_mandatory": True,  "valid_period_months": 24, "description": "Hot work, cold work, electrical isolation, and confined space permit-to-work procedures."},
    {"course_code": "IWCF-S",   "course_name": "Well Control — Subsurface (IWCF)",                    "category": "compliance",    "duration_hours": 40, "is_mandatory": False, "valid_period_months": 24, "description": "IWCF-certified well control for drilling and workover personnel."},
    {"course_code": "LOLER",    "course_name": "LOLER / Lifting Operations Safety",                   "category": "compliance",    "duration_hours": 8,  "is_mandatory": False, "valid_period_months": 36, "description": "Lifting Operations and Lifting Equipment Regulations. Rigging, slinging, and inspection."},
    {"course_code": "HAZMAT",   "course_name": "Hazardous Materials Handling (COSHH)",                "category": "compliance",    "duration_hours": 8,  "is_mandatory": True,  "valid_period_months": 24, "description": "Control of Substances Hazardous to Health. SDS interpretation, PPE selection, spill response."},
    {"course_code": "ENV-AWR",  "course_name": "Environmental Awareness",                            "category": "compliance",    "duration_hours": 4,  "is_mandatory": True,  "valid_period_months": 12, "description": "Oil spill response, waste management, environmental legislation compliance."},
    {"course_code": "SEC-AWR",  "course_name": "Security Awareness (ISPS)",                          "category": "compliance",    "duration_hours": 4,  "is_mandatory": True,  "valid_period_months": 12, "description": "ISPS Code awareness for offshore facilities. Threat recognition, access control."},
    # Technical
    {"course_code": "RIGGING",  "course_name": "Rigging & Slinging",                                  "category": "technical",     "duration_hours": 16, "is_mandatory": False, "valid_period_months": 36, "description": "Wire rope, chain slings, shackles, and lifting beam operations. BS EN 13411."},
    {"course_code": "SCAFFOLD", "course_name": "Scaffold Inspector",                                  "category": "technical",     "duration_hours": 24, "is_mandatory": False, "valid_period_months": 36, "description": "Scaffold inspection, tagging, and TG20 compliance. CISRS-aligned."},
    {"course_code": "CRANE-OP", "course_name": "Offshore Crane Operations",                           "category": "technical",     "duration_hours": 40, "is_mandatory": False, "valid_period_months": 36, "description": "Pedestal crane operations, blind lifts, load charts, and adverse weather procedures."},
    {"course_code": "ELEC-SAF", "course_name": "Electrical Safety Awareness",                        "category": "technical",     "duration_hours": 8,  "is_mandatory": False, "valid_period_months": 24, "description": "LV/HV isolation, LOTO, arc flash, and safe working on electrical equipment."},
    # Medical / Welfare
    {"course_code": "FA-BASIC", "course_name": "Basic First Aid",                                     "category": "safety",        "duration_hours": 16, "is_mandatory": True,  "valid_period_months": 36, "description": "CPR, AED, wound management, fracture stabilisation, and shock treatment."},
    {"course_code": "MEDEVAC",  "course_name": "Medical Evacuation Procedures",                       "category": "safety",        "duration_hours": 4,  "is_mandatory": True,  "valid_period_months": 12, "description": "Casualty handling, stretcher use, helicopter winching, and medevac coordination."},
    # Leadership / Soft Skills
    {"course_code": "SAFE-LD",  "course_name": "Safety Leadership & Behavioural Safety",             "category": "leadership",    "duration_hours": 16, "is_mandatory": False, "valid_period_months": 24, "description": "Human factors, safety culture, toolbox talks, and incident causation theory."},
    {"course_code": "INDUCT",   "course_name": "Site Safety Induction",                               "category": "induction",     "duration_hours": 4,  "is_mandatory": True,  "valid_period_months": 12, "description": "Facility-specific induction covering muster points, emergency signals, prohibited areas, and PPE requirements. Required for ALL personnel before site access."},
    {"course_code": "DEF-DRV",  "course_name": "Defensive Driving",                                  "category": "soft_skills",   "duration_hours": 8,  "is_mandatory": False, "valid_period_months": 36, "description": "Safe driving techniques, night driving on site roads, convoy procedures."},
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _cert_status(expiry_date: Optional[date]) -> str:
    """Returns valid|expiring|expired|no_expiry."""
    if expiry_date is None:
        return "no_expiry"
    today = date.today()
    if expiry_date < today:
        return "expired"
    if (expiry_date - today).days <= 30:
        return "expiring"
    return "valid"


def _calc_expiry(completion: Optional[date], valid_months: Optional[int]) -> Optional[date]:
    if completion is None or valid_months is None:
        return None
    return completion + relativedelta(months=valid_months)


def _enrich_enrollment(rec: TrainingEnrollment) -> TrainingEnrollment:
    if rec.personnel:
        rec.personnel_name = f"{rec.personnel.first_name} {rec.personnel.last_name}".strip()
        rec.personnel_emp_code = getattr(rec.personnel, "emp_code", None)
        rec.personnel_company = getattr(rec.personnel, "company", None)
        # Sync personnel_type from personnel record
        if not rec.personnel_type:
            rec.personnel_type = getattr(rec.personnel, "personnel_type", None)
        dept = getattr(rec.personnel, "department", None)
        rec.department_id   = getattr(rec.personnel, "department_id", None)
        rec.department_name = getattr(dept, "name", None) if dept else None
    else:
        rec.personnel_name = None
        rec.personnel_emp_code = None
        rec.personnel_company = None
        rec.department_id = None
        rec.department_name = None

    if rec.course:
        rec.course_name = rec.course.course_name
        rec.course_code = rec.course.course_code
        rec.course_category = rec.course.category
        rec.is_mandatory = rec.course.is_mandatory
        rec.valid_period_months = rec.course.valid_period_months
    else:
        rec.course_name = None
        rec.course_code = None
        rec.course_category = None
        rec.is_mandatory = None
        rec.valid_period_months = None

    rec.cert_status = _cert_status(rec.expiry_date)
    return rec


def _enrich_course(rec: TrainingCourse, db: Session) -> TrainingCourse:
    rec.enrollment_count = (
        db.query(func.count(TrainingEnrollment.id))
        .filter(TrainingEnrollment.course_id == rec.id)
        .scalar()
    )
    return rec


# ── static paths ──────────────────────────────────────────────────────────────

@router.get("/training/categories")
async def get_training_categories(current_user: User = Depends(get_current_user)):
    return TRAINING_CATEGORIES


@router.get("/training/statuses")
async def get_training_statuses(current_user: User = Depends(get_current_user)):
    return TRAINING_STATUSES


@router.get("/training/standard-courses")
async def get_standard_courses(current_user: User = Depends(get_current_user)):
    """Return the built-in O&G course catalogue (not yet imported courses)."""
    return OG_STANDARD_COURSES


@router.post("/training/import-standard-courses", status_code=status.HTTP_201_CREATED)
async def import_standard_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import all standard O&G courses that do not already exist (by course_code).
    Returns a summary of created vs skipped.
    """
    created, skipped = [], []
    for c in OG_STANDARD_COURSES:
        existing = db.query(TrainingCourse).filter(TrainingCourse.course_code == c["course_code"]).first()
        if existing:
            skipped.append(c["course_code"])
        else:
            course = TrainingCourse(**c, created_by=current_user.id)
            db.add(course)
            created.append(c["course_code"])
    db.commit()
    return {"created": len(created), "skipped": len(skipped), "codes": created}


@router.get("/training/summary")
async def get_training_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_courses = db.query(func.count(TrainingCourse.id)).scalar() or 0
    mandatory_courses = (
        db.query(func.count(TrainingCourse.id))
        .filter(TrainingCourse.is_mandatory == True).scalar() or 0
    )
    total_enrollments = db.query(func.count(TrainingEnrollment.id)).scalar() or 0
    completed = db.query(func.count(TrainingEnrollment.id)).filter(TrainingEnrollment.status == "completed").scalar() or 0
    certified = db.query(func.count(TrainingEnrollment.id)).filter(TrainingEnrollment.status == "certified").scalar() or 0
    in_progress = db.query(func.count(TrainingEnrollment.id)).filter(TrainingEnrollment.status == "in_progress").scalar() or 0
    expired = (
        db.query(func.count(TrainingEnrollment.id))
        .filter(
            TrainingEnrollment.expiry_date < date.today(),
            TrainingEnrollment.status == "certified",
        ).scalar() or 0
    )

    # Breakdown by personnel type
    type_counts = (
        db.query(TrainingEnrollment.personnel_type, func.count(TrainingEnrollment.id))
        .group_by(TrainingEnrollment.personnel_type)
        .all()
    )

    return {
        "total_courses": total_courses,
        "mandatory_courses": mandatory_courses,
        "total_enrollments": total_enrollments,
        "completed": completed,
        "certified": certified,
        "in_progress": in_progress,
        "expired_certs": expired,
        "by_personnel_type": {t or "unknown": c for t, c in type_counts},
    }


@router.get("/training/compliance", response_model=List[ComplianceRecord])
async def get_compliance_gaps(
    personnel_type: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all personnel × mandatory course combinations where compliance is missing:
    - never enrolled
    - enrolled but failed/cancelled
    - certificate expired
    - certificate expiring within 30 days
    """
    # Get all mandatory courses
    courses_q = db.query(TrainingCourse).filter(TrainingCourse.is_mandatory == True)
    if category:
        courses_q = courses_q.filter(TrainingCourse.category == category)
    mandatory_courses = courses_q.all()

    if not mandatory_courses:
        return []

    # Get all active personnel
    # status is an UPPERCASE enum describing location (ACTIVE/ONSHORE/OFFSHORE);
    # is_active is the employed flag. The lowercase literal matched nobody.
    pers_q = db.query(Personnel).filter(Personnel.is_active.is_(True))
    if personnel_type:
        pers_q = pers_q.filter(Personnel.personnel_type == personnel_type)
    active_personnel = pers_q.all()

    today = date.today()
    gaps: List[ComplianceRecord] = []

    for person in active_personnel:
        for course in mandatory_courses:
            # Find best enrollment for this person × course
            enrollments = (
                db.query(TrainingEnrollment)
                .filter(
                    TrainingEnrollment.personnel_id == person.id,
                    TrainingEnrollment.course_id == course.id,
                )
                .order_by(TrainingEnrollment.created_at.desc())
                .all()
            )

            # Check for valid certification
            valid_cert = next(
                (
                    e for e in enrollments
                    if e.status == "certified"
                    and (e.expiry_date is None or e.expiry_date >= today)
                    and (e.expiry_date is None or (e.expiry_date - today).days > 30)
                ),
                None,
            )
            if valid_cert:
                continue  # compliant

            # Determine the issue
            if not enrollments:
                issue = "never_enrolled"
                expiry = None
                days = None
            else:
                latest = enrollments[0]
                if latest.status in ("failed", "cancelled"):
                    issue = "failed"
                    expiry = None
                    days = None
                elif latest.status == "certified" and latest.expiry_date:
                    if latest.expiry_date < today:
                        issue = "expired"
                        expiry = latest.expiry_date
                        days = (today - latest.expiry_date).days * -1
                    else:
                        issue = "expiring_soon"
                        expiry = latest.expiry_date
                        days = (latest.expiry_date - today).days
                else:
                    # enrolled or in_progress — not yet a gap, skip
                    continue

            dept = getattr(person, "department", None)
            gaps.append(ComplianceRecord(
                personnel_id=person.id,
                personnel_name=f"{person.first_name} {person.last_name}".strip(),
                personnel_emp_code=person.emp_code,
                personnel_type=person.personnel_type or "STAFF",
                personnel_company=person.company,
                department_id=getattr(person, "department_id", None),
                department_name=getattr(dept, "name", None) if dept else None,
                course_id=course.id,
                course_name=course.course_name,
                course_code=course.course_code,
                category=course.category,
                issue=issue,
                expiry_date=expiry,
                days_until_expiry=days,
            ))

    return gaps


# ── course CRUD ───────────────────────────────────────────────────────────────

@router.post("/training/courses", response_model=TrainingCourseResponse, status_code=status.HTTP_201_CREATED)
async def create_training_course(
    course_data: TrainingCourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(TrainingCourse).filter(TrainingCourse.course_code == course_data.course_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Course code '{course_data.course_code}' already exists")
    course = TrainingCourse(**course_data.model_dump(), created_by=current_user.id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return _enrich_course(course, db)


@router.get("/training/courses", response_model=List[TrainingCourseResponse])
async def get_training_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    category: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(TrainingCourse)
    if category:
        q = q.filter(TrainingCourse.category == category)
    if is_mandatory is not None:
        q = q.filter(TrainingCourse.is_mandatory == is_mandatory)
    if search:
        q = q.filter(
            TrainingCourse.course_name.ilike(f"%{search}%") |
            TrainingCourse.course_code.ilike(f"%{search}%")
        )
    return [_enrich_course(c, db) for c in q.order_by(TrainingCourse.course_name).offset(skip).limit(limit).all()]


@router.get("/training/courses/{course_id}", response_model=TrainingCourseResponse)
async def get_training_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(TrainingCourse).filter(TrainingCourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _enrich_course(course, db)


@router.put("/training/courses/{course_id}", response_model=TrainingCourseResponse)
async def update_training_course(
    course_id: int,
    course_data: TrainingCourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(TrainingCourse).filter(TrainingCourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for field, value in course_data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return _enrich_course(course, db)


@router.delete("/training/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(TrainingCourse).filter(TrainingCourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    enrolled = db.query(TrainingEnrollment).filter(TrainingEnrollment.course_id == course_id).count()
    if enrolled:
        raise HTTPException(status_code=400, detail=f"Cannot delete: {enrolled} enrollment(s) exist for this course")
    db.delete(course)
    db.commit()


# ── enrollment CRUD ───────────────────────────────────────────────────────────

@router.post("/training/enrollments", response_model=TrainingEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_in_training(
    enrollment_data: TrainingEnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    personnel = db.query(Personnel).filter(Personnel.id == enrollment_data.personnel_id).first()
    if not personnel:
        raise HTTPException(status_code=404, detail="Personnel not found")

    course = db.query(TrainingCourse).filter(TrainingCourse.id == enrollment_data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    duplicate = db.query(TrainingEnrollment).filter(
        TrainingEnrollment.personnel_id == enrollment_data.personnel_id,
        TrainingEnrollment.course_id == enrollment_data.course_id,
        TrainingEnrollment.status.in_(["enrolled", "in_progress"]),
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Personnel is already actively enrolled in this course")

    data = enrollment_data.model_dump()
    data["personnel_type"] = personnel.personnel_type  # denormalize for compliance queries
    enrollment = TrainingEnrollment(**data)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return _enrich_enrollment(enrollment)


@router.get("/training/enrollments", response_model=List[TrainingEnrollmentResponse])
async def get_training_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    personnel_id: Optional[int] = None,
    course_id: Optional[int] = None,
    status: Optional[str] = None,
    personnel_type: Optional[str] = None,
    category: Optional[str] = None,
    department_id: Optional[int] = None,
    search: Optional[str] = None,
    expiring_within_days: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(TrainingEnrollment)
    if personnel_id:
        q = q.filter(TrainingEnrollment.personnel_id == personnel_id)
    if course_id:
        q = q.filter(TrainingEnrollment.course_id == course_id)
    if status:
        q = q.filter(TrainingEnrollment.status == status)
    if personnel_type:
        q = q.filter(TrainingEnrollment.personnel_type == personnel_type)
    if category:
        q = q.join(TrainingCourse).filter(TrainingCourse.category == category)
    if expiring_within_days is not None:
        from datetime import timedelta
        cutoff = date.today() + timedelta(days=expiring_within_days)
        q = q.filter(
            TrainingEnrollment.expiry_date <= cutoff,
            TrainingEnrollment.expiry_date >= date.today(),
        )
    enrollments = q.order_by(TrainingEnrollment.enrollment_date.desc()).offset(skip).limit(limit).all()
    enriched = [_enrich_enrollment(e) for e in enrollments]
    if department_id:
        enriched = [e for e in enriched if e.department_id == department_id]
    return enriched


@router.get("/training/enrollments/{enrollment_id}", response_model=TrainingEnrollmentResponse)
async def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return _enrich_enrollment(enrollment)


@router.put("/training/enrollments/{enrollment_id}", response_model=TrainingEnrollmentResponse)
async def update_enrollment(
    enrollment_id: int,
    data: TrainingEnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(enrollment, field, value)
    db.commit()
    db.refresh(enrollment)
    return _enrich_enrollment(enrollment)


@router.delete("/training/enrollments/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    db.delete(enrollment)
    db.commit()


@router.put("/training/enrollments/{enrollment_id}/start", response_model=TrainingEnrollmentResponse)
async def start_training(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment.status != "enrolled":
        raise HTTPException(status_code=400, detail=f"Cannot start a {enrollment.status} enrollment")
    enrollment.status = "in_progress"
    db.commit()
    db.refresh(enrollment)
    return _enrich_enrollment(enrollment)


@router.put("/training/enrollments/{enrollment_id}/complete", response_model=TrainingEnrollmentResponse)
async def complete_training(
    enrollment_id: int,
    data: TrainingCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment.status not in ("enrolled", "in_progress"):
        raise HTTPException(status_code=400, detail=f"Cannot complete a {enrollment.status} enrollment")

    enrollment.status = "completed"
    enrollment.completion_date = data.completion_date or date.today()
    if data.score is not None:
        enrollment.score = data.score
    if data.certificate_url:
        enrollment.certificate_url = data.certificate_url

    db.commit()
    db.refresh(enrollment)
    return _enrich_enrollment(enrollment)


@router.put("/training/enrollments/{enrollment_id}/certify", response_model=TrainingEnrollmentResponse)
async def certify_training(
    enrollment_id: int,
    data: TrainingCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment.status != "completed":
        raise HTTPException(status_code=400, detail="Can only certify completed enrollments")

    enrollment.status = "certified"
    if data.certificate_url:
        enrollment.certificate_url = data.certificate_url

    # Calculate certificate expiry
    completion = enrollment.completion_date or date.today()
    course = db.query(TrainingCourse).filter(TrainingCourse.id == enrollment.course_id).first()
    if course and course.valid_period_months:
        enrollment.expiry_date = _calc_expiry(completion, course.valid_period_months)

    db.commit()
    db.refresh(enrollment)
    return _enrich_enrollment(enrollment)


@router.put("/training/enrollments/{enrollment_id}/fail", response_model=TrainingEnrollmentResponse)
async def fail_training(
    enrollment_id: int,
    data: TrainingCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    enrollment.status = "failed"
    if data.score is not None:
        enrollment.score = data.score
    enrollment.completion_date = data.completion_date or date.today()
    db.commit()
    db.refresh(enrollment)
    return _enrich_enrollment(enrollment)


@router.put("/training/enrollments/{enrollment_id}/cancel", response_model=TrainingEnrollmentResponse)
async def cancel_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment.status in ("completed", "certified"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a {enrollment.status} enrollment")
    enrollment.status = "cancelled"
    db.commit()
    db.refresh(enrollment)
    return _enrich_enrollment(enrollment)
