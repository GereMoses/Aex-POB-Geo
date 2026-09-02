"""
Vendor/Contractor Management Pydantic Schemas
Request and response models for vendor and contractor management API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VendorType(str, Enum):
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    EQUIPMENT_SUPPLIER = "EQUIPMENT_SUPPLIER"
    CONSULTING_FIRM = "CONSULTING_FIRM"
    STAFFING_AGENCY = "STAFFING_AGENCY"
    TRAINING_PROVIDER = "TRAINING_PROVIDER"
    SOFTWARE_VENDOR = "SOFTWARE_VENDOR"
    MAINTENANCE_PROVIDER = "MAINTENANCE_PROVIDER"


class VendorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    UNDER_REVIEW = "UNDER_REVIEW"
    BLACKLISTED = "BLACKLISTED"


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    PENDING_REVIEW = "PENDING_REVIEW"
    NON_COMPLIANT = "NON_COMPLIANT"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


class ContractStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"
    RENEWAL_PENDING = "RENEWAL_PENDING"
    SUSPENDED = "SUSPENDED"


class VendorCreate(BaseModel):
    """Request to create vendor"""
    vendor_code: str = Field(..., min_length=1, max_length=50, description="Unique vendor code")
    vendor_name: str = Field(..., min_length=1, max_length=200, description="Vendor name")
    vendor_type: VendorType = Field(..., description="Type of vendor")
    description: Optional[str] = Field(None, max_length=1000, description="Vendor description")
    
    # Contact information
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    mobile: Optional[str] = Field(None, max_length=20, description="Mobile number")
    fax: Optional[str] = Field(None, max_length=20, description="Fax number")
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=200, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    
    # Business information
    business_registration: Optional[str] = Field(None, max_length=100, description="Business registration")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax ID")
    website: Optional[str] = Field(None, max_length=200, description="Website")
    
    # Services and capabilities
    services_offered: Optional[List[str]] = Field(None, description="Services offered")
    service_areas: Optional[List[str]] = Field(None, description="Service areas")
    certifications: Optional[List[Dict[str, Any]]] = Field(None, description="Vendor certifications")
    
    # Financial information
    payment_terms: Optional[str] = Field(None, max_length=100, description="Payment terms")
    credit_limit: Optional[float] = Field(None, ge=0, description="Credit limit")
    currency: Optional[str] = Field("USD", max_length=3, description="Currency")
    
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class VendorUpdate(BaseModel):
    """Request to update vendor"""
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    vendor_type: Optional[VendorType] = Field(None)
    status: Optional[VendorStatus] = Field(None)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Contact information
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    # Business information
    business_registration: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=200)
    
    # Services and capabilities
    services_offered: Optional[List[str]] = Field(None)
    service_areas: Optional[List[str]] = Field(None)
    certifications: Optional[List[Dict[str, Any]]] = Field(None)
    
    # Financial information
    payment_terms: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    
    # Compliance and risk
    compliance_status: Optional[ComplianceStatus] = Field(None)
    next_compliance_due: Optional[datetime] = Field(None)
    risk_rating: Optional[str] = Field(None, max_length=10)
    
    notes: Optional[str] = Field(None, max_length=500)


class VendorResponse(BaseModel):
    """Vendor response model"""
    id: int
    vendor_code: str
    vendor_name: str
    vendor_type: VendorType
    status: VendorStatus
    description: Optional[str]
    
    # Contact information
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    fax: Optional[str]
    
    # Address
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    
    # Business information
    business_registration: Optional[str]
    tax_id: Optional[str]
    website: Optional[str]
    
    # Services and capabilities
    services_offered: Optional[List[str]]
    service_areas: Optional[List[str]]
    certifications: Optional[List[Dict[str, Any]]]
    
    # Financial information
    payment_terms: Optional[str]
    credit_limit: Optional[float]
    currency: Optional[str]
    
    # Compliance and risk
    compliance_status: Optional[ComplianceStatus]
    last_compliance_check: Optional[datetime]
    next_compliance_due: Optional[datetime]
    risk_rating: Optional[str]
    
    # Performance metrics
    performance_score: float
    total_contracts: int
    active_contracts: int
    
    # Audit trail
    created_by: int
    created_at: datetime
    updated_by: Optional[int]
    updated_at: datetime
    notes: Optional[str]


class VendorContractCreate(BaseModel):
    """Request to create vendor contract"""
    vendor_id: int = Field(..., description="Vendor ID")
    contract_number: str = Field(..., min_length=1, max_length=50, description="Contract number")
    contract_name: str = Field(..., min_length=1, max_length=200, description="Contract name")
    contract_type: str = Field(..., min_length=1, max_length=50, description="Contract type")
    start_date: datetime = Field(..., description="Contract start date")
    end_date: datetime = Field(..., description="Contract end date")
    renewal_date: Optional[datetime] = Field(None, description="Renewal date")
    notice_period_days: Optional[int] = Field(30, ge=1, description="Notice period in days")
    
    # Financial terms
    total_value: Optional[float] = Field(None, ge=0, description="Total contract value")
    currency: Optional[str] = Field("USD", max_length=3, description="Currency")
    payment_terms: Optional[str] = Field(None, max_length=100, description="Payment terms")
    billing_frequency: Optional[str] = Field(None, max_length=20, description="Billing frequency")
    
    # Service level agreement
    sla_requirements: Optional[Dict[str, Any]] = Field(None, description="SLA requirements")
    penalty_clauses: Optional[Dict[str, Any]] = Field(None, description="Penalty clauses")
    
    # Scope and deliverables
    scope_of_work: Optional[str] = Field(None, max_length=2000, description="Scope of work")
    deliverables: Optional[List[Dict[str, Any]]] = Field(None, description="Deliverables")
    key_performance_indicators: Optional[Dict[str, Any]] = Field(None, description="KPIs")
    
    # Contract management
    contract_manager: Optional[int] = Field(None, description="Contract manager ID")
    legal_reviewer: Optional[int] = Field(None, description="Legal reviewer ID")
    
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class VendorContractResponse(BaseModel):
    """Vendor contract response model"""
    id: int
    vendor_id: int
    contract_number: str
    contract_name: str
    contract_type: str
    status: ContractStatus
    
    # Contract dates
    start_date: datetime
    end_date: datetime
    renewal_date: Optional[datetime]
    notice_period_days: int
    
    # Financial terms
    total_value: Optional[float]
    currency: Optional[str]
    payment_terms: Optional[str]
    billing_frequency: Optional[str]
    
    # Service level agreement
    sla_requirements: Optional[Dict[str, Any]]
    penalty_clauses: Optional[Dict[str, Any]]
    
    # Scope and deliverables
    scope_of_work: Optional[str]
    deliverables: Optional[List[Dict[str, Any]]]
    key_performance_indicators: Optional[Dict[str, Any]]
    
    # Contract management
    contract_manager: Optional[int]
    legal_reviewer: Optional[int]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    
    # Performance tracking
    performance_score: float
    compliance_score: float
    last_performance_review: Optional[datetime]
    
    # Vendor info
    vendor_name: Optional[str]
    vendor_code: Optional[str]
    
    # Audit trail
    created_by: int
    created_at: datetime
    updated_by: Optional[int]
    updated_at: datetime
    notes: Optional[str]


class ContractorCreate(BaseModel):
    """Request to create contractor"""
    vendor_id: Optional[int] = Field(None, description="Vendor ID")
    contractor_code: str = Field(..., min_length=1, max_length=50, description="Contractor code")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    
    # Personal information
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    national_id: Optional[str] = Field(None, max_length=50, description="National ID")
    passport_number: Optional[str] = Field(None, max_length=50, description="Passport number")
    work_permit_number: Optional[str] = Field(None, max_length=50, description="Work permit number")
    work_permit_expiry: Optional[datetime] = Field(None, description="Work permit expiry")
    
    # Professional information
    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    specialization: Optional[str] = Field(None, max_length=100, description="Specialization")
    experience_years: Optional[int] = Field(0, ge=0, description="Experience in years")
    hourly_rate: Optional[float] = Field(None, ge=0, description="Hourly rate")
    daily_rate: Optional[float] = Field(None, ge=0, description="Daily rate")
    currency: Optional[str] = Field("USD", max_length=3, description="Currency")
    
    # Skills and certifications
    skills: Optional[List[str]] = Field(None, description="Skills")
    certifications: Optional[List[Dict[str, Any]]] = Field(None, description="Certifications")
    security_clearance: Optional[str] = Field(None, max_length=50, description="Security clearance")
    
    # Status and availability
    availability_status: Optional[str] = Field("AVAILABLE", max_length=20, description="Availability status")
    preferred_work_locations: Optional[List[str]] = Field(None, description="Preferred work locations")
    
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class ContractorUpdate(BaseModel):
    """Request to update contractor — every field optional (PATCH-style PUT)"""
    vendor_id: Optional[int] = Field(None, description="Vendor ID")
    contractor_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Contractor code")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")

    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    national_id: Optional[str] = Field(None, max_length=50, description="National ID")
    passport_number: Optional[str] = Field(None, max_length=50, description="Passport number")
    work_permit_number: Optional[str] = Field(None, max_length=50, description="Work permit number")
    work_permit_expiry: Optional[datetime] = Field(None, description="Work permit expiry")

    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    specialization: Optional[str] = Field(None, max_length=100, description="Specialization")
    experience_years: Optional[int] = Field(None, ge=0, description="Experience in years")
    hourly_rate: Optional[float] = Field(None, ge=0, description="Hourly rate")
    daily_rate: Optional[float] = Field(None, ge=0, description="Daily rate")
    currency: Optional[str] = Field(None, max_length=3, description="Currency")

    skills: Optional[List[str]] = Field(None, description="Skills")
    certifications: Optional[List[Dict[str, Any]]] = Field(None, description="Certifications")
    security_clearance: Optional[str] = Field(None, max_length=50, description="Security clearance")

    status: Optional[str] = Field(None, max_length=20, description="Contractor status")
    availability_status: Optional[str] = Field(None, max_length=20, description="Availability status")
    preferred_work_locations: Optional[List[str]] = Field(None, description="Preferred work locations")

    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class ContractorResponse(BaseModel):
    """Contractor response model"""
    id: int
    vendor_id: Optional[int]
    contractor_code: str
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    
    # Personal information
    date_of_birth: Optional[datetime]
    national_id: Optional[str]
    passport_number: Optional[str]
    work_permit_number: Optional[str]
    work_permit_expiry: Optional[datetime]
    
    # Professional information
    job_title: Optional[str]
    specialization: Optional[str]
    experience_years: int
    hourly_rate: Optional[float]
    daily_rate: Optional[float]
    currency: Optional[str]
    
    # Skills and certifications
    skills: Optional[List[str]]
    certifications: Optional[List[Dict[str, Any]]]
    security_clearance: Optional[str]
    
    # Status and availability
    status: str
    availability_status: str
    preferred_work_locations: Optional[List[str]]
    
    # Compliance and background
    background_check_status: str
    background_check_date: Optional[datetime]
    medical_clearance_status: str
    medical_clearance_date: Optional[datetime]
    
    # Vendor info
    vendor_name: Optional[str]
    vendor_code: Optional[str]
    
    # Audit trail
    created_by: int
    created_at: datetime
    updated_by: Optional[int]
    updated_at: datetime
    notes: Optional[str]


class ContractAssignmentCreate(BaseModel):
    """Request to create contract assignment"""
    contract_id: int = Field(..., description="Contract ID")
    contractor_id: int = Field(..., description="Contractor ID")
    personnel_id: Optional[int] = Field(None, description="Personnel ID")
    
    # Assignment details
    project_name: Optional[str] = Field(None, max_length=200, description="Project name")
    project_code: Optional[str] = Field(None, max_length=50, description="Project code")
    role: str = Field(..., min_length=1, max_length=100, description="Role")
    department_id: Optional[int] = Field(None, description="Department ID")
    
    # Assignment dates
    start_date: datetime = Field(..., description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    
    # Financial details
    hourly_rate: Optional[float] = Field(None, ge=0, description="Hourly rate")
    daily_rate: Optional[float] = Field(None, ge=0, description="Daily rate")
    overtime_rate: Optional[float] = Field(None, ge=0, description="Overtime rate")
    currency: Optional[str] = Field("USD", max_length=3, description="Currency")
    
    # Assignment management
    assigned_by: Optional[int] = Field(None, description="Assigned by user ID")
    supervisor_id: Optional[int] = Field(None, description="Supervisor ID")
    
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class ContractAssignmentResponse(BaseModel):
    """Contract assignment response model"""
    id: int
    contract_id: int
    contractor_id: int
    personnel_id: Optional[int]
    
    # Assignment details
    project_name: Optional[str]
    project_code: Optional[str]
    role: str
    department_id: Optional[int]
    
    # Assignment dates
    start_date: datetime
    end_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    
    # Financial details
    hourly_rate: Optional[float]
    daily_rate: Optional[float]
    overtime_rate: Optional[float]
    currency: Optional[str]
    
    # Status tracking
    status: str
    performance_rating: Optional[str]
    completion_status: str
    
    # Assignment management
    assigned_by: Optional[int]
    supervisor_id: Optional[int]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    
    # Related info
    contract_name: Optional[str]
    contract_number: Optional[str]
    contractor_name: Optional[str]
    personnel_name: Optional[str]
    department_name: Optional[str]
    
    # Audit trail
    created_by: int
    created_at: datetime
    updated_by: Optional[int]
    updated_at: datetime
    notes: Optional[str]


class VendorComplianceCreate(BaseModel):
    """Request to create vendor compliance record"""
    vendor_id: int = Field(..., description="Vendor ID")
    compliance_type: str = Field(..., min_length=1, max_length=50, description="Compliance type")
    compliance_status: ComplianceStatus = Field(..., description="Compliance status")
    compliance_date: datetime = Field(..., description="Compliance date")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    certifying_authority: Optional[str] = Field(None, max_length=100, description="Certifying authority")
    certificate_number: Optional[str] = Field(None, max_length=100, description="Certificate number")
    
    # Assessment details
    assessment_score: Optional[float] = Field(None, ge=0, le=100, description="Assessment score")
    assessment_notes: Optional[str] = Field(None, max_length=1000, description="Assessment notes")
    corrective_actions: Optional[List[str]] = Field(None, description="Corrective actions")
    follow_up_date: Optional[datetime] = Field(None, description="Follow-up date")
    
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class VendorComplianceResponse(BaseModel):
    """Vendor compliance response model"""
    id: int
    vendor_id: int
    compliance_type: str
    compliance_status: ComplianceStatus
    compliance_date: datetime
    expiry_date: Optional[datetime]
    certifying_authority: Optional[str]
    certificate_number: Optional[str]
    
    # Assessment details
    assessment_score: Optional[float]
    assessment_notes: Optional[str]
    corrective_actions: Optional[List[str]]
    follow_up_date: Optional[datetime]
    
    # Documents
    certificate_path: Optional[str]
    supporting_documents: Optional[List[str]]
    
    # Vendor info
    vendor_name: Optional[str]
    vendor_code: Optional[str]
    
    # Audit trail
    assessed_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    notes: Optional[str]


class VendorStatisticsResponse(BaseModel):
    """Vendor statistics response model"""
    total_vendors: int
    active_vendors: int
    vendors_by_type: Dict[str, int]
    vendors_by_status: Dict[str, int]
    
    # Contract statistics
    total_contracts: int
    active_contracts: int
    expired_contracts: int
    contracts_by_type: Dict[str, int]
    
    # Contractor statistics
    total_contractors: int
    active_contractors: int
    contractors_by_status: Dict[str, int]
    
    # Compliance statistics
    compliance_overdue: int
    vendors_by_compliance_status: Dict[str, int]
    
    # Performance metrics
    average_vendor_performance: Optional[float]
    top_performing_vendors: List[Dict[str, Any]]


class BulkVendorAction(BaseModel):
    """Bulk vendor action request"""
    vendor_ids: List[int] = Field(..., max_items=50, description="List of vendor IDs")
    action: str = Field(..., description="Action to perform: ACTIVATE, DEACTIVATE, SUSPEND, BLACKLIST")
    reason: Optional[str] = Field(None, max_length=500, description="Action reason")
    notes: Optional[str] = Field(None, max_length=500, description="Action notes")


class BulkVendorResponse(BaseModel):
    """Bulk vendor action response"""
    total_vendors: int
    successful_actions: int
    failed_actions: int
    action_results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class VendorSearchResponse(BaseModel):
    """Vendor search response model"""
    vendors: List[VendorResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
