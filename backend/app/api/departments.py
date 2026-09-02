from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.department import Department, DepartmentPersonnel
from ..models.personnel import Personnel
from ..models.user import User
from ..models.biotime_models import PersonnelDepartment as BioTimeDept, AttShift
from ..models.zone import Zone

router = APIRouter(prefix="/departments", tags=["Departments"])

# ── Schemas ───────────────────────────────────────────────────────────────────

DEPT_TYPES = [
    "operations", "maintenance", "safety", "security", "administration",
    "logistics", "technical", "medical", "training", "contractor", "management", "support",
]

DEPT_STATUSES = ["active", "inactive", "temporary", "under_review"]

class DepartmentCreate(BaseModel):
    name:            str            = Field(..., min_length=1, max_length=100)
    code:            str            = Field(..., min_length=1, max_length=20)
    description:     Optional[str]  = None
    department_type: Optional[str]  = None
    parent_id:       Optional[int]  = None
    level:           Optional[int]  = 1
    sort_order:      Optional[int]  = 0
    zone_id:         Optional[int]  = None
    manager_id:      Optional[int]  = None
    contact_person:  Optional[str]  = Field(None, max_length=100)
    contact_email:   Optional[str]  = Field(None, max_length=100)
    contact_phone:   Optional[str]  = Field(None, max_length=20)
    max_personnel:   Optional[int]  = None
    budget_allocated: Optional[float] = None
    safety_critical:             Optional[bool] = False
    security_clearance_required: Optional[bool] = False
    required_certifications:     Optional[Any]  = None
    safety_protocols:            Optional[Any]  = None
    access_levels:               Optional[Any]  = None
    zkteco_sync_enabled:         Optional[bool] = True

class DepartmentUpdate(BaseModel):
    name:            Optional[str]  = Field(None, max_length=100)
    description:     Optional[str]  = None
    department_type: Optional[str]  = None
    status:          Optional[str]  = None
    parent_id:       Optional[int]  = None
    zone_id:         Optional[int]  = None
    manager_id:      Optional[int]  = None
    contact_person:  Optional[str]  = Field(None, max_length=100)
    contact_email:   Optional[str]  = Field(None, max_length=100)
    contact_phone:   Optional[str]  = Field(None, max_length=20)
    max_personnel:   Optional[int]  = None
    budget_allocated: Optional[float] = None
    budget_used:      Optional[float] = None
    safety_critical:             Optional[bool] = None
    security_clearance_required: Optional[bool] = None
    required_certifications:     Optional[Any]  = None
    safety_protocols:            Optional[Any]  = None
    access_levels:               Optional[Any]  = None
    zkteco_department_id: Optional[int]  = None
    zkteco_sync_enabled:  Optional[bool] = None
    is_active:            Optional[bool] = None
    default_shift_id:     Optional[int]  = None

class PersonnelAssignCreate(BaseModel):
    personnel_id: int
    role:         str            = Field(..., max_length=100)
    position:     Optional[str] = Field(None, max_length=100)
    is_primary:   Optional[bool] = False
    is_manager:   Optional[bool] = False

# ── Helpers ───────────────────────────────────────────────────────────────────

def _zkteco_status(dept: Department) -> str:
    if not dept.zkteco_sync_enabled:
        return "disabled"
    if not dept.zkteco_department_id:
        return "not_configured"
    if dept.last_sync_at:
        return "synced"
    return "pending"

def _to_dict(dept: Department, db: Session) -> dict:
    # Count active personnel assigned to this department via personnel.department_id —
    # the FK that is actually set when an employee is created/assigned. The legacy
    # DepartmentPersonnel association table is no longer populated by that flow, so
    # counting it returned 0 even though employees were assigned.
    from sqlalchemy import text as _sql_text
    personnel_count = db.execute(_sql_text(
        "SELECT COUNT(*) FROM personnel WHERE department_id = :did AND is_active = TRUE"
    ), {"did": dept.id}).scalar() or 0
    sub_dept_count = (
        db.query(Department)
        .filter(Department.parent_id == dept.id, Department.is_active == True)
        .count()
    )
    budget_alloc = float(dept.budget_allocated or 0)
    budget_used  = float(dept.budget_used or 0)
    utilization  = round(budget_used / budget_alloc * 100, 1) if budget_alloc > 0 else 0.0

    parent_name = None
    if dept.parent_id:
        p = db.query(Department).filter(Department.id == dept.parent_id).first()
        parent_name = p.name if p else None

    manager_name = None
    if dept.manager_id:
        m = db.query(Personnel).filter(Personnel.id == dept.manager_id).first()
        if m:
            manager_name = (f"{m.first_name or ''} {m.last_name or ''}".strip()) or m.full_name or None

    zone_name = None
    if dept.zone_id:
        z = db.query(Zone).filter(Zone.id == dept.zone_id).first()
        zone_name = z.name if z else None

    default_shift_name = None
    if dept.default_shift_id:
        s = db.query(AttShift).filter(AttShift.id == dept.default_shift_id).first()
        default_shift_name = s.name if s else None

    return {
        "id":               dept.id,
        "name":             dept.name,
        "code":             dept.code,
        "description":      dept.description,
        "department_type":  dept.department_type.lower() if dept.department_type else None,
        "status":           (dept.status or "active").lower(),
        "is_active":        dept.is_active,
        "parent_id":        dept.parent_id,
        "parent_name":      parent_name,
        "level":            dept.level,
        "sort_order":       dept.sort_order,
        "zone_id":          dept.zone_id,
        "zone_name":        zone_name,
        "manager_id":       dept.manager_id,
        "manager_name":     manager_name,
        "contact_person":   dept.contact_person,
        "contact_email":    dept.contact_email,
        "contact_phone":    dept.contact_phone,
        "max_personnel":    dept.max_personnel,
        "current_personnel_count": personnel_count,
        "sub_departments_count":   sub_dept_count,
        "budget_allocated": budget_alloc,
        "budget_used":      budget_used,
        "budget_utilization": utilization,
        "safety_critical":              dept.safety_critical or False,
        "security_clearance_required":  dept.security_clearance_required or False,
        "required_certifications":      dept.required_certifications,
        "safety_protocols":             dept.safety_protocols,
        "access_levels":                dept.access_levels,
        "zkteco_department_id": dept.zkteco_department_id,
        "zkteco_sync_enabled":  dept.zkteco_sync_enabled,
        "zkteco_status":        _zkteco_status(dept),
        "last_sync_at":         dept.last_sync_at.isoformat() if dept.last_sync_at else None,
        "default_shift_id":     dept.default_shift_id,
        "default_shift_name":   default_shift_name,
        "created_at":           dept.created_at.isoformat() if dept.created_at else None,
        "updated_at":           dept.updated_at.isoformat() if dept.updated_at else None,
        "created_by":           dept.created_by,
        "updated_by":           dept.updated_by,
    }

# ── Static routes (all must come before /{department_id}) ────────────────────

@router.get("/meta/summary")
async def department_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    depts = db.query(Department).filter(Department.is_active == True).all()
    by_type   = {}
    by_status = {}
    zkteco_synced = 0
    zkteco_pending = 0
    safety_critical = 0
    total_budget = 0.0
    used_budget  = 0.0

    for d in depts:
        dt = (d.department_type or "other").lower()
        by_type[dt] = by_type.get(dt, 0) + 1
        st = (d.status or "active").lower()
        by_status[st] = by_status.get(st, 0) + 1
        zs = _zkteco_status(d)
        if zs == "synced":
            zkteco_synced += 1
        elif zs == "pending":
            zkteco_pending += 1
        if d.safety_critical:
            safety_critical += 1
        total_budget += float(d.budget_allocated or 0)
        used_budget  += float(d.budget_used or 0)

    from sqlalchemy import text as _sql_text
    total_personnel = db.execute(_sql_text(
        "SELECT COUNT(*) FROM personnel WHERE department_id IS NOT NULL AND is_active = TRUE"
    )).scalar() or 0

    return {
        "total_departments":      len(depts),
        "active":                 by_status.get("active", 0),
        "inactive":               by_status.get("inactive", 0),
        "safety_critical":        safety_critical,
        "zkteco_synced":          zkteco_synced,
        "zkteco_pending":         zkteco_pending,
        "total_personnel_assigned": total_personnel,
        "total_budget_allocated": total_budget,
        "total_budget_used":      used_budget,
        "by_type":                by_type,
        "by_status":              by_status,
    }

@router.get("/types", response_model=List[str])
async def get_department_types():
    return DEPT_TYPES

@router.get("/statuses", response_model=List[str])
async def get_department_statuses():
    return DEPT_STATUSES

@router.get("/hierarchy/tree")
async def get_hierarchy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    depts = db.query(Department).filter(Department.is_active == True).order_by(Department.sort_order, Department.name).all()

    def build_tree(parent_id=None):
        return [
            {
                "id":              d.id,
                "name":            d.name,
                "code":            d.code,
                "department_type": d.department_type.lower() if d.department_type else None,
                "status":          (d.status or "active").lower(),
                "level":           d.level,
                "children":        build_tree(d.id),
            }
            for d in depts if d.parent_id == parent_id
        ]

    return build_tree()

# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_departments(
    department_type: Optional[str] = None,
    status:          Optional[str] = None,
    is_active:       Optional[bool] = True,
    parent_id:       Optional[int] = None,
    skip:  int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Department)
    if is_active is not None:
        q = q.filter(Department.is_active == is_active)
    if department_type:
        q = q.filter(Department.department_type == department_type)
    if status:
        q = q.filter(Department.status == status)
    if parent_id is not None:
        q = q.filter(Department.parent_id == parent_id)
    depts = q.order_by(Department.sort_order, Department.name).offset(skip).limit(limit).all()
    return [_to_dict(d, db) for d in depts]

@router.get("/{department_id}")
async def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return _to_dict(dept, db)

@router.post("", status_code=201)
async def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Department).filter(Department.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Department code '{data.code}' already exists")
    payload = data.model_dump()
    payload["created_by"] = current_user.id
    payload["updated_by"] = current_user.id
    dept = Department(**payload)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return _to_dict(dept, db)

@router.put("/{department_id}")
async def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(dept, k, v)
    dept.updated_by = current_user.id
    db.commit()
    db.refresh(dept)
    return _to_dict(dept, db)

@router.delete("/{department_id}", status_code=204)
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    children = db.query(Department).filter(Department.parent_id == department_id).count()
    if children:
        raise HTTPException(status_code=400, detail=f"Cannot delete department with {children} sub-department(s)")
    from sqlalchemy import text as _sql_text
    active_personnel = db.execute(_sql_text(
        "SELECT COUNT(*) FROM personnel WHERE department_id = :did AND is_active = TRUE"
    ), {"did": department_id}).scalar() or 0
    if active_personnel:
        raise HTTPException(status_code=400, detail=f"Cannot delete department with {active_personnel} active personnel assignment(s)")
    dept.is_active = False
    dept.status = "inactive"
    dept.updated_by = current_user.id
    db.commit()

# ── Personnel assignments ──────────────────────────────────────────────────────

@router.get("/{department_id}/personnel")
async def get_department_personnel(
    department_id: int,
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    # Personnel are linked to a department via personnel.department_id (set on
    # create/assign), not the legacy DepartmentPersonnel association table.
    from sqlalchemy import text as _sql_text
    active_only = (status or "").lower() == "active"
    rows = db.execute(_sql_text(
        "SELECT id, emp_code, first_name, last_name, personnel_type, company, role, position, is_active "
        "FROM personnel WHERE department_id = :did "
        + ("AND is_active = TRUE " if active_only else "")
        + "ORDER BY first_name, last_name"
    ), {"did": department_id}).fetchall()

    return [
        {
            "id":             p.id,
            "personnel_id":   p.id,
            "personnel_name": f"{p.first_name or ''} {p.last_name or ''}".strip() or p.emp_code,
            "emp_code":       p.emp_code,
            "personnel_type": p.personnel_type,
            "company":        p.company,
            "role":           p.role,
            "position":       p.position,
            "is_primary":     False,
            "is_manager":     False,
            "status":         "active" if p.is_active else "inactive",
            "assigned_at":    None,
        }
        for p in rows
    ]

@router.post("/{department_id}/assign-personnel", status_code=201)
async def assign_personnel(
    department_id: int,
    data: PersonnelAssignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if not db.query(Personnel).filter(Personnel.id == data.personnel_id).first():
        raise HTTPException(status_code=404, detail="Personnel not found")
    existing = db.query(DepartmentPersonnel).filter(
        DepartmentPersonnel.department_id == department_id,
        DepartmentPersonnel.personnel_id == data.personnel_id,
        DepartmentPersonnel.status == "active",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Personnel already assigned to this department")
    assignment = DepartmentPersonnel(
        department_id=department_id,
        personnel_id=data.personnel_id,
        role=data.role,
        position=data.position,
        is_primary=data.is_primary or False,
        is_manager=data.is_manager or False,
        approved_by=current_user.id,
        approved_at=datetime.utcnow(),
        status="active",
    )
    db.add(assignment)

    # Mirror the assignment onto the personnel record itself.
    #
    # Department membership is recorded in department_personnel (a person can sit
    # in several), but the attendance engine resolves an employee's shift through
    # personnel.department_id → departments.default_shift_id. Without this the
    # Department screen appears to assign someone and their shift never changes,
    # because nothing the engine reads was touched. The PRIMARY department is the
    # one that decides the shift; a person's first assignment is primary by
    # definition, since they had no department before it.
    person = db.query(Personnel).filter(Personnel.id == data.personnel_id).first()
    if person is not None:
        had_primary = db.query(DepartmentPersonnel).filter(
            DepartmentPersonnel.personnel_id == data.personnel_id,
            DepartmentPersonnel.status == "active",
            DepartmentPersonnel.is_primary.is_(True),
        ).first()
        if assignment.is_primary or had_primary is None or person.department_id is None:
            person.department_id = department_id
            person.department = dept.name

    db.commit()
    db.refresh(assignment)
    return {"id": assignment.id, "department_id": department_id, "personnel_id": data.personnel_id,
            "status": "active", "primary_department_id": getattr(person, "department_id", None)}

@router.delete("/{department_id}/personnel/{personnel_id}", status_code=204)
async def remove_personnel(
    department_id: int,
    personnel_id:  int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(DepartmentPersonnel).filter(
        DepartmentPersonnel.department_id == department_id,
        DepartmentPersonnel.personnel_id == personnel_id,
        DepartmentPersonnel.status == "active",
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Active assignment not found")
    assignment.status = "transferred"
    assignment.unassigned_at = datetime.utcnow()

    # If this was the department driving the employee's shift, move them to
    # whatever active assignment remains, or clear it. Leaving personnel.department_id
    # pointing at a department they were just removed from would keep applying that
    # department's shift to their timesheet.
    person = db.query(Personnel).filter(Personnel.id == personnel_id).first()
    if person is not None and person.department_id == department_id:
        remaining = db.query(DepartmentPersonnel).filter(
            DepartmentPersonnel.personnel_id == personnel_id,
            DepartmentPersonnel.status == "active",
            DepartmentPersonnel.department_id != department_id,
        ).order_by(DepartmentPersonnel.is_primary.desc(), DepartmentPersonnel.id).first()
        if remaining:
            other = db.query(Department).filter(Department.id == remaining.department_id).first()
            person.department_id = remaining.department_id
            person.department = other.name if other else None
        else:
            person.department_id = None
            person.department = None

    db.commit()

# ── ZKTeco sync ───────────────────────────────────────────────────────────────

@router.post("/{department_id}/push-to-biotime")
async def push_to_biotime(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id, Department.is_active == True).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if dept.zkteco_department_id:
        existing = db.query(BioTimeDept).filter(BioTimeDept.id == dept.zkteco_department_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already linked to BioTime department")
    bt = BioTimeDept(
        dept_code=dept.code[:20],
        dept_name=dept.name[:50],
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)
    dept.zkteco_department_id = bt.id
    dept.zkteco_sync_enabled  = True
    dept.last_sync_at         = datetime.utcnow()
    dept.updated_by           = current_user.id
    db.commit()
    db.refresh(dept)
    return _to_dict(dept, db)

@router.patch("/{department_id}/reactivate")
async def reactivate_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    dept.is_active = True
    dept.status = "active"
    dept.updated_by = current_user.id
    db.commit()
    db.refresh(dept)
    return _to_dict(dept, db)

# ── Clone ──────────────────────────────────────────────────────────────────────

class DepartmentClonePayload(BaseModel):
    name: Optional[str] = None
    code: str = Field(..., min_length=1, max_length=20)

@router.post("/{department_id}/clone", status_code=201)
async def clone_department(
    department_id: int,
    data: DepartmentClonePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    src = db.query(Department).filter(Department.id == department_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source department not found")
    if db.query(Department).filter(Department.code == data.code).first():
        raise HTTPException(status_code=400, detail=f"Code '{data.code}' already exists")
    new_dept = Department(
        name=data.name or f"{src.name} (Copy)",
        code=data.code,
        description=src.description,
        department_type=src.department_type,
        parent_id=src.parent_id,
        level=src.level,
        sort_order=src.sort_order,
        zone_id=src.zone_id,
        manager_id=src.manager_id,
        contact_person=src.contact_person,
        contact_email=src.contact_email,
        contact_phone=src.contact_phone,
        max_personnel=src.max_personnel,
        budget_allocated=src.budget_allocated,
        safety_critical=src.safety_critical,
        security_clearance_required=src.security_clearance_required,
        required_certifications=src.required_certifications,
        safety_protocols=src.safety_protocols,
        access_levels=src.access_levels,
        zkteco_sync_enabled=False,
        default_shift_id=src.default_shift_id,
        status="active",
        is_active=True,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return _to_dict(new_dept, db)

# ── Budget spend ───────────────────────────────────────────────────────────────

class BudgetSpendPayload(BaseModel):
    amount: float = Field(..., gt=0)
    description: Optional[str] = None

@router.post("/{department_id}/log-budget-spend")
async def log_budget_spend(
    department_id: int,
    data: BudgetSpendPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = db.query(Department).filter(Department.id == department_id, Department.is_active == True).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if not dept.budget_allocated:
        raise HTTPException(status_code=400, detail="No budget allocated for this department")
    dept.budget_used = float(dept.budget_used or 0) + data.amount
    dept.updated_by = current_user.id
    db.commit()
    db.refresh(dept)
    return _to_dict(dept, db)

# ── Transfer personnel ─────────────────────────────────────────────────────────

class PersonnelTransferPayload(BaseModel):
    personnel_id: int
    target_department_id: int
    role: str = Field(..., max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = False
    is_manager: Optional[bool] = False

@router.post("/{department_id}/transfer-personnel")
async def transfer_personnel_endpoint(
    department_id: int,
    data: PersonnelTransferPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if department_id == data.target_department_id:
        raise HTTPException(status_code=400, detail="Source and target departments must be different")
    target = db.query(Department).filter(Department.id == data.target_department_id, Department.is_active == True).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target department not found")
    assignment = db.query(DepartmentPersonnel).filter(
        DepartmentPersonnel.department_id == department_id,
        DepartmentPersonnel.personnel_id == data.personnel_id,
        DepartmentPersonnel.status == "active",
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Active assignment not found in source department")
    assignment.status = "transferred"
    assignment.unassigned_at = datetime.utcnow()
    existing = db.query(DepartmentPersonnel).filter(
        DepartmentPersonnel.department_id == data.target_department_id,
        DepartmentPersonnel.personnel_id == data.personnel_id,
        DepartmentPersonnel.status == "active",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Personnel already assigned to target department")
    db.add(DepartmentPersonnel(
        department_id=data.target_department_id,
        personnel_id=data.personnel_id,
        role=data.role,
        position=data.position,
        is_primary=data.is_primary or False,
        is_manager=data.is_manager or False,
        approved_by=current_user.id,
        approved_at=datetime.utcnow(),
        status="active",
    ))
    db.commit()
    return {"message": "Personnel transferred successfully", "target_department_id": data.target_department_id}
