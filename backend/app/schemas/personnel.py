from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, EmailStr
from datetime import datetime, date


# ── Create (BioTime-standard field names) ────────────────────────────────────
class PersonnelCreate(BaseModel):
    # BioTime core — maps directly to ZKTeco BioTime employee fields
    emp_code: str                              # BioTime PIN / unique employee number
    first_name: str
    last_name: str
    card_no: Optional[str] = None             # RFID badge number (→ badge_id in DB)
    hire_date: Optional[date] = None
    nationality: Optional[str] = None
    id_number: Optional[str] = None           # NIN / National ID
    passport_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    enable_att: bool = True
    dev_privilege: int = 0                    # 0=user, 6=admin (BioTime device privilege)

    # Employment
    company: Optional[str] = None
    department_id: Optional[int] = None
    department: Optional[str] = None         # dept name fallback when no dept_id
    role: Optional[str] = None               # Job title
    position: Optional[str] = None           # Position / grade
    employment_type: str = "EMPLOYEE"        # EMPLOYEE, CONTRACTOR, SUBCONTRACTOR

    # POB / oil & gas
    personnel_type: str = "STAFF"            # STAFF, CONTRACTOR, VISITOR
    safety_critical: bool = False
    is_onboard: bool = False
    current_zone_id: Optional[int] = None
    status: str = "ACTIVE"                   # ACTIVE, INACTIVE, ON_LEAVE, OFFSHORE, ONSHORE, TRANSIT

    # Medical & emergency
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_conditions: Optional[str] = None


# ── Update (all optional) ────────────────────────────────────────────────────
class PersonnelUpdate(BaseModel):
    emp_code: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    card_no: Optional[str] = None
    hire_date: Optional[date] = None
    nationality: Optional[str] = None
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    department_id: Optional[int] = None
    department: Optional[str] = None
    role: Optional[str] = None
    position: Optional[str] = None
    employment_type: Optional[str] = None
    personnel_type: Optional[str] = None
    safety_critical: Optional[bool] = None
    is_onboard: Optional[bool] = None
    current_zone_id: Optional[int] = None
    # The COMPLETE set of warehouses this employee may clock in at. Sending a
    # set rather than a single id is what lets an edit remove a site as well as
    # add one; omit the field entirely to leave assignments untouched.
    warehouse_ids: Optional[List[int]] = None
    status: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_conditions: Optional[str] = None


# ── Response ─────────────────────────────────────────────────────────────────
class PersonnelResponse(BaseModel):
    id: int
    emp_code: str
    badge_id: Optional[str] = None           # RFID card / physical badge
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    nationality: Optional[str] = None
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    hire_date: Optional[date] = None
    company: Optional[str] = None
    department: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None
    position: Optional[str] = None
    employment_type: Optional[str] = None
    personnel_type: Optional[str] = None
    status: Optional[str] = None
    is_onboard: Optional[bool] = False
    is_pob: Optional[bool] = False
    safety_critical: Optional[bool] = False
    biometric_enrolled: Optional[bool] = False
    compliance_score: Optional[float] = 0.0
    current_zone_id: Optional[int] = None
    current_location: Optional[str] = None
    photo_url: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_conditions: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Stats ─────────────────────────────────────────────────────────────────────
class PersonnelStats(BaseModel):
    total_personnel: int
    active_personnel: int
    offshore_personnel: int
    onshore_personnel: int
    personnel_onboard: int
    personnel_not_onboard: int
