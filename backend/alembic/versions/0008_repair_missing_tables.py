"""Create the tables an incomplete baseline failed to build

The alembic baseline referenced 48 enum types it never defined, so every table
with an enum column failed to create — 16 of them, including the whole payroll
core, onboarding, certifications, resignations and custom attributes. The
baseline itself is now fixed; databases already seeded from the broken version
need the tables adding.

Idempotent throughout: a database built from database/init/complete_schema.sql,
or from the repaired baseline, already has all of this and is untouched.

Revision ID: 0008_repair_missing_tables
Revises: 0007_personnel_schema_drift
Create Date: 2026-08-29
"""
from alembic import op

revision = "0008_repair_missing_tables"
down_revision = "0007_personnel_schema_drift"
branch_labels = None
depends_on = None

# Enum definitions the tables below depend on. Guarded, because Postgres has no
# CREATE TYPE IF NOT EXISTS.
_ENUMS = {'appraisalstatus': "'DRAFT', 'SUBMITTED', 'IN_PROGRESS', 'COMPLETED', 'APPROVED', 'REJECTED'", 'assignmentstatus': "'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'ERROR'", 'attributetype': "'TEXT', 'NUMBER', 'DATE', 'BOOLEAN', 'SELECT', 'MULTI_SELECT', 'FILE', 'EMAIL', 'PHONE', 'URL'", 'benefiteligibility': "'ALL_EMPLOYEES', 'FULL_TIME_ONLY', 'PART_TIME_ONLY', 'PER_DEPARTMENT', 'PER_POSITION', 'TENURE_BASED', 'SALARY_BASED'", 'benefittype': "'HEALTH_INSURANCE', 'DENTAL_INSURANCE', 'VISION_INSURANCE', 'LIFE_INSURANCE', 'RETIREMENT_401K', 'RETIREMENT_PENSION', 'PAID_TIME_OFF', 'SICK_LEAVE', 'MATERNITY_LEAVE', 'PATERNITY_LEAVE', 'DISABILITY_INSURANCE', 'TUITION_REIMBURSEMENT', 'GYM_MEMBERSHIP', 'TRANSPORTATION', 'HOUSING_ALLOWANCE', 'MEAL_ALLOWANCE', 'OTHER'", 'certificationstatus': "'ACTIVE', 'EXPIRED', 'SUSPENDED', 'REVOKED'", 'certificationtype': "'OPITO', 'NOPSEMA', 'COMPANY', 'OTHER'", 'companytype': "'HOLDING', 'SUBSIDIARY', 'BRANCH'", 'compliancestatus': "'COMPLIANT', 'PENDING_REVIEW', 'NON_COMPLIANT', 'EXPIRED', 'SUSPENDED'", 'contractstatus': "'DRAFT', 'ACTIVE', 'EXPIRED', 'TERMINATED', 'SUSPENDED', 'RENEWED'", 'contracttype': "'PERMANENT', 'FIXED_TERM', 'CONTRACTOR', 'INTERN', 'APPRENTICE', 'TEMPORARY'", 'departmentstatus': "'ACTIVE', 'INACTIVE', 'TEMPORARY', 'UNDER_REVIEW'", 'departmenttype': "'OPERATIONS', 'MAINTENANCE', 'SAFETY', 'SECURITY', 'ADMINISTRATION', 'LOGISTICS', 'TECHNICAL', 'MEDICAL', 'TRAINING', 'CONTRACTOR', 'MANAGEMENT', 'SUPPORT'", 'devicestatus': "'ONLINE', 'OFFLINE', 'MAINTENANCE', 'ERROR', 'DISCONNECTED'", 'devicetype': "'BIOMETRIC_READER', 'CARD_READER', 'TURNSTILE', 'DOOR_CONTROLLER', 'GATE_CONTROLLER'", 'disciplinaryactiontype': "'VERBAL_WARNING', 'WRITTEN_WARNING', 'FINAL_WARNING', 'SUSPENSION', 'DEMOTION', 'TERMINATION', 'OTHER'", 'disciplinarystatus': "'OPEN', 'UNDER_INVESTIGATION', 'HEARING_SCHEDULED', 'CLOSED', 'APPEALED', 'RESOLVED'", 'leavestatus': "'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'ON_LEAVE', 'COMPLETED'", 'leavetype': "'ANNUAL', 'SICK', 'MATERNITY', 'PATERNITY', 'UNPAID', 'COMPASSIONATE', 'STUDY', 'MILITARY', 'JURY_DUTY', 'FAMILY_CARE', 'PERSONAL', 'OTHER'", 'licensetype': "'TRIAL', 'STANDARD', 'ENTERPRISE'", 'onboardingstatus': "'NOT_STARTED', 'IN_PROGRESS', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'COMPLETED', 'CANCELLED'", 'onboardingtype': "'NEW_HIRE', 'REHIRE', 'INTERNAL_TRANSFER', 'PROMOTION', 'CONTRACT_RENEWAL'", 'overtimecompensation': "'PAY', 'TIME_OFF', 'MIXED'", 'overtimestatus': "'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'PROCESSED'", 'overtimetype': "'DAILY', 'WEEKLY', 'MONTHLY', 'HOLIDAY', 'WEEKEND', 'SPECIAL'", 'paycalcstatus': "'PENDING', 'CALCULATED', 'VERIFIED', 'APPROVED'", 'paycalctype': "'FIXED', 'FORMULA', 'ATTENDANCE'", 'payitemtype': "'EARNING', 'DEDUCTION', 'ATTENDANCE'", 'payloanstatus': "'PENDING', 'ACTIVE', 'COMPLETED', 'CANCELLED'", 'payperiodstatus': "'OPEN', 'CALCULATING', 'CLOSED', 'CANCELLED'", 'paystructuretype': "'MONTHLY', 'DAILY', 'HOURLY'", 'performancerating': "'EXCELLENT', 'VERY_GOOD', 'GOOD', 'SATISFACTORY', 'NEEDS_IMPROVEMENT', 'POOR'", 'personnelstatus': "'ACTIVE', 'INACTIVE', 'ON_LEAVE', 'TRANSIT', 'OFFSHORE', 'ONSHORE'", 'resignationstatus': "'PENDING', 'APPROVED', 'REJECTED', 'PROCESSING', 'COMPLETED', 'CANCELLED'", 'resignationtype': "'VOLUNTARY', 'RETIREMENT', 'TERMINATION', 'CONTRACT_END'", 'shifttype': "'MORNING', 'EVENING', 'NIGHT', 'CUSTOM', 'ROTATING'", 'ssotype': "'LDAP', 'SAML'", 'taskpriority': "'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'", 'tasktype': "'DOCUMENT_UPLOAD', 'TRAINING', 'REVIEW', 'APPROVAL', 'BACKGROUND_CHECK', 'MEDICAL_CHECK', 'ASSET_RETURN', 'SYSTEM_ACCESS'", 'trainingcategory': "'SAFETY', 'TECHNICAL', 'COMPLIANCE', 'SOFT_SKILLS', 'LEADERSHIP', 'INDUCTION', 'REFRESHER', 'CERTIFICATION'", 'trainingstatus': "'ENROLLED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED', 'CERTIFIED'", 'transferstatus': "'PENDING', 'APPROVED', 'REJECTED', 'COMPLETED', 'CANCELLED'", 'transfertype': "'DEPARTMENT', 'LOCATION', 'POSITION', 'ROLE'", 'validationrule': "'REQUIRED', 'OPTIONAL', 'MIN_LENGTH', 'MAX_LENGTH', 'MIN_VALUE', 'MAX_VALUE', 'EMAIL_FORMAT', 'PHONE_FORMAT', 'REGEX_PATTERN'", 'vendorstatus': "'ACTIVE', 'INACTIVE', 'SUSPENDED', 'UNDER_REVIEW', 'BLACKLISTED'", 'vendortype': "'SERVICE_PROVIDER', 'EQUIPMENT_SUPPLIER', 'CONSULTING_FIRM', 'STAFFING_AGENCY', 'TRAINING_PROVIDER', 'SOFTWARE_VENDOR', 'MAINTENANCE_PROVIDER'", 'zonestatus': "'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'EMERGENCY', 'LOCKDOWN'", 'zonetype': "'RESTRICTED', 'PUBLIC', 'SAFE_HAVEN', 'WORK_AREA', 'ACCOMMODATION', 'HELIPAD', 'CONTROL_ROOM', 'STORAGE', 'EMERGENCY'"}


def upgrade():
    for name, values in _ENUMS.items():
        op.execute(
            f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
        )

    op.execute("""
CREATE TABLE IF NOT EXISTS attribute_validations (
    id integer NOT NULL,
    attribute_value_id integer NOT NULL,
    validation_rule validationrule NOT NULL,
    validation_parameters json,
    is_valid boolean,
    error_message text,
    validated_at timestamp with time zone DEFAULT now()
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS base_company (
    id integer NOT NULL,
    company_name character varying(100) NOT NULL,
    address text,
    phone character varying(20),
    email character varying(100),
    logo character varying(255),
    website character varying(100),
    work_days character varying(7),
    timezone character varying(50),
    date_format character varying(20),
    currency character varying(10),
    emergency_contact json,
    evac_map_pdf character varying(255),
    parent_company_id integer,
    company_type companytype,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS certification_templates (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    certification_type certificationtype NOT NULL,
    issuer character varying(255) NOT NULL,
    description text,
    validity_days integer NOT NULL,
    renewal_required boolean,
    requirements text,
    prerequisites text,
    personnel_types character varying(100),
    roles character varying(500),
    locations character varying(500),
    is_mandatory boolean,
    compliance_weight integer,
    expiry_notification_days integer,
    renewal_notification_days integer,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS certifications (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    name character varying(255) NOT NULL,
    certification_type certificationtype,
    issuer character varying(255) NOT NULL,
    certificate_number character varying(100) NOT NULL,
    issue_date timestamp with time zone NOT NULL,
    expire_date timestamp with time zone NOT NULL,
    verified_date timestamp with time zone,
    status certificationstatus,
    verified boolean,
    verification_data text,
    description text,
    requirements text,
    training_provider character varying(255),
    location character varying(255),
    certificate_file character varying(500),
    verification_file character varying(500),
    notes text,
    tags character varying(500),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS custom_attributes (
    id integer NOT NULL,
    attribute_code character varying(50) NOT NULL,
    attribute_name character varying(100) NOT NULL,
    attribute_type attributetype NOT NULL,
    description text,
    validation_rules json,
    default_value json,
    display_options json,
    placeholder_text character varying(100),
    category character varying(50),
    group_name character varying(50),
    sort_order integer,
    is_active boolean,
    is_required boolean,
    is_searchable boolean,
    is_visible_in_list boolean,
    read_permissions json,
    write_permissions json,
    created_by integer,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS onboarding_tasks (
    id integer NOT NULL,
    onboarding_id integer NOT NULL,
    task_name character varying(100) NOT NULL,
    task_type tasktype NOT NULL,
    description text,
    is_required boolean,
    due_date timestamp with time zone,
    priority taskpriority,
    status character varying(20),
    completion_date timestamp with time zone,
    completed_by integer,
    completion_notes text,
    checklist_items json,
    completed_items json,
    depends_on_tasks json,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS onboarding_templates (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    template_code character varying(50) NOT NULL,
    onboarding_type onboardingtype NOT NULL,
    description text,
    default_tasks json NOT NULL,
    required_documents json,
    approval_workflow json,
    default_duration_days integer,
    reminder_settings json,
    is_active boolean,
    is_default boolean,
    usage_count integer,
    last_used timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS onboardings (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    onboarding_type onboardingtype NOT NULL,
    status onboardingstatus,
    start_date timestamp with time zone NOT NULL,
    planned_end_date timestamp with time zone NOT NULL,
    actual_end_date timestamp with time zone,
    job_title character varying(200) NOT NULL,
    job_description text,
    department_id integer,
    position_id integer,
    reporting_to integer,
    buddy_id integer,
    manager_id integer,
    template_id integer,
    template_data json,
    custom_fields json,
    completion_percentage double precision,
    last_progress_update timestamp with time zone,
    submitted_at timestamp with time zone,
    reviewed_by integer,
    reviewed_at timestamp with time zone,
    approved_by integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    completed_at timestamp with time zone,
    completed_by integer,
    exit_interview_date timestamp with time zone,
    exit_interview_conducted_by integer,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS pay_item (
    id integer NOT NULL,
    structure_id integer NOT NULL,
    item_name character varying(50) NOT NULL,
    item_type payitemtype NOT NULL,
    calc_type paycalctype,
    amount numeric(10,2),
    formula text,
    attendance_field character varying(50),
    rate numeric(10,4),
    sequence integer,
    is_taxable boolean,
    is_print boolean,
    is_mandatory boolean,
    gl_account character varying(50),
    created_at timestamp with time zone DEFAULT now()
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS pay_loan (
    id integer NOT NULL,
    emp_id integer NOT NULL,
    loan_type character varying(50),
    loan_amount numeric(10,2) NOT NULL,
    emi_amount numeric(10,2) NOT NULL,
    interest_rate numeric(5,2),
    start_date date NOT NULL,
    end_date date NOT NULL,
    balance numeric(10,2) NOT NULL,
    status payloanstatus,
    reason character varying(255),
    approved_by integer,
    approved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS pay_period (
    id integer NOT NULL,
    period_name character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    pay_date date,
    status payperiodstatus,
    is_att_locked boolean,
    description text,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    closed_at timestamp with time zone,
    closed_by integer
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS pay_salary (
    id bigint NOT NULL,
    period_id integer NOT NULL,
    emp_id integer NOT NULL,
    structure_id integer,
    basic_salary numeric(10,2),
    work_days numeric(5,2),
    present_days numeric(5,2),
    ot_hours numeric(5,2),
    late_minutes integer,
    leave_days numeric(5,2),
    absent_days numeric(5,2),
    gross_salary numeric(10,2),
    total_earnings numeric(10,2),
    total_deductions numeric(10,2),
    net_salary numeric(10,2),
    is_final boolean,
    calc_status paycalcstatus,
    calc_time timestamp with time zone DEFAULT now(),
    calc_by integer,
    verified_by integer,
    verified_at timestamp with time zone,
    approved_by integer,
    approved_at timestamp with time zone,
    zone_hours numeric(5,2),
    night_hours numeric(5,2),
    hazard_days numeric(5,2),
    contractor_flag boolean
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS pay_salary_item (
    id bigint NOT NULL,
    salary_id bigint NOT NULL,
    item_id integer,
    item_name character varying(50) NOT NULL,
    item_value numeric(10,2),
    item_type payitemtype NOT NULL,
    formula_used text,
    source_value numeric(10,2),
    calculation_order integer,
    is_manual_adjustment boolean,
    adjustment_reason text,
    created_at timestamp with time zone DEFAULT now()
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS pay_structure (
    id integer NOT NULL,
    structure_name character varying(100) NOT NULL,
    structure_type paystructuretype,
    is_active boolean,
    version integer,
    effective_date date,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by integer
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS resignation_templates (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    template_code character varying(20) NOT NULL,
    resignation_type resignationtype NOT NULL,
    default_tasks json NOT NULL,
    required_documents json,
    approval_workflow json,
    notification_settings json,
    description text,
    is_active boolean,
    is_default boolean,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
    """)

    op.execute("""
CREATE TABLE IF NOT EXISTS resignations (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    resignation_type resignationtype NOT NULL,
    status resignationstatus,
    resignation_date timestamp with time zone NOT NULL,
    last_working_day timestamp with time zone NOT NULL,
    reason text NOT NULL,
    detailed_reason text,
    exit_interview_date timestamp with time zone,
    exit_interview_conducted_by integer,
    exit_interview_notes text,
    handover_completed boolean,
    handover_date timestamp with time zone,
    handover_conducted_by integer,
    handover_notes text,
    handover_checklist json,
    financial_clearance_completed boolean,
    financial_clearance_date timestamp with time zone,
    financial_clearance_conducted_by integer,
    financial_clearance_notes text,
    assets_returned boolean,
    assets_return_date timestamp with time zone,
    assets_return_conducted_by integer,
    assets_return_notes text,
    assets_return_checklist json,
    system_access_revoked boolean,
    system_access_revoked_date timestamp with time zone,
    system_access_revoked_by integer,
    device_access_removed boolean,
    approved_by integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    completed_at timestamp with time zone,
    completed_by integer,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);
    """)


def downgrade():
    # Not dropped: these tables are core to the application, and their absence
    # is the defect being repaired rather than a state worth returning to.
    pass
