-- ENUM TYPES (added to the baseline: these were defined only in
-- database/init/complete_schema.sql, so an alembic-seeded database failed to
-- create the 16 tables that reference them — payroll, onboarding,
-- certifications, resignations and custom attributes among them.)

DO $$ BEGIN
    CREATE TYPE appraisalstatus AS ENUM ('DRAFT', 'SUBMITTED', 'IN_PROGRESS', 'COMPLETED', 'APPROVED', 'REJECTED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE assignmentstatus AS ENUM ('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'ERROR');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE attributetype AS ENUM ('TEXT', 'NUMBER', 'DATE', 'BOOLEAN', 'SELECT', 'MULTI_SELECT', 'FILE', 'EMAIL', 'PHONE', 'URL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE benefiteligibility AS ENUM ('ALL_EMPLOYEES', 'FULL_TIME_ONLY', 'PART_TIME_ONLY', 'PER_DEPARTMENT', 'PER_POSITION', 'TENURE_BASED', 'SALARY_BASED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE benefittype AS ENUM ('HEALTH_INSURANCE', 'DENTAL_INSURANCE', 'VISION_INSURANCE', 'LIFE_INSURANCE', 'RETIREMENT_401K', 'RETIREMENT_PENSION', 'PAID_TIME_OFF', 'SICK_LEAVE', 'MATERNITY_LEAVE', 'PATERNITY_LEAVE', 'DISABILITY_INSURANCE', 'TUITION_REIMBURSEMENT', 'GYM_MEMBERSHIP', 'TRANSPORTATION', 'HOUSING_ALLOWANCE', 'MEAL_ALLOWANCE', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE certificationstatus AS ENUM ('ACTIVE', 'EXPIRED', 'SUSPENDED', 'REVOKED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE certificationtype AS ENUM ('OPITO', 'NOPSEMA', 'COMPANY', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE companytype AS ENUM ('HOLDING', 'SUBSIDIARY', 'BRANCH');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE compliancestatus AS ENUM ('COMPLIANT', 'PENDING_REVIEW', 'NON_COMPLIANT', 'EXPIRED', 'SUSPENDED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE contractstatus AS ENUM ('DRAFT', 'ACTIVE', 'EXPIRED', 'TERMINATED', 'SUSPENDED', 'RENEWED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE contracttype AS ENUM ('PERMANENT', 'FIXED_TERM', 'CONTRACTOR', 'INTERN', 'APPRENTICE', 'TEMPORARY');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE departmentstatus AS ENUM ('ACTIVE', 'INACTIVE', 'TEMPORARY', 'UNDER_REVIEW');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE departmenttype AS ENUM ('OPERATIONS', 'MAINTENANCE', 'SAFETY', 'SECURITY', 'ADMINISTRATION', 'LOGISTICS', 'TECHNICAL', 'MEDICAL', 'TRAINING', 'CONTRACTOR', 'MANAGEMENT', 'SUPPORT');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE devicestatus AS ENUM ('ONLINE', 'OFFLINE', 'MAINTENANCE', 'ERROR', 'DISCONNECTED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE devicetype AS ENUM ('BIOMETRIC_READER', 'CARD_READER', 'TURNSTILE', 'DOOR_CONTROLLER', 'GATE_CONTROLLER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE disciplinaryactiontype AS ENUM ('VERBAL_WARNING', 'WRITTEN_WARNING', 'FINAL_WARNING', 'SUSPENSION', 'DEMOTION', 'TERMINATION', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE disciplinarystatus AS ENUM ('OPEN', 'UNDER_INVESTIGATION', 'HEARING_SCHEDULED', 'CLOSED', 'APPEALED', 'RESOLVED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE leavestatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'ON_LEAVE', 'COMPLETED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE leavetype AS ENUM ('ANNUAL', 'SICK', 'MATERNITY', 'PATERNITY', 'UNPAID', 'COMPASSIONATE', 'STUDY', 'MILITARY', 'JURY_DUTY', 'FAMILY_CARE', 'PERSONAL', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE licensetype AS ENUM ('TRIAL', 'STANDARD', 'ENTERPRISE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE onboardingstatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE onboardingtype AS ENUM ('NEW_HIRE', 'REHIRE', 'INTERNAL_TRANSFER', 'PROMOTION', 'CONTRACT_RENEWAL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE overtimecompensation AS ENUM ('PAY', 'TIME_OFF', 'MIXED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE overtimestatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'PROCESSED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE overtimetype AS ENUM ('DAILY', 'WEEKLY', 'MONTHLY', 'HOLIDAY', 'WEEKEND', 'SPECIAL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE paycalcstatus AS ENUM ('PENDING', 'CALCULATED', 'VERIFIED', 'APPROVED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE paycalctype AS ENUM ('FIXED', 'FORMULA', 'ATTENDANCE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE payitemtype AS ENUM ('EARNING', 'DEDUCTION', 'ATTENDANCE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE payloanstatus AS ENUM ('PENDING', 'ACTIVE', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE payperiodstatus AS ENUM ('OPEN', 'CALCULATING', 'CLOSED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE paystructuretype AS ENUM ('MONTHLY', 'DAILY', 'HOURLY');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE performancerating AS ENUM ('EXCELLENT', 'VERY_GOOD', 'GOOD', 'SATISFACTORY', 'NEEDS_IMPROVEMENT', 'POOR');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE personnelstatus AS ENUM ('ACTIVE', 'INACTIVE', 'ON_LEAVE', 'TRANSIT', 'OFFSHORE', 'ONSHORE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE resignationstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'PROCESSING', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE resignationtype AS ENUM ('VOLUNTARY', 'RETIREMENT', 'TERMINATION', 'CONTRACT_END');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE shifttype AS ENUM ('MORNING', 'EVENING', 'NIGHT', 'CUSTOM', 'ROTATING');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE ssotype AS ENUM ('LDAP', 'SAML');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE taskpriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE tasktype AS ENUM ('DOCUMENT_UPLOAD', 'TRAINING', 'REVIEW', 'APPROVAL', 'BACKGROUND_CHECK', 'MEDICAL_CHECK', 'ASSET_RETURN', 'SYSTEM_ACCESS');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE trainingcategory AS ENUM ('SAFETY', 'TECHNICAL', 'COMPLIANCE', 'SOFT_SKILLS', 'LEADERSHIP', 'INDUCTION', 'REFRESHER', 'CERTIFICATION');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE trainingstatus AS ENUM ('ENROLLED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED', 'CERTIFIED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE transferstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE transfertype AS ENUM ('DEPARTMENT', 'LOCATION', 'POSITION', 'ROLE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE validationrule AS ENUM ('REQUIRED', 'OPTIONAL', 'MIN_LENGTH', 'MAX_LENGTH', 'MIN_VALUE', 'MAX_VALUE', 'EMAIL_FORMAT', 'PHONE_FORMAT', 'REGEX_PATTERN');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE vendorstatus AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'UNDER_REVIEW', 'BLACKLISTED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE vendortype AS ENUM ('SERVICE_PROVIDER', 'EQUIPMENT_SUPPLIER', 'CONSULTING_FIRM', 'STAFFING_AGENCY', 'TRAINING_PROVIDER', 'SOFTWARE_VENDOR', 'MAINTENANCE_PROVIDER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE zonestatus AS ENUM ('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'EMERGENCY', 'LOCKDOWN');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE zonetype AS ENUM ('RESTRICTED', 'PUBLIC', 'SAFE_HAVEN', 'WORK_AREA', 'ACCOMMODATION', 'HELIPAD', 'CONTROL_ROOM', 'STORAGE', 'EMERGENCY');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- POB System complete schema — 232 tables
-- Generated 2026-06-06 from live database
-- All CREATE statements use IF NOT EXISTS for safe re-runs

CREATE TABLE IF NOT EXISTS acc_antipassback (
    id bigint NOT NULL,
    emp_code character varying(20) NOT NULL,
    door_id integer NOT NULL,
    last_event_time timestamp with time zone NOT NULL,
    last_event_type smallint NOT NULL,
    last_terminal_sn character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_antipassback_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_door (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    terminal_sn character varying(20),
    acc_level_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    mustering_mode boolean DEFAULT false,
    emergency_action smallint DEFAULT 0,
    relay_time integer DEFAULT 5,
    door_sensor_type smallint DEFAULT 0,
    alarm_delay integer DEFAULT 30,
    open_duration integer DEFAULT 15,
    anti_passback smallint DEFAULT 0,
    first_card_open boolean DEFAULT false,
    interlock_group integer DEFAULT 0,
    fire_linkage boolean DEFAULT false
);

CREATE SEQUENCE IF NOT EXISTS acc_door_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_event (
    id bigint NOT NULL,
    event_time timestamp with time zone NOT NULL,
    terminal_sn character varying(20) NOT NULL,
    door_id integer,
    emp_code character varying(20),
    emp_name character varying(50),
    event_type smallint NOT NULL,
    verify_type smallint,
    in_out smallint,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    photo_url text
);

CREATE SEQUENCE IF NOT EXISTS acc_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_first_card (
    id bigint NOT NULL,
    door_id integer NOT NULL,
    timezone_id integer NOT NULL,
    first_card_time timestamp with time zone NOT NULL,
    emp_code character varying(20) NOT NULL,
    zone_end_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_first_card_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_guard_tour (
    id integer NOT NULL,
    tour_name character varying(100) NOT NULL,
    description text,
    interval_minutes integer DEFAULT 60,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS acc_guard_tour_checkpoint (
    id integer NOT NULL,
    tour_id integer,
    door_id integer,
    sequence_order integer NOT NULL,
    time_window_minutes integer DEFAULT 10,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_guard_tour_checkpoint_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS acc_guard_tour_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_guard_tour_log (
    id bigint NOT NULL,
    schedule_id integer,
    checkpoint_id integer,
    emp_code character varying(20),
    scan_time timestamp with time zone NOT NULL,
    is_on_time boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_guard_tour_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_guard_tour_schedule (
    id integer NOT NULL,
    tour_id integer,
    guard_emp_code character varying(20),
    guard_name character varying(100),
    scheduled_start timestamp with time zone NOT NULL,
    scheduled_end timestamp with time zone,
    status character varying(20) DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_guard_tour_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_interlock_door (
    id integer NOT NULL,
    group_id integer NOT NULL,
    door_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_interlock_door_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_interlock_group (
    id integer NOT NULL,
    group_name character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_interlock_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_level (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    time_zone character varying(50) DEFAULT 'UTC'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    mustering_only boolean DEFAULT false,
    is_active boolean DEFAULT true
);

CREATE TABLE IF NOT EXISTS acc_level_door (
    id integer NOT NULL,
    level_id integer NOT NULL,
    door_id integer NOT NULL,
    timezone_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_level_door_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS acc_level_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_linkage (
    id integer NOT NULL,
    terminal_sn character varying(20) NOT NULL,
    input_type smallint,
    output_action smallint,
    output_door_id integer,
    output_terminal_sn character varying(20),
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_linkage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_multi_card (
    id integer NOT NULL,
    door_id integer,
    min_cards smallint DEFAULT 2 NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_multi_card_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_multi_card_user (
    id integer NOT NULL,
    multi_card_id integer NOT NULL,
    emp_code character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_multi_card_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_passback_rule (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    in_door_id integer,
    out_door_id integer,
    mode smallint,
    is_active boolean,
    description text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_passback_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_timezone (
    id integer NOT NULL,
    timezone_name character varying(50) NOT NULL,
    sun_time1 character varying(11),
    sun_time2 character varying(11),
    sun_time3 character varying(11),
    mon_time1 character varying(11),
    mon_time2 character varying(11),
    mon_time3 character varying(11),
    tue_time1 character varying(11),
    tue_time2 character varying(11),
    tue_time3 character varying(11),
    wed_time1 character varying(11),
    wed_time2 character varying(11),
    wed_time3 character varying(11),
    thu_time1 character varying(11),
    thu_time2 character varying(11),
    thu_time3 character varying(11),
    fri_time1 character varying(11),
    fri_time2 character varying(11),
    fri_time3 character varying(11),
    sat_time1 character varying(11),
    sat_time2 character varying(11),
    sat_time3 character varying(11),
    hol1_time1 character varying(11),
    hol1_time2 character varying(11),
    hol1_time3 character varying(11),
    hol2_time1 character varying(11),
    hol2_time2 character varying(11),
    hol2_time3 character varying(11),
    hol3_time1 character varying(11),
    hol3_time2 character varying(11),
    hol3_time3 character varying(11),
    emergency_override boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acc_timezone_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_userauthorize (
    id integer NOT NULL,
    emp_code character varying(20) NOT NULL,
    acc_level_id integer,
    start_time time without time zone,
    end_time time without time zone,
    valid_days character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    valid_from date,
    valid_to date
);

CREATE SEQUENCE IF NOT EXISTS acc_userauthorize_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_visitor_access (
    id integer NOT NULL,
    visitor_name character varying(100),
    visitor_company character varying(100),
    visitor_phone character varying(20),
    host_emp_code character varying(20),
    host_name character varying(100),
    acc_level_id integer,
    card_number character varying(50),
    valid_from timestamp with time zone NOT NULL,
    valid_to timestamp with time zone NOT NULL,
    purpose text,
    status character varying(20) DEFAULT 'active'::character varying,
    created_by_username character varying(150),
    created_at timestamp with time zone DEFAULT now(),
    emp_code character varying(20),
    note text,
    door_ids jsonb DEFAULT '[]'::jsonb,
    is_revoked boolean DEFAULT false,
    level_id integer
);

CREATE SEQUENCE IF NOT EXISTS acc_visitor_access_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acc_zone (
    id integer NOT NULL,
    zone_name character varying(100) NOT NULL,
    description text,
    is_mustering_zone boolean DEFAULT false,
    capacity integer,
    created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS acc_zone_door (
    id integer NOT NULL,
    zone_id integer,
    door_id integer,
    direction smallint DEFAULT 0
);

CREATE SEQUENCE IF NOT EXISTS acc_zone_door_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS acc_zone_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS access_logs (
    id integer NOT NULL,
    personnel_id integer,
    device_id character varying(100),
    event_type character varying(50) NOT NULL,
    access_granted boolean NOT NULL,
    access_method character varying(50),
    "timestamp" timestamp with time zone NOT NULL,
    duration integer,
    biometric_data json,
    denial_reason character varying(255),
    error_code character varying(50),
    zone_id integer,
    notes text,
    verification_method character varying(50),
    ip_address character varying(45),
    user_agent character varying(500),
    direction character varying(10),
    CONSTRAINT access_logs_direction_check CHECK (((direction)::text = ANY ((ARRAY['ENTRY'::character varying, 'EXIT'::character varying])::text[])))
);

CREATE SEQUENCE IF NOT EXISTS access_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS acgroup (
    id integer NOT NULL,
    group_name character varying(50) NOT NULL,
    description text,
    parent_id integer,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS acgroup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS appraisal_cycles (
    id integer NOT NULL,
    cycle_name character varying(100) NOT NULL,
    cycle_code character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying,
    description text,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS appraisal_cycles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_exception (
    id integer NOT NULL,
    emp_id integer,
    att_date date NOT NULL,
    exception_type character varying(50) NOT NULL,
    deviation_minutes integer DEFAULT 0,
    exception_note text,
    department_id integer,
    handled_at timestamp with time zone,
    handle_action character varying(50),
    handle_note text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS att_exception_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_holiday (
    id integer NOT NULL,
    holiday_name character varying(100) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    holiday_type smallint DEFAULT 0,
    description text,
    area_id integer,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true NOT NULL
);

CREATE SEQUENCE IF NOT EXISTS att_holiday_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_leave (
    id integer NOT NULL,
    emp_id integer NOT NULL,
    leave_type_id integer,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    reason text,
    apply_time timestamp with time zone DEFAULT now(),
    approval_status smallint DEFAULT 0,
    approver_id integer,
    approved_at timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS att_leave_old (
    id integer NOT NULL,
    emp_code character varying(20) NOT NULL,
    leave_type character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    days_count double precision DEFAULT 0,
    status smallint DEFAULT 0,
    approved_by character varying(20),
    approved_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS att_leave_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS att_leave_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_leave_type (
    id integer NOT NULL,
    leave_name character varying(100) NOT NULL,
    unit smallint DEFAULT 0,
    accrual_rule text,
    affects_mustering boolean DEFAULT true,
    max_days_per_year numeric(6,2),
    requires_approval boolean DEFAULT true,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true
);

CREATE SEQUENCE IF NOT EXISTS att_leave_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_manual_log (
    id integer NOT NULL,
    emp_id integer NOT NULL,
    punch_time timestamp with time zone NOT NULL,
    punch_state smallint DEFAULT 0,
    reason text,
    attachment character varying(255),
    apply_time timestamp with time zone DEFAULT now(),
    approval_status smallint DEFAULT 0,
    approver_id integer,
    approved_at timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS att_manual_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_overtime (
    id integer NOT NULL,
    emp_id integer NOT NULL,
    ot_date date NOT NULL,
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    minutes integer DEFAULT 0 NOT NULL,
    reason text,
    apply_time timestamp with time zone DEFAULT now(),
    approval_status smallint DEFAULT 0,
    approver_id integer,
    approved_at timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    overtime_type character varying(20) DEFAULT 'daily'::character varying,
    hours_worked numeric(5,2),
    overtime_hours numeric(5,2),
    compensation_type character varying(20),
    rejection_reason text
);

CREATE SEQUENCE IF NOT EXISTS att_overtime_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_overtime_rule (
    id integer NOT NULL,
    rule_name character varying(100) NOT NULL,
    ot_type smallint DEFAULT 0,
    min_minutes integer DEFAULT 30,
    rate numeric(4,2) DEFAULT 1.5,
    area_id integer,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true
);

CREATE SEQUENCE IF NOT EXISTS att_overtime_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_report (
    id integer NOT NULL,
    emp_id integer NOT NULL,
    att_date date NOT NULL,
    shift_id integer,
    timetable_id integer,
    check_in timestamp with time zone,
    check_out timestamp with time zone,
    work_hours numeric(6,2) DEFAULT 0,
    work_minutes integer DEFAULT 0,
    late_minutes integer DEFAULT 0,
    early_minutes integer DEFAULT 0,
    ot_minutes integer DEFAULT 0,
    att_status smallint DEFAULT 0,
    exception_count integer DEFAULT 0,
    area_compliance boolean DEFAULT true,
    department_id integer,
    scheduled_minutes integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    overtime_minutes integer DEFAULT 0
);

CREATE SEQUENCE IF NOT EXISTS att_report_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_rules (
    rule_key character varying(100) NOT NULL,
    rule_value text,
    updated_by integer,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS att_schedule (
    id integer NOT NULL,
    emp_code character varying(20) NOT NULL,
    shift_id integer,
    start_date date NOT NULL,
    end_date date,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    status character varying(20) DEFAULT 'scheduled'::character varying,
    notes text
);

CREATE SEQUENCE IF NOT EXISTS att_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_shift (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    timetable_id integer,
    days_of_week character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    alias character varying(100),
    work_days character varying(20) DEFAULT '12345'::character varying,
    cycle_unit smallint DEFAULT 1,
    cycle_count smallint DEFAULT 1,
    roster_type smallint DEFAULT 0,
    created_by integer,
    shift_code character varying(20),
    shift_type character varying(20) DEFAULT 'CUSTOM'::character varying,
    start_time time without time zone,
    end_time time without time zone,
    break_duration integer DEFAULT 0,
    working_hours integer DEFAULT 8,
    is_night_shift boolean DEFAULT false,
    is_weekend_shift boolean DEFAULT false,
    is_flexible boolean DEFAULT false,
    rotation_pattern jsonb,
    rotation_cycle_days integer,
    grace_period_minutes integer DEFAULT 15,
    max_late_minutes integer DEFAULT 60,
    max_early_departure_minutes integer DEFAULT 30,
    overtime_threshold_minutes integer DEFAULT 30,
    description text,
    is_active boolean DEFAULT true
);

CREATE SEQUENCE IF NOT EXISTS att_shift_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_shift_timetable (
    id integer NOT NULL,
    shift_id integer NOT NULL,
    day_of_week smallint NOT NULL,
    timetable_id integer NOT NULL
);

CREATE SEQUENCE IF NOT EXISTS att_shift_timetable_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS att_timetable (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    late_grace_minutes integer DEFAULT 0,
    early_exit_minutes integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    alias character varying(100),
    work_day numeric(4,2) DEFAULT 1.0,
    color character varying(20) DEFAULT '#1890ff'::character varying,
    break_time_start time without time zone,
    break_time_end time without time zone,
    must_checkin boolean DEFAULT true,
    must_checkout boolean DEFAULT true,
    area_id integer,
    created_by integer,
    updated_by integer,
    is_active boolean DEFAULT true
);

CREATE SEQUENCE IF NOT EXISTS att_timetable_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS attendance_logs (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    device_id character varying(50),
    event_type character varying(20) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    verification_method character varying(50),
    verification_score double precision,
    device_type character varying(50),
    network_type character varying(20),
    raw_data jsonb,
    is_processed boolean DEFAULT false,
    processed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE IF NOT EXISTS attendance_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS attribute_templates (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    template_code character varying(50) NOT NULL,
    description text,
    attributes json NOT NULL,
    category character varying(50),
    is_system_template boolean,
    is_active boolean,
    usage_count integer,
    last_used timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS attribute_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS attribute_validations (
    id integer NOT NULL,
    attribute_value_id integer NOT NULL,
    validation_rule validationrule NOT NULL,
    validation_parameters json,
    is_valid boolean,
    error_message text,
    validated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS attribute_validations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS auth_permission (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    codename character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS auth_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS auth_role (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS auth_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS auth_role_permission (
    id integer NOT NULL,
    role_id integer NOT NULL,
    permission_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS auth_role_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS auth_user (
    id integer NOT NULL,
    username character varying(150) NOT NULL,
    password character varying(128) NOT NULL,
    email character varying(100),
    first_name character varying(50),
    last_name character varying(50),
    is_superuser boolean DEFAULT false,
    is_active boolean DEFAULT true,
    last_login timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_global_admin boolean DEFAULT false
);

CREATE SEQUENCE IF NOT EXISTS auth_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS auth_user_role (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS auth_user_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS base_company_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS base_operationlog (
    id bigint NOT NULL,
    user_id integer,
    action character varying(50) NOT NULL,
    table_name character varying(50),
    record_id integer,
    old_values text,
    new_values text,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS base_operationlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS benefit_plans (
    id integer NOT NULL,
    plan_code character varying(20) NOT NULL,
    plan_name character varying(100) NOT NULL,
    benefit_type character varying(50) NOT NULL,
    description text,
    eligibility character varying(20) DEFAULT 'all_employees'::character varying,
    employer_contribution numeric(5,2),
    employee_contribution numeric(5,2),
    max_coverage numeric(10,2),
    currency character varying(3) DEFAULT 'USD'::character varying,
    enrollment_period_start date,
    enrollment_period_end date,
    effective_date date,
    is_active boolean DEFAULT true,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS benefit_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biometric_devices (
    id integer NOT NULL,
    device_serial character varying(50) NOT NULL,
    device_name character varying(100) NOT NULL,
    device_type character varying(20) NOT NULL,
    manufacturer character varying(50),
    model character varying(50),
    firmware_version character varying(20),
    ip_address character varying(15),
    port integer,
    communication_key character varying(50),
    supported_templates json,
    max_templates_per_user integer,
    enrollment_quality_threshold double precision,
    is_online boolean,
    is_active boolean,
    last_heartbeat timestamp with time zone,
    configuration json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_sync timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS biometric_devices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biometric_enrollment_sessions (
    id integer NOT NULL,
    session_id character varying(100) NOT NULL,
    personnel_id integer NOT NULL,
    template_type character varying(20) NOT NULL,
    device_serial character varying(50),
    status character varying(20),
    progress_percentage double precision,
    current_step character varying(50),
    templates_collected integer,
    templates_required integer,
    quality_threshold double precision,
    error_message text,
    retry_count integer,
    max_retries integer,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    last_activity timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biometric_enrollment_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biometric_templates (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    template_type character varying(20) NOT NULL,
    template_data text NOT NULL,
    template_quality double precision,
    finger_index integer,
    hand character varying(10),
    device_serial character varying(50),
    enrollment_method character varying(20),
    is_active boolean,
    is_verified boolean,
    verification_count integer,
    last_used timestamp with time zone,
    enrolled_by integer,
    enrolled_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS biometric_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biometric_verification_logs (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    template_type character varying(20) NOT NULL,
    device_serial character varying(50),
    is_successful boolean NOT NULL,
    confidence_score double precision,
    response_time_ms integer,
    verification_method character varying(20),
    template_used integer,
    error_code character varying(20),
    error_message text,
    location character varying(100),
    purpose character varying(50),
    verified_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biometric_verification_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biotime_access_levels (
    id integer NOT NULL,
    level_name character varying(100) NOT NULL,
    level_code character varying(20) NOT NULL,
    priority integer NOT NULL,
    time_restrictions json,
    location_restrictions json,
    device_restrictions json,
    required_biometric_types json,
    min_biometric_quality double precision,
    multi_factor_required boolean DEFAULT false,
    access_permissions json,
    door_permissions json,
    area_permissions json,
    personnel_ids json NOT NULL,
    device_group_ids json NOT NULL,
    biotime_access_level_id character varying(100),
    biotime_configuration json,
    biotime_last_sync timestamp with time zone,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biotime_access_levels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biotime_access_schedules (
    id integer NOT NULL,
    schedule_name character varying(100) NOT NULL,
    schedule_type character varying(20) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    monday_enabled boolean DEFAULT true,
    tuesday_enabled boolean DEFAULT true,
    wednesday_enabled boolean DEFAULT true,
    thursday_enabled boolean DEFAULT true,
    friday_enabled boolean DEFAULT true,
    saturday_enabled boolean DEFAULT false,
    sunday_enabled boolean DEFAULT false,
    monday_start_time character varying(5),
    monday_end_time character varying(5),
    tuesday_start_time character varying(5),
    tuesday_end_time character varying(5),
    wednesday_start_time character varying(5),
    wednesday_end_time character varying(5),
    thursday_start_time character varying(5),
    thursday_end_time character varying(5),
    friday_start_time character varying(5),
    friday_end_time character varying(5),
    saturday_start_time character varying(5),
    saturday_end_time character varying(5),
    sunday_start_time character varying(5),
    sunday_end_time character varying(5),
    personnel_ids json NOT NULL,
    device_group_ids json NOT NULL,
    access_levels json NOT NULL,
    biotime_schedule_id character varying(100),
    biotime_sync_enabled boolean DEFAULT true,
    biotime_last_sync timestamp with time zone,
    holiday_overrides json,
    emergency_override json,
    temporary_override json,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biotime_access_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biotime_biometric_templates (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    template_type character varying(20) NOT NULL,
    template_id character varying(100) NOT NULL,
    quality_score double precision NOT NULL,
    enrollment_date timestamp with time zone NOT NULL,
    last_used timestamp with time zone,
    device_id character varying(50),
    biotime_template_hash character varying(255),
    template_data json,
    is_active boolean DEFAULT true,
    backup_count integer,
    verification_count integer,
    failure_count integer,
    last_verification_score double precision,
    biotime_template_version character varying(20),
    biotime_device_type character varying(50),
    biotime_enrollment_method character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biotime_biometric_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biotime_conflict_resolutions (
    id integer NOT NULL,
    conflict_id character varying(100) NOT NULL,
    conflict_type character varying(50) NOT NULL,
    conflict_description text NOT NULL,
    detected_at timestamp with time zone NOT NULL,
    resolution_strategy character varying(50) NOT NULL,
    resolution_details json,
    resolved_at timestamp with time zone,
    resolved_by integer,
    impact_level character varying(20) NOT NULL,
    affected_records json,
    prevention_measures json,
    biotime_conflict_id character varying(100),
    biotime_resolution_data json,
    status character varying(20),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biotime_conflict_resolutions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biotime_device_groups (
    id integer NOT NULL,
    group_name character varying(100) NOT NULL,
    group_type character varying(50) NOT NULL,
    device_ids json NOT NULL,
    configuration json,
    is_active boolean DEFAULT true,
    parent_group_id integer,
    priority integer,
    description text,
    biotime_group_id character varying(100),
    biotime_sync_enabled boolean DEFAULT true,
    biotime_last_sync timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biotime_device_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biotime_devices (
    id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    device_name character varying(100) NOT NULL,
    device_type character varying(50) NOT NULL,
    manufacturer character varying(100),
    model character varying(100),
    firmware_version character varying(50),
    hardware_version character varying(50),
    serial_number character varying(100),
    ip_address character varying(45),
    mac_address character varying(17),
    port integer,
    network_type character varying(20),
    biotime_device_id character varying(100),
    biotime_configuration json,
    biotime_last_config_sync timestamp with time zone,
    biotime_api_version character varying(20),
    supported_biometric_types json,
    max_templates_per_type json,
    supported_verification_methods json,
    anti_passback_enabled boolean DEFAULT false,
    multi_factor_enabled boolean DEFAULT false,
    status character varying(20) NOT NULL,
    last_seen timestamp with time zone,
    last_heartbeat timestamp with time zone,
    battery_level integer,
    signal_strength integer,
    device_group_id integer,
    location character varying(100),
    zone character varying(100),
    installation_date timestamp with time zone,
    warranty_expiry timestamp with time zone,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biotime_devices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS biotime_sync_logs (
    id integer NOT NULL,
    sync_type character varying(50) NOT NULL,
    sync_direction character varying(20) NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    duration_seconds integer,
    total_records integer,
    successful_records integer,
    failed_records integer,
    conflict_records integer,
    skipped_records integer,
    sync_details json,
    error_details json,
    conflict_resolution json,
    biotime_sync_id character varying(100),
    biotime_api_version character varying(20),
    biotime_server_url character varying(255),
    biotime_last_successful_sync timestamp with time zone,
    status character varying(20),
    retry_count integer,
    max_retries integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS biotime_sync_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS certification_audits (
    id integer NOT NULL,
    certification_id integer NOT NULL,
    personnel_id integer NOT NULL,
    action character varying(50) NOT NULL,
    old_values text,
    new_values text,
    performed_by integer,
    performed_at timestamp with time zone DEFAULT now(),
    reason text,
    ip_address character varying(45),
    user_agent character varying(500)
);

CREATE SEQUENCE IF NOT EXISTS certification_audits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS certification_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS certifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS checkinout (
    id bigint NOT NULL,
    user_id integer,
    emp_code character varying(20) NOT NULL,
    check_time timestamp with time zone NOT NULL,
    check_type smallint NOT NULL,
    verify_type smallint,
    sensor_id character varying(20),
    terminal_sn character varying(20),
    work_code integer,
    processed boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS checkinout_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS contract_assignments (
    id integer NOT NULL,
    contract_id integer NOT NULL,
    contractor_id integer NOT NULL,
    personnel_id integer,
    project_name character varying(200),
    project_code character varying(50),
    role character varying(100) NOT NULL,
    department_id integer,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    actual_end_date timestamp with time zone,
    hourly_rate double precision,
    daily_rate double precision,
    overtime_rate double precision,
    currency character varying(3) DEFAULT 'USD'::character varying,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    performance_rating character varying(10),
    completion_status character varying(20) DEFAULT 'IN_PROGRESS'::character varying,
    assigned_by integer,
    supervisor_id integer,
    approved_by integer,
    approved_at timestamp with time zone,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS contract_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS contractor_compliance (
    id integer NOT NULL,
    contractor_id integer NOT NULL,
    compliance_type character varying(50) NOT NULL,
    compliance_status character varying(20) NOT NULL,
    compliance_date timestamp with time zone NOT NULL,
    expiry_date timestamp with time zone,
    certifying_authority character varying(100),
    certificate_number character varying(100),
    assessment_score double precision,
    assessment_notes text,
    requirements_met json,
    next_review_date timestamp with time zone,
    certificate_path character varying(500),
    supporting_documents json,
    assessed_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS contractor_compliance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS contractors (
    id integer NOT NULL,
    vendor_id integer,
    contractor_code character varying(50) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(100),
    phone character varying(20),
    date_of_birth timestamp with time zone,
    national_id character varying(50),
    passport_number character varying(50),
    work_permit_number character varying(50),
    work_permit_expiry timestamp with time zone,
    job_title character varying(100),
    specialization character varying(100),
    experience_years integer DEFAULT 0,
    hourly_rate double precision,
    daily_rate double precision,
    currency character varying(3) DEFAULT 'USD'::character varying,
    skills json,
    certifications json,
    security_clearance character varying(50),
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    availability_status character varying(20) DEFAULT 'AVAILABLE'::character varying,
    preferred_work_locations json,
    background_check_status character varying(20) DEFAULT 'PENDING'::character varying,
    background_check_date timestamp with time zone,
    medical_clearance_status character varying(20) DEFAULT 'PENDING'::character varying,
    medical_clearance_date timestamp with time zone,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS contractors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS custom_attribute_values (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    attribute_id integer NOT NULL,
    value_text text,
    value_number double precision,
    value_date timestamp with time zone,
    value_boolean boolean,
    value_json json,
    file_path character varying(500),
    file_name character varying(255),
    file_size integer,
    mime_type character varying(100),
    is_valid boolean,
    validation_errors json,
    created_by integer,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS custom_attribute_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS custom_attributes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS department_personnel (
    id integer NOT NULL,
    department_id integer NOT NULL,
    personnel_id integer NOT NULL,
    role character varying(100) NOT NULL,
    "position" character varying(100),
    is_primary boolean,
    is_manager boolean,
    assigned_at timestamp with time zone DEFAULT now(),
    unassigned_at timestamp with time zone,
    approved_by integer,
    approved_at timestamp with time zone,
    status character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS department_personnel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS departments (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(20) NOT NULL,
    description text,
    parent_id integer,
    manager_id integer,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    department_type character varying(50),
    level integer DEFAULT 0,
    sort_order integer DEFAULT 0,
    zone_id integer,
    contact_person character varying(100),
    contact_email character varying(100),
    contact_phone character varying(20),
    max_personnel integer DEFAULT 0,
    current_personnel_count integer DEFAULT 0,
    budget_allocated numeric(15,2),
    budget_used numeric(15,2),
    safety_critical boolean DEFAULT false,
    required_certifications json,
    safety_protocols json,
    access_levels json,
    security_clearance_required boolean DEFAULT false,
    zkteco_department_id integer,
    zkteco_sync_enabled boolean DEFAULT false,
    last_sync_at timestamp with time zone,
    created_by integer,
    updated_by integer,
    status character varying(20),
    default_shift_id integer
);

CREATE SEQUENCE IF NOT EXISTS departments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS device_blacklist (
    id integer NOT NULL,
    emp_code character varying(20) NOT NULL,
    reason text,
    blocked_at timestamp with time zone DEFAULT now(),
    blocked_by integer,
    is_active boolean,
    expires_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS device_blacklist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS device_events (
    id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    event_type character varying(50) NOT NULL,
    event_severity character varying(20),
    event_data json,
    old_values json,
    new_values json,
    "timestamp" timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    status character varying(20),
    description text,
    resolution_notes text,
    acknowledged_by integer,
    acknowledged_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS device_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS device_maintenance (
    id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    maintenance_type character varying(50) NOT NULL,
    description text,
    scheduled_date timestamp with time zone NOT NULL,
    estimated_duration integer,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    actual_duration integer,
    status character varying(20),
    performed_by integer,
    technician_notes text,
    parts_used json,
    cost integer,
    test_results json,
    next_maintenance_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS device_maintenance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS device_schedules (
    id integer NOT NULL,
    device_id character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    monday_enabled boolean,
    tuesday_enabled boolean,
    wednesday_enabled boolean,
    thursday_enabled boolean,
    friday_enabled boolean,
    saturday_enabled boolean,
    sunday_enabled boolean,
    time_ranges json,
    access_mode character varying(50),
    authorized_personnel json,
    is_active boolean,
    priority integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS device_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS devicemap (
    id integer NOT NULL,
    device_sn character varying(20) NOT NULL,
    ip_address character varying(15),
    port integer DEFAULT 4370,
    comm_key character varying(20) DEFAULT '0'::character varying,
    device_type smallint DEFAULT 0,
    area_id integer,
    last_sync timestamp with time zone,
    sync_status smallint DEFAULT 0,
    status smallint DEFAULT 0,
    firmware_version character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS devicemap_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS devices (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    serial_number character varying(50) NOT NULL,
    device_type character varying(50) DEFAULT 'FINGERPRINT'::character varying,
    model character varying(100),
    firmware_version character varying(50),
    ip_address character varying(45),
    port integer DEFAULT 4370,
    location character varying(255),
    zone_id integer,
    status character varying(20) DEFAULT 'OFFLINE'::character varying,
    is_active boolean DEFAULT true NOT NULL,
    last_heartbeat timestamp with time zone,
    last_sync timestamp with time zone,
    connection_mode character varying(20) DEFAULT 'ADMS'::character varying,
    adms_url character varying(500),
    user_count integer DEFAULT 0,
    fp_count integer DEFAULT 0,
    face_count integer DEFAULT 0,
    log_count integer DEFAULT 0,
    manufacturer character varying(100) DEFAULT 'ZKTeco'::character varying,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    device_id character varying(100),
    location_description character varying(255),
    building character varying(100),
    floor character varying(50),
    last_seen timestamp with time zone,
    battery_level integer,
    signal_strength integer,
    supported_biometrics jsonb,
    max_templates integer DEFAULT 1000,
    current_templates integer DEFAULT 0,
    access_mode character varying(50) DEFAULT 'normal'::character varying,
    authorized_personnel jsonb,
    access_schedule jsonb,
    zkteco_device_id character varying(50),
    zkteco_config jsonb,
    encryption_enabled boolean DEFAULT true,
    authentication_key character varying(255),
    last_maintenance timestamp with time zone,
    next_maintenance timestamp with time zone,
    maintenance_interval_days integer DEFAULT 90,
    settings jsonb,
    mac_address character varying(17),
    hardware_version character varying(50),
    auto_poll boolean DEFAULT false NOT NULL,
    poll_interval_sec integer DEFAULT 300 NOT NULL,
    last_attendance_pull timestamp with time zone,
    custom_fields jsonb
);

CREATE SEQUENCE IF NOT EXISTS devices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS disciplinary_cases (
    id integer NOT NULL,
    personnel_id integer,
    case_number character varying(50) NOT NULL,
    incident_date date NOT NULL,
    incident_type character varying(50) NOT NULL,
    description text,
    severity_level character varying(20),
    action_type character varying(20),
    status character varying(20) DEFAULT 'open'::character varying,
    reported_by integer,
    assigned_to integer,
    resolution_date date,
    resolution_notes text,
    appeal_status character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS disciplinary_cases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_device (
    id integer NOT NULL,
    terminal_sn character varying(20),
    device_type smallint DEFAULT 0,
    zone_id integer,
    status smallint DEFAULT 0,
    last_heartbeat timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS emergency_device_command (
    id bigint NOT NULL,
    emergency_event_id bigint,
    device_id integer,
    command_type character varying(50),
    command_data jsonb,
    command_priority smallint,
    status character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    sent_at timestamp with time zone,
    executed_at timestamp with time zone,
    completed_at timestamp with time zone,
    queue_time double precision,
    execution_time double precision,
    total_time double precision,
    device_response jsonb,
    acknowledgment jsonb,
    confirmation_data jsonb,
    error_code character varying(50),
    error_message text,
    retry_count integer,
    max_retries integer,
    batch_id character varying(50),
    parent_command bigint,
    operator_id integer,
    audit_log jsonb,
    compliance_data jsonb
);

CREATE SEQUENCE IF NOT EXISTS emergency_device_command_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_device_enhanced (
    id integer NOT NULL,
    terminal_sn character varying(20) NOT NULL,
    device_type smallint NOT NULL,
    zone_id integer,
    building_id integer,
    status smallint,
    health_score double precision,
    last_maintenance timestamp with time zone,
    next_maintenance timestamp with time zone,
    response_time_avg double precision,
    uptime_percentage double precision,
    failure_count integer,
    test_results jsonb,
    ai_monitored boolean,
    predictive_maintenance jsonb,
    performance_anomalies jsonb,
    usage_patterns jsonb,
    location_description character varying(200),
    installation_date date,
    manufacturer character varying(100),
    model character varying(100),
    firmware_version character varying(50),
    serial_number character varying(100),
    capabilities jsonb,
    supported_commands jsonb,
    integration_points jsonb,
    test_schedule character varying(50),
    last_test timestamp with time zone,
    test_results_history jsonb,
    calibration_data jsonb,
    operating_temperature_min double precision,
    operating_temperature_max double precision,
    humidity_tolerance_min double precision,
    humidity_tolerance_max double precision,
    power_requirements jsonb,
    network_config jsonb,
    communication_protocols jsonb,
    encryption_keys jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS emergency_device_enhanced_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS emergency_device_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_device_maintenance (
    id integer NOT NULL,
    device_id integer NOT NULL,
    maintenance_type smallint NOT NULL,
    description text NOT NULL,
    priority smallint,
    scheduled_date timestamp with time zone NOT NULL,
    estimated_duration integer,
    actual_duration integer,
    status character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    technician character varying(100),
    technician_id integer,
    supervisor character varying(100),
    supervisor_id integer,
    work_performed text,
    parts_used jsonb,
    tools_used jsonb,
    measurements jsonb,
    labor_cost double precision,
    parts_cost double precision,
    total_cost double precision,
    cost_center character varying(50),
    quality_check boolean,
    quality_score double precision,
    inspection_notes text,
    approved_by integer,
    approved_time timestamp with time zone,
    next_maintenance timestamp with time zone,
    warranty_expiry date,
    maintenance_interval integer,
    predictive_maintenance boolean,
    ai_recommended boolean,
    performance_impact jsonb,
    risk_assessment jsonb,
    work_order_id character varying(100),
    photos_before jsonb,
    photos_after jsonb,
    documentation jsonb,
    compliance_required boolean,
    audit_findings jsonb,
    regulatory_compliance jsonb
);

CREATE SEQUENCE IF NOT EXISTS emergency_device_maintenance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_event (
    id bigint NOT NULL,
    event_type smallint NOT NULL,
    status smallint,
    scope smallint,
    zone_ids integer[],
    door_ids integer[],
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    initiated_by integer,
    initiated_type smallint,
    trigger_source character varying(100),
    reason text,
    actions jsonb,
    mustering_event_id bigint,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS emergency_event_enhanced (
    id bigint NOT NULL,
    event_type smallint NOT NULL,
    status smallint,
    scope smallint,
    severity smallint,
    zone_ids integer[],
    door_ids integer[],
    building_ids integer[],
    personnel_ids integer[],
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    estimated_resolution timestamp with time zone,
    actual_resolution timestamp with time zone,
    initiated_by integer,
    initiated_type smallint,
    trigger_source character varying(100),
    confidence_score double precision,
    reason text,
    description text,
    impact_assessment jsonb,
    risk_factors jsonb,
    mitigation_actions jsonb,
    ai_detected boolean,
    ai_predictions jsonb,
    ai_recommendations jsonb,
    pattern_anomalies jsonb,
    mustering_event_id bigint,
    incident_report_id bigint,
    external_system_id character varying(100),
    response_time double precision,
    resolution_time double precision,
    cost_impact double precision,
    disruption_level smallint,
    actions jsonb,
    command_queue jsonb,
    notification_log jsonb,
    compliance_required boolean,
    compliance_notes text,
    audit_trail jsonb,
    regulatory_reports jsonb,
    weather_conditions jsonb,
    environmental_factors jsonb,
    affected_personnel jsonb,
    injuries jsonb,
    evacuations jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS emergency_event_enhanced_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS emergency_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_notification (
    id bigint NOT NULL,
    emergency_event_id bigint NOT NULL,
    channel smallint NOT NULL,
    recipient_type smallint,
    recipient_id integer,
    recipient_addr character varying(255),
    message text,
    status smallint,
    sent_time timestamp with time zone,
    delivered_time timestamp with time zone,
    error_msg text,
    template_vars jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS emergency_notification_enhanced (
    id bigint NOT NULL,
    emergency_event_id bigint NOT NULL,
    channel smallint NOT NULL,
    recipient_type smallint,
    recipient_id integer,
    recipient_addr character varying(255),
    recipient_name character varying(100),
    message text,
    message_template character varying(100),
    template_variables jsonb,
    personalization_data jsonb,
    status smallint,
    priority smallint,
    created_at timestamp with time zone DEFAULT now(),
    queued_at timestamp with time zone,
    sent_time timestamp with time zone,
    delivered_time timestamp with time zone,
    acknowledged_at timestamp with time zone,
    read_time timestamp with time zone,
    delivery_attempts integer,
    last_attempt_status character varying(50),
    delivery_provider character varying(50),
    tracking_id character varying(100),
    delivery_time double precision,
    cost double precision,
    engagement_metrics jsonb,
    retry_policy jsonb,
    escalation_rules jsonb,
    acknowledgment_required boolean,
    response_tracking jsonb,
    compliance_required boolean,
    audit_log jsonb,
    regulatory_compliance jsonb,
    error_codes jsonb,
    error_details text,
    recovery_actions jsonb
);

CREATE SEQUENCE IF NOT EXISTS emergency_notification_enhanced_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS emergency_notification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_panic_log (
    id bigint NOT NULL,
    terminal_sn character varying(20),
    panic_time timestamp with time zone NOT NULL,
    panic_type smallint,
    emp_code character varying(20),
    location character varying(100),
    emergency_event_id bigint,
    reason text,
    resolved_by integer,
    resolved_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS emergency_panic_log_enhanced (
    id bigint NOT NULL,
    terminal_sn character varying(20),
    device_type smallint,
    emp_code character varying(20),
    location character varying(100),
    geolocation jsonb,
    emergency_event_id bigint,
    panic_time timestamp with time zone NOT NULL,
    panic_type smallint,
    severity smallint,
    confidence double precision,
    environmental_conditions jsonb,
    nearby_personnel jsonb,
    security_context jsonb,
    ai_detected boolean,
    ai_confidence double precision,
    ai_risk_assessment jsonb,
    false_alarm_probability double precision,
    resolved_by integer,
    resolved_time timestamp with time zone,
    resolution_method character varying(50),
    verification_required boolean,
    verified_by integer,
    verified_time timestamp with time zone,
    impact_assessment jsonb,
    disruption_duration integer,
    cost_impact double precision,
    personnel_impacted jsonb,
    follow_up_required boolean,
    follow_up_actions jsonb,
    investigation_required boolean,
    investigation_results jsonb,
    audio_recording character varying(255),
    video_recording character varying(255),
    sensor_data jsonb,
    regulatory_report boolean,
    audit_findings jsonb,
    compliance_notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS emergency_panic_log_enhanced_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS emergency_panic_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_plan (
    id integer NOT NULL,
    plan_name character varying(100) NOT NULL,
    event_type smallint,
    zone_id integer,
    steps text,
    pdf_path character varying(255),
    contacts jsonb,
    is_active boolean,
    last_reviewed date,
    next_review date,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS emergency_plan_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS emergency_template (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    event_type smallint NOT NULL,
    description text,
    actions jsonb NOT NULL,
    notify_channels jsonb,
    auto_mustering boolean,
    auto_mustering_zone_id integer,
    is_active boolean,
    is_default boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS emergency_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS employee_benefits (
    id integer NOT NULL,
    personnel_id integer,
    plan_id integer,
    enrollment_date date,
    effective_date date,
    coverage_amount numeric(10,2),
    dependents json,
    status character varying(20) DEFAULT 'active'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS employee_benefits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS employment_contracts (
    id integer NOT NULL,
    personnel_id integer,
    contract_number character varying(50) NOT NULL,
    contract_type character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date,
    probation_end_date date,
    salary numeric(10,2),
    currency character varying(3) DEFAULT 'USD'::character varying,
    payment_frequency character varying(20),
    working_hours integer,
    job_title character varying(100),
    department_id integer,
    position_id integer,
    terms text,
    status character varying(20) DEFAULT 'active'::character varying,
    signed_by integer,
    signed_date date,
    document_url character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS employment_contracts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS events (
    id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    description text,
    personnel_id integer,
    user_id integer,
    "timestamp" timestamp with time zone NOT NULL,
    event_metadata json
);

CREATE SEQUENCE IF NOT EXISTS events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS face (
    id integer NOT NULL,
    user_id integer,
    template_data bytea NOT NULL,
    template_version integer DEFAULT 1,
    quality_score integer,
    template_size integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT face_quality_score_check CHECK (((quality_score >= 0) AND (quality_score <= 100)))
);

CREATE SEQUENCE IF NOT EXISTS face_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS fingerprint (
    id integer NOT NULL,
    user_id integer,
    finger_index integer NOT NULL,
    template_data bytea NOT NULL,
    template_version integer DEFAULT 1,
    quality_score integer,
    template_size integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT fingerprint_finger_index_check CHECK (((finger_index >= 0) AND (finger_index <= 9))),
    CONSTRAINT fingerprint_quality_score_check CHECK (((quality_score >= 0) AND (quality_score <= 100)))
);

CREATE SEQUENCE IF NOT EXISTS fingerprint_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS flight_log (
    id integer NOT NULL,
    transport_id integer NOT NULL,
    flight_date timestamp with time zone NOT NULL,
    departure_time timestamp with time zone NOT NULL,
    arrival_time timestamp with time zone,
    departure_location character varying(100) NOT NULL,
    arrival_location character varying(100) NOT NULL,
    flight_duration double precision NOT NULL,
    distance double precision NOT NULL,
    fuel_consumed double precision,
    weather_conditions character varying(100),
    pilot_name character varying(100),
    co_pilot_name character varying(100),
    flight_route character varying(200),
    passengers_count integer,
    cargo_weight double precision,
    incidents text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS flight_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS holiday (
    id integer NOT NULL,
    holiday_name character varying(100) NOT NULL,
    holiday_date date NOT NULL,
    end_date date,
    is_repeatable boolean DEFAULT false,
    repeat_month integer,
    repeat_day integer,
    holiday_type smallint DEFAULT 0,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS holiday_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS hr_integration_config (
    id integer NOT NULL,
    api_base_url character varying(255),
    api_key character varying(500),
    org_id character varying(100),
    auth_header_name character varying(100) DEFAULT 'Authorization'::character varying,
    attendance_endpoint character varying(255) DEFAULT '/v1/attendance/clock-records'::character varying,
    employee_endpoint character varying(255) DEFAULT '/v1/employees'::character varying,
    is_enabled boolean DEFAULT false,
    sync_time character varying(10) DEFAULT '00:00'::character varying,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS hr_integration_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS hr_sync_log (
    id integer NOT NULL,
    sync_date date,
    triggered_by character varying(50),
    status character varying(20),
    records_built integer DEFAULT 0,
    records_sent integer DEFAULT 0,
    records_failed integer DEFAULT 0,
    message character varying(500),
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS hr_sync_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS iclock_bio_template (
    id bigint NOT NULL,
    emp_code character varying(20) NOT NULL,
    finger_id smallint DEFAULT 0 NOT NULL,
    template_size integer,
    valid boolean DEFAULT true,
    template_data text,
    source_sn character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS iclock_bio_template_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS iclock_devcmd (
    id bigint NOT NULL,
    sn character varying(20) NOT NULL,
    cmd_content text NOT NULL,
    status smallint,
    cmd_commit_time timestamp with time zone DEFAULT now(),
    cmd_trans_time timestamp with time zone,
    cmd_return_time timestamp with time zone,
    cmd_return text,
    created_by integer,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS iclock_devcmd_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS iclock_operlog (
    id bigint NOT NULL,
    terminal_sn character varying(20) NOT NULL,
    oper_event smallint NOT NULL,
    event_time timestamp with time zone NOT NULL,
    admin_id character varying(20),
    door_id integer,
    object_name character varying(100),
    param1 character varying(100),
    param2 character varying(100),
    raw_data text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS iclock_operlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS iclock_terminal (
    id integer NOT NULL,
    sn character varying(20) NOT NULL,
    alias character varying(50),
    ip_address character varying(45),
    area_id integer,
    last_activity timestamp with time zone,
    state smallint DEFAULT 0,
    comm_key character varying(20),
    fw_ver character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    log_count integer DEFAULT 0,
    zone_id integer,
    pushver character varying(10) DEFAULT '1.0'::character varying,
    user_count integer DEFAULT 0,
    fp_count integer DEFAULT 0,
    face_count integer DEFAULT 0,
    palm_count integer DEFAULT 0,
    att_stamp bigint DEFAULT 0,
    op_stamp bigint DEFAULT 0,
    heartbeat_interval integer DEFAULT 30,
    device_name character varying(50),
    device_model character varying(50),
    device_type smallint DEFAULT 0,
    is_auto_reg boolean DEFAULT false,
    reader_purpose character varying(20) DEFAULT 'ATTENDANCE'::character varying NOT NULL,
    connection_mode character varying(10) DEFAULT 'adms'::character varying NOT NULL,
    user_stamp bigint DEFAULT 0 NOT NULL,
    platform character varying(30),
    mac_address character varying(17),
    oem_vendor character varying(50),
    CONSTRAINT iclock_terminal_reader_purpose_check CHECK (((reader_purpose)::text = ANY ((ARRAY['ATTENDANCE'::character varying, 'ACCESS_ENTRY'::character varying, 'ACCESS_EXIT'::character varying, 'MUSTERING'::character varying, 'POB'::character varying, 'EMERGENCY'::character varying])::text[])))
);

CREATE SEQUENCE IF NOT EXISTS iclock_terminal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS iclock_transaction (
    id bigint NOT NULL,
    emp_code character varying(20) NOT NULL,
    punch_time timestamp with time zone NOT NULL,
    punch_state smallint,
    verify_type smallint,
    work_code integer,
    terminal_sn character varying(20),
    area_alias character varying(50),
    upload_time timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS iclock_transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS leave_balance (
    id integer NOT NULL,
    personnel_id integer,
    leave_type character varying(50) NOT NULL,
    total_days numeric(5,2),
    used_days numeric(5,2) DEFAULT 0,
    balance_days numeric(5,2),
    carry_forward_days numeric(5,2) DEFAULT 0,
    year integer,
    accrual_rate numeric(5,2),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS leave_balance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS leave_blackout (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    reason text,
    applies_to character varying(20) DEFAULT 'all'::character varying,
    department_id integer,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS leave_blackout_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS leave_management (
    id integer NOT NULL,
    personnel_id integer,
    leave_type character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    days_count numeric(5,2),
    reason text,
    status character varying(20) DEFAULT 'pending'::character varying,
    approved_by integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS leave_management_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS manifest_entry (
    id integer NOT NULL,
    schedule_id integer NOT NULL,
    personnel_id integer,
    passenger_name character varying(200) NOT NULL,
    emp_code character varying(50),
    company character varying(100),
    id_number character varying(50),
    direction character varying(20) DEFAULT 'INBOUND'::character varying NOT NULL,
    status character varying(20) DEFAULT 'MANIFESTED'::character varying NOT NULL,
    confirmed_at timestamp with time zone,
    confirmed_by_id integer,
    remarks text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS manifest_entry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_audit_log (
    id bigint NOT NULL,
    access_time timestamp without time zone,
    user_id integer,
    record_type character varying(50),
    record_id bigint,
    action character varying(20),
    ip_address character varying(45),
    user_agent text,
    details text
);

CREATE SEQUENCE IF NOT EXISTS mtd_audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_cert_type (
    id integer NOT NULL,
    cert_name character varying(100) NOT NULL,
    validity_days integer NOT NULL,
    is_critical boolean,
    required_for_dept integer[],
    required_for_position integer[],
    required_for_vendor integer[],
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS mtd_cert_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_certification (
    id bigint NOT NULL,
    person_type smallint NOT NULL,
    emp_id integer,
    visitor_id bigint,
    cert_type_id integer NOT NULL,
    cert_no character varying(100),
    issuer character varying(100),
    issue_date date NOT NULL,
    expiry_date date,
    cert_path character varying(255),
    status smallint,
    verified_by integer,
    verified_time timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS mtd_certification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_compliance_log (
    id bigint NOT NULL,
    check_time timestamp without time zone,
    emp_id integer,
    cert_type_id integer,
    record_type character varying(50),
    record_id bigint,
    status smallint,
    action_taken character varying(100),
    details text,
    created_by integer
);

CREATE SEQUENCE IF NOT EXISTS mtd_compliance_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_induction_record (
    id bigint NOT NULL,
    person_type smallint NOT NULL,
    emp_id integer,
    visitor_id bigint,
    template_id integer NOT NULL,
    taken_date date,
    score integer,
    passed boolean,
    valid_until date,
    signed_doc character varying(255),
    trainer_emp_id integer,
    quiz_answers json,
    completion_time timestamp without time zone,
    created_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS mtd_induction_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_induction_template (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    video_path character varying(255),
    slides_path character varying(255),
    quiz_questions json,
    passing_score integer,
    validity_days integer,
    required_for_type smallint,
    description text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS mtd_induction_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_medical_record (
    id bigint NOT NULL,
    person_type smallint NOT NULL,
    emp_id integer,
    visitor_id bigint,
    blood_group character varying(3),
    height_cm integer,
    weight_kg numeric(5,2),
    bmi numeric(4,2),
    medical_conditions text,
    allergies text,
    disabilities text,
    fit_status smallint,
    restrictions text,
    doctor_name character varying(100),
    last_checkup date,
    next_due date,
    cert_path character varying(255),
    updated_by integer,
    updated_time timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS mtd_medical_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_ppe_issue (
    id bigint NOT NULL,
    emp_id integer NOT NULL,
    ppe_type_id integer NOT NULL,
    serial_no character varying(100),
    issue_date date,
    due_return_date date,
    return_date date,
    condition_out smallint,
    condition_in smallint,
    last_calib_date date,
    next_calib_date date,
    status smallint,
    notes text,
    issued_by integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS mtd_ppe_issue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtd_ppe_type (
    id integer NOT NULL,
    ppe_name character varying(100) NOT NULL,
    lifespan_days integer,
    requires_calibration boolean,
    calib_interval_days integer,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS mtd_ppe_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtg_action_item (
    id bigint NOT NULL,
    booking_id bigint NOT NULL,
    action_desc character varying(500) NOT NULL,
    assignee_emp_id integer NOT NULL,
    due_date date,
    status smallint,
    completed_time timestamp with time zone,
    created_time timestamp with time zone,
    created_by integer
);

CREATE SEQUENCE IF NOT EXISTS mtg_action_item_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtg_attendance (
    id bigint NOT NULL,
    booking_id bigint NOT NULL,
    attendee_id bigint NOT NULL,
    check_in_time timestamp with time zone,
    check_out_time timestamp with time zone,
    device_sn character varying(20),
    verify_type smallint,
    status smallint,
    notes text
);

CREATE SEQUENCE IF NOT EXISTS mtg_attendance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtg_attendee (
    id bigint NOT NULL,
    booking_id bigint NOT NULL,
    attendee_type smallint NOT NULL,
    emp_id integer,
    visitor_id bigint,
    ext_name character varying(100),
    ext_email character varying(100),
    ext_phone character varying(20),
    is_required boolean,
    pre_reg_id bigint,
    invitation_sent boolean,
    invitation_sent_time timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS mtg_attendee_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtg_booking (
    id bigint NOT NULL,
    room_id integer NOT NULL,
    title character varying(200) NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    organizer_emp_id integer NOT NULL,
    attendee_count integer,
    agenda text,
    attachments text,
    repeat_type smallint,
    repeat_until date,
    status smallint,
    approval_by integer,
    approval_time timestamp with time zone,
    approval_note character varying(255),
    meeting_code character varying(20) NOT NULL,
    qr_code character varying(100),
    auto_unlock boolean,
    created_time timestamp with time zone,
    updated_time timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS mtg_booking_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtg_equipment (
    id integer NOT NULL,
    equip_name character varying(100) NOT NULL,
    equip_type character varying(50),
    room_id integer,
    status smallint,
    serial_no character varying(50),
    purchase_date date,
    warranty_expiry date,
    last_maintenance date,
    notes text
);

CREATE SEQUENCE IF NOT EXISTS mtg_equipment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtg_minutes (
    id bigint NOT NULL,
    booking_id bigint NOT NULL,
    minutes_path character varying(255),
    uploaded_by integer NOT NULL,
    uploaded_time timestamp with time zone,
    file_size bigint,
    file_type character varying(10)
);

CREATE SEQUENCE IF NOT EXISTS mtg_minutes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mtg_room (
    id integer NOT NULL,
    room_name character varying(100) NOT NULL,
    capacity integer NOT NULL,
    location character varying(100),
    area_id integer,
    door_id integer,
    equipment text,
    status smallint,
    require_approval boolean,
    mustering_zone_id integer,
    is_emergency_assembly boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS mtg_room_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mustering_drill_schedule (
    id integer NOT NULL,
    zone_id integer NOT NULL,
    event_type smallint DEFAULT 1,
    scheduled_time timestamp with time zone NOT NULL,
    participant_type smallint DEFAULT 0,
    participant_id integer,
    template_id integer,
    auto_start boolean DEFAULT true,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    processed boolean DEFAULT false,
    processed_time timestamp with time zone,
    status character varying(20) DEFAULT 'PENDING'::character varying
);

CREATE SEQUENCE IF NOT EXISTS mustering_drill_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mustering_escalation_record (
    id bigint NOT NULL,
    event_id bigint NOT NULL,
    emp_code character varying(20) NOT NULL,
    level smallint NOT NULL,
    notification_type character varying(20),
    notified_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS mustering_escalation_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mustering_event (
    id bigint NOT NULL,
    zone_id integer,
    event_type smallint NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    status smallint DEFAULT 0,
    initiated_by integer,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text,
    total_expected integer DEFAULT 0,
    total_safe integer DEFAULT 0,
    total_missing integer DEFAULT 0,
    total_injured integer DEFAULT 0,
    zone_ids jsonb DEFAULT '[]'::jsonb
);

CREATE SEQUENCE IF NOT EXISTS mustering_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mustering_expected (
    id bigint NOT NULL,
    event_id bigint NOT NULL,
    emp_code character varying(50) NOT NULL,
    emp_name character varying(100) NOT NULL,
    dept_id integer,
    shift_id integer,
    last_punch_time timestamp with time zone,
    last_punch_area character varying(100),
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS mustering_expected_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mustering_log (
    id bigint NOT NULL,
    event_id bigint NOT NULL,
    emp_code character varying(20) NOT NULL,
    check_time timestamp with time zone NOT NULL,
    device_sn character varying(20),
    status smallint DEFAULT 0,
    location character varying(100),
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    emp_name character varying(100),
    dept_name character varying(50),
    device_alias character varying(50),
    last_punch_area character varying(20)
);

CREATE SEQUENCE IF NOT EXISTS mustering_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mustering_search_sweep (
    id bigint NOT NULL,
    event_id bigint NOT NULL,
    emp_code character varying(20) NOT NULL,
    area_searched character varying(200) NOT NULL,
    result character varying(20) NOT NULL,
    searcher_id integer,
    searcher_name character varying(100),
    notes text,
    sweep_time timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS mustering_search_sweep_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS mustering_template (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    event_type smallint,
    notify_sms boolean DEFAULT false,
    notify_email boolean DEFAULT false,
    notify_users text,
    actions text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS mustering_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS onboarding_checklists (
    id integer NOT NULL,
    onboarding_id integer NOT NULL,
    checklist_name character varying(100) NOT NULL,
    checklist_type character varying(50) NOT NULL,
    description text,
    is_required boolean,
    checklist_items json,
    sort_order integer,
    is_completed boolean,
    completed_by integer,
    completed_at timestamp with time zone,
    completion_notes text,
    depends_on_tasks json,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS onboarding_checklists_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS onboarding_documents (
    id integer NOT NULL,
    onboarding_id integer NOT NULL,
    document_type character varying(50) NOT NULL,
    document_name character varying(255) NOT NULL,
    document_path character varying(500) NOT NULL,
    file_size integer,
    mime_type character varying(100),
    description text,
    is_required boolean,
    uploaded_by integer,
    uploaded_at timestamp with time zone DEFAULT now(),
    is_verified boolean,
    verified_by integer,
    verified_at timestamp with time zone,
    verification_notes text
);

CREATE SEQUENCE IF NOT EXISTS onboarding_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS onboarding_notifications (
    id integer NOT NULL,
    onboarding_id integer NOT NULL,
    notification_type character varying(50) NOT NULL,
    recipient_id integer NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    is_read boolean,
    read_at timestamp with time zone,
    sent_via character varying(20),
    sent_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS onboarding_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS onboarding_task (
    id integer NOT NULL,
    emp_id integer NOT NULL,
    task_name character varying(100) NOT NULL,
    doc_path character varying(255),
    status smallint DEFAULT 0,
    due_date date,
    approved_by integer,
    approved_time timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS onboarding_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS onboarding_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS onboarding_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS onboardings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS overtime_management (
    id integer NOT NULL,
    personnel_id integer,
    overtime_type character varying(20) NOT NULL,
    date date NOT NULL,
    start_time time without time zone,
    end_time time without time zone,
    hours_worked numeric(5,2),
    overtime_hours numeric(5,2),
    reason text,
    status character varying(20) DEFAULT 'pending'::character varying,
    approved_by integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    compensation_type character varying(20),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS overtime_management_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS overtime_record (
    id bigint NOT NULL,
    emp_code character varying(20) NOT NULL,
    overtime_date date NOT NULL,
    overtime_rule_id integer,
    start_time time without time zone,
    end_time time without time zone,
    total_minutes integer NOT NULL,
    rate double precision NOT NULL,
    overtime_amount double precision,
    approved_by integer,
    approved_time timestamp with time zone,
    status smallint DEFAULT 0,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS overtime_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS overtime_rule (
    id integer NOT NULL,
    rule_name character varying(100) NOT NULL,
    rule_type smallint NOT NULL,
    min_minutes integer NOT NULL,
    rate double precision DEFAULT 1.0 NOT NULL,
    max_hours_per_day double precision,
    max_hours_per_week double precision,
    area_id integer,
    department_id integer,
    is_active boolean DEFAULT true,
    effective_date date NOT NULL,
    expiry_date date,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS overtime_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS overtime_rules (
    id integer NOT NULL,
    rule_name character varying(100) NOT NULL,
    rule_type character varying(20) NOT NULL,
    daily_threshold_hours numeric(5,2),
    weekly_threshold_hours numeric(5,2),
    monthly_threshold_hours numeric(5,2),
    rate_multiplier numeric(5,2) DEFAULT 1.5,
    max_daily_hours numeric(5,2),
    max_weekly_hours numeric(5,2),
    max_monthly_hours numeric(5,2),
    requires_approval boolean DEFAULT true,
    applies_to character varying(20) DEFAULT 'all'::character varying,
    is_active boolean DEFAULT true,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS overtime_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pay_attendance_mapping (
    id integer NOT NULL,
    attendance_field character varying(50) NOT NULL,
    payroll_item_name character varying(50) NOT NULL,
    rate numeric(10,4),
    is_active boolean,
    description text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_attendance_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pay_audit_log (
    id bigint NOT NULL,
    table_name character varying(50) NOT NULL,
    record_id integer NOT NULL,
    action_type character varying(20) NOT NULL,
    old_values jsonb,
    new_values jsonb,
    changed_fields jsonb,
    user_id integer,
    ip_address inet,
    user_agent text,
    "timestamp" timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pay_bank_config (
    id integer NOT NULL,
    bank_name character varying(100) NOT NULL,
    bank_code character varying(20) NOT NULL,
    export_format character varying(10),
    file_template text,
    header_rows integer,
    footer_rows integer,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_bank_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pay_calculation_log (
    id bigint NOT NULL,
    period_id integer,
    emp_id integer,
    calculation_type character varying(50),
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    status character varying(20),
    input_data jsonb,
    result_data jsonb,
    error_message text,
    created_by integer,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_calculation_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pay_contractor_rate (
    id integer NOT NULL,
    vendor_id integer,
    position_id integer,
    position_name character varying(100),
    hourly_rate numeric(10,2),
    daily_rate numeric(10,2),
    weekly_rate numeric(10,2),
    monthly_rate numeric(10,2),
    ot_rate numeric(10,2),
    night_shift_rate numeric(10,2),
    holiday_rate numeric(10,2),
    is_active boolean,
    effective_date date,
    end_date date,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_contractor_rate_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS pay_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE TABLE IF NOT EXISTS pay_loan_deduction (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    salary_id bigint,
    period_id integer,
    emp_id integer NOT NULL,
    emi_amount numeric(10,2) NOT NULL,
    principal_amount numeric(10,2),
    interest_amount numeric(10,2),
    balance_before numeric(10,2),
    balance_after numeric(10,2),
    deduction_date date,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_loan_deduction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS pay_loan_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pay_payslip_template (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    template_type character varying(20),
    header_html text,
    body_html text,
    footer_html text,
    css_style text,
    is_default boolean,
    is_active boolean,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_payslip_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS pay_period_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS pay_salary_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS pay_salary_item_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE TABLE IF NOT EXISTS pay_structure_assign (
    id integer NOT NULL,
    structure_id integer NOT NULL,
    assign_type integer NOT NULL,
    assign_id integer NOT NULL,
    priority integer,
    effective_date date,
    end_date date,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_structure_assign_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS pay_structure_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pay_zone_allowance (
    id integer NOT NULL,
    structure_id integer NOT NULL,
    area_id integer,
    zone_name character varying(100),
    allowance_type integer,
    amount numeric(10,2) NOT NULL,
    is_hazard boolean,
    hazard_rate numeric(5,2),
    effective_date date,
    end_date date,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS pay_zone_allowance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS performance_appraisals (
    id integer NOT NULL,
    personnel_id integer,
    cycle_id integer,
    appraisal_date date,
    reviewer_id integer,
    overall_rating character varying(20),
    goals_achieved numeric(5,2),
    performance_score numeric(5,2),
    strengths text,
    areas_for_improvement text,
    comments text,
    status character varying(20) DEFAULT 'draft'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS performance_appraisals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS permissions (
    id integer NOT NULL,
    code character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    category character varying(50) DEFAULT 'general'::character varying NOT NULL,
    is_system boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS personnel (
    id integer NOT NULL,
    emp_code character varying(20) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    full_name character varying(200),
    email character varying(255),
    phone character varying(20),
    user_id integer,
    department_id integer,
    "position" character varying(100),
    primary_role_id integer,
    current_zone_id integer,
    status character varying(20) DEFAULT 'ONSHORE'::character varying,
    employment_type character varying(30) DEFAULT 'EMPLOYEE'::character varying,
    hire_date date,
    photo_url character varying(500),
    nationality character varying(100),
    id_number character varying(50),
    passport_number character varying(50),
    emergency_contact_name character varying(200),
    emergency_contact_phone character varying(20),
    is_active boolean DEFAULT true NOT NULL,
    is_pob boolean DEFAULT false NOT NULL,
    pob_location character varying(100),
    pob_since timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    badge_id character varying(50),
    company character varying(255),
    department character varying(100),
    role character varying(100),
    current_location character varying(100),
    is_onboard boolean DEFAULT false,
    personnel_type character varying(20) DEFAULT 'STAFF'::character varying,
    safety_critical boolean DEFAULT false,
    biometric_enrolled boolean DEFAULT false,
    compliance_score double precision DEFAULT 0.0,
    biometric_data jsonb,
    fingerprint_templates jsonb,
    face_template character varying(255),
    certifications jsonb,
    training_records jsonb,
    medical_fitness_date timestamp with time zone,
    emergency_contact jsonb,
    blood_group character varying(10),
    medical_conditions text,
    last_seen timestamp with time zone,
    biotime_employee_id character varying(50),
    work_schedule jsonb,
    access_groups jsonb,
    device_groups jsonb,
    biometric_quality_score double precision DEFAULT 0.0,
    last_sync_timestamp timestamp with time zone,
    timezone_preference character varying(50) DEFAULT 'UTC'::character varying,
    language_preference character varying(10) DEFAULT 'en'::character varying,
    card_number bigint
);

CREATE TABLE IF NOT EXISTS personnel_area (
    id integer NOT NULL,
    area_code character varying(20),
    area_name character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS personnel_area_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS personnel_assignments (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    location character varying(255) NOT NULL,
    zone character varying(100),
    vessel character varying(100),
    platform character varying(100),
    assignment_type character varying(50) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    is_active boolean DEFAULT true,
    transport_method character varying(50),
    transport_details jsonb,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS personnel_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS personnel_department (
    id integer NOT NULL,
    dept_code character varying(20),
    dept_name character varying(50) NOT NULL,
    parent_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    default_shift_id integer
);

CREATE SEQUENCE IF NOT EXISTS personnel_department_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS personnel_employee (
    id integer NOT NULL,
    emp_code character varying(20) NOT NULL,
    first_name character varying(20),
    last_name character varying(25) NOT NULL,
    dept_id integer,
    area_id integer,
    position_id integer,
    hire_date date,
    birthday date,
    sex character(1),
    photo character varying(255),
    card_no character varying(20),
    pwd character varying(20),
    status smallint DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS personnel_employee_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS personnel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS pob_status (
    id integer NOT NULL,
    personnel_id integer,
    personnel_count integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'ONSHORE'::character varying NOT NULL,
    location character varying(100),
    last_updated timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS pob_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS position_assignments (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    position_id integer NOT NULL,
    department_id integer,
    assignment_type character varying(20) DEFAULT 'PRIMARY'::character varying,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    is_current boolean DEFAULT true,
    assigned_by integer,
    approved_by integer,
    approved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS position_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS position_levels (
    id integer NOT NULL,
    level_code character varying(10) NOT NULL,
    level_name character varying(50) NOT NULL,
    level_number integer NOT NULL,
    description text,
    level_type character varying(20),
    authority_level integer DEFAULT 1,
    can_approve boolean DEFAULT false,
    can_manage boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS position_levels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS position_templates (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    template_code character varying(20) NOT NULL,
    position_type character varying(20),
    job_category character varying(30),
    template_data json NOT NULL,
    default_requirements json,
    usage_count integer DEFAULT 0,
    last_used timestamp with time zone,
    is_active boolean DEFAULT true,
    is_system_template boolean DEFAULT false,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS position_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS positions (
    id integer NOT NULL,
    position_code character varying(20) NOT NULL,
    position_name character varying(100) NOT NULL,
    description text,
    parent_id integer,
    level integer DEFAULT 1,
    sort_order integer DEFAULT 0,
    department_id integer,
    position_type character varying(20),
    job_category character varying(30),
    grade_level character varying(10),
    required_certifications json,
    required_skills json,
    min_experience_years integer DEFAULT 0,
    education_level character varying(50),
    salary_range_min double precision,
    salary_range_max double precision,
    currency character varying(3) DEFAULT 'USD'::character varying,
    is_active boolean DEFAULT true,
    is_safety_critical boolean DEFAULT false,
    requires_background_check boolean DEFAULT false,
    created_by integer,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS promotion_transfers (
    id integer NOT NULL,
    personnel_id integer,
    transfer_type character varying(20) NOT NULL,
    effective_date date NOT NULL,
    from_department_id integer,
    to_department_id integer,
    from_position_id integer,
    to_position_id integer,
    from_location character varying(100),
    to_location character varying(100),
    salary_change numeric(10,2),
    reason text,
    status character varying(20) DEFAULT 'pending'::character varying,
    requested_by integer,
    approved_by integer,
    approved_at timestamp with time zone,
    rejection_reason text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS promotion_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS resignation_documents (
    id integer NOT NULL,
    resignation_id integer NOT NULL,
    document_type character varying(50) NOT NULL,
    document_name character varying(255) NOT NULL,
    document_path character varying(500) NOT NULL,
    file_size integer,
    mime_type character varying(100),
    description text,
    is_required boolean,
    uploaded_by integer,
    uploaded_at timestamp with time zone DEFAULT now(),
    is_verified boolean,
    verified_by integer,
    verified_at timestamp with time zone,
    verification_notes text
);

CREATE SEQUENCE IF NOT EXISTS resignation_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS resignation_notifications (
    id integer NOT NULL,
    resignation_id integer NOT NULL,
    notification_type character varying(50) NOT NULL,
    recipient_id integer NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    is_read boolean,
    read_at timestamp with time zone,
    sent_via character varying(20),
    sent_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS resignation_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS resignation_tasks (
    id integer NOT NULL,
    resignation_id integer NOT NULL,
    task_name character varying(100) NOT NULL,
    task_type character varying(50) NOT NULL,
    description text,
    is_required boolean,
    is_completed boolean,
    completion_date timestamp with time zone,
    completed_by integer,
    completion_notes text,
    checklist_items json,
    due_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS resignation_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS resignation_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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

CREATE SEQUENCE IF NOT EXISTS resignations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS role_assignments (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by character varying(100),
    expires_at timestamp with time zone,
    is_active boolean DEFAULT true,
    is_primary boolean DEFAULT false
);

CREATE SEQUENCE IF NOT EXISTS role_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS role_permissions (
    id integer NOT NULL,
    role_id integer NOT NULL,
    permission_code character varying(100) NOT NULL,
    granted_at timestamp with time zone DEFAULT now(),
    granted_by character varying(100)
);

CREATE SEQUENCE IF NOT EXISTS role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS roles (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    description text,
    level integer DEFAULT 1,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS rpt_export_log (
    id integer NOT NULL,
    template_id integer,
    user_id integer,
    export_time timestamp without time zone,
    format character varying(10),
    filters jsonb,
    row_count integer,
    file_path character varying(255),
    file_size integer,
    ip_address character varying(45),
    status character varying(20),
    error_message text,
    task_id character varying(100)
);

CREATE SEQUENCE IF NOT EXISTS rpt_export_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS rpt_favorite (
    id integer NOT NULL,
    user_id integer NOT NULL,
    template_id integer NOT NULL,
    created_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS rpt_favorite_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS rpt_schedule (
    id integer NOT NULL,
    template_id integer NOT NULL,
    schedule_name character varying(100) NOT NULL,
    cron character varying(50) NOT NULL,
    format character varying(10),
    recipients jsonb,
    last_run timestamp without time zone,
    next_run timestamp without time zone,
    is_active boolean,
    created_by integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS rpt_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS rpt_template (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    module character varying(50) NOT NULL,
    report_code character varying(100) NOT NULL,
    filters jsonb,
    columns jsonb,
    group_by character varying(50),
    chart_type character varying(20),
    is_system boolean,
    created_by integer,
    is_public boolean,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS rpt_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS rpt_user_preset (
    id integer NOT NULL,
    user_id integer NOT NULL,
    template_id integer,
    preset_name character varying(100) NOT NULL,
    preset_type character varying(20) NOT NULL,
    filters jsonb,
    columns jsonb,
    is_default boolean,
    created_at timestamp without time zone
);

CREATE SEQUENCE IF NOT EXISTS rpt_user_preset_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS schedule_management (
    id integer NOT NULL,
    personnel_id integer,
    shift_id integer,
    schedule_date date NOT NULL,
    status character varying(20) DEFAULT 'scheduled'::character varying,
    assigned_by integer,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS schedule_management_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS shift_management (
    id integer NOT NULL,
    shift_code character varying(20) NOT NULL,
    shift_name character varying(100) NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    break_duration integer DEFAULT 0,
    shift_type character varying(20) NOT NULL,
    working_hours integer NOT NULL,
    is_night_shift boolean DEFAULT false,
    is_weekend_shift boolean DEFAULT false,
    is_flexible boolean DEFAULT false,
    rotation_pattern json,
    rotation_cycle_days integer,
    grace_period_minutes integer DEFAULT 15,
    max_late_minutes integer DEFAULT 60,
    max_early_departure_minutes integer DEFAULT 30,
    overtime_threshold_minutes integer DEFAULT 30,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS shift_management_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sn (
    id integer NOT NULL,
    sn character varying(20) NOT NULL,
    device_type character varying(50),
    model character varying(50),
    firmware character varying(20),
    purchase_date date,
    warranty_expiry date,
    status smallint DEFAULT 0,
    location character varying(100),
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sn_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS ssr (
    id bigint NOT NULL,
    user_id integer,
    ssr_type smallint NOT NULL,
    request_date date NOT NULL,
    start_time time without time zone,
    end_time time without time zone,
    reason text,
    status smallint DEFAULT 0,
    approved_by integer,
    approved_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS ssr_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_api_keys (
    id integer NOT NULL,
    api_key character varying(255) NOT NULL,
    name character varying(100) NOT NULL,
    created_by integer,
    is_active boolean DEFAULT true,
    expiry_date date,
    last_used timestamp with time zone,
    usage_count integer DEFAULT 0,
    ip_whitelist text[],
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_api_keys_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_branding (
    id integer NOT NULL,
    company_name character varying(100),
    logo_url character varying(500),
    primary_color character varying(7),
    secondary_color character varying(7),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_branding_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_consent_records (
    id integer NOT NULL,
    user_id integer NOT NULL,
    consent_type character varying(50),
    consented boolean DEFAULT true,
    ip_address character varying(45),
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_consent_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_data_access_logs (
    id bigint NOT NULL,
    user_id integer,
    table_name character varying(100),
    record_id integer,
    action character varying(50),
    accessed_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_data_access_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_db_backups (
    id bigint NOT NULL,
    backup_time timestamp with time zone DEFAULT now(),
    backup_type smallint DEFAULT 0,
    file_path character varying(255),
    file_size bigint,
    status smallint DEFAULT 0,
    created_by character varying(100)
);

CREATE SEQUENCE IF NOT EXISTS sys_db_backups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_email_templates (
    id integer NOT NULL,
    code character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    subject character varying(255),
    body_html text,
    body_text text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_email_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_languages (
    id integer NOT NULL,
    code character varying(10) NOT NULL,
    name character varying(50) NOT NULL,
    is_default boolean DEFAULT false,
    is_active boolean DEFAULT true
);

CREATE SEQUENCE IF NOT EXISTS sys_languages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_licenses (
    id integer NOT NULL,
    license_key character varying(255) NOT NULL,
    license_type smallint DEFAULT 1,
    max_users integer DEFAULT 100,
    max_devices integer DEFAULT 50,
    issued_to character varying(255),
    valid_from timestamp with time zone DEFAULT now(),
    valid_until timestamp with time zone,
    is_active boolean DEFAULT true,
    features jsonb,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_licenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_notifications (
    id integer NOT NULL,
    user_id integer,
    notification_type character varying(50) DEFAULT 'info'::character varying,
    title character varying(200) NOT NULL,
    message text,
    priority character varying(20) DEFAULT 'medium'::character varying,
    is_read boolean DEFAULT false,
    read_at timestamp with time zone,
    link character varying(500),
    dedup_key character varying(200),
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS sys_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_parameters (
    id integer NOT NULL,
    param_key character varying(100) NOT NULL,
    param_value text,
    param_type character varying(20) DEFAULT 'string'::character varying,
    module character varying(50) DEFAULT 'system'::character varying NOT NULL,
    description text,
    is_public boolean DEFAULT false,
    is_encrypted boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    updated_by character varying(100)
);

CREATE SEQUENCE IF NOT EXISTS sys_parameters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_permissions (
    id integer NOT NULL,
    code character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    module character varying(50) DEFAULT 'general'::character varying NOT NULL,
    action character varying(50) DEFAULT 'view'::character varying NOT NULL,
    category character varying(50) DEFAULT 'general'::character varying NOT NULL,
    is_system boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_renewal_log (
    id integer NOT NULL,
    subscription_id integer,
    previous_expiry timestamp with time zone NOT NULL,
    new_expiry timestamp with time zone NOT NULL,
    key_prefix character varying(12),
    activated_by character varying(150),
    ip_address character varying(45),
    activated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_renewal_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_role_permissions (
    id integer NOT NULL,
    role_id integer NOT NULL,
    permission_code character varying(100) NOT NULL,
    granted_at timestamp with time zone DEFAULT now(),
    granted_by character varying(100)
);

CREATE SEQUENCE IF NOT EXISTS sys_role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_roles (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text DEFAULT ''::text NOT NULL,
    level integer DEFAULT 50 NOT NULL,
    is_system boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by character varying(100)
);

CREATE SEQUENCE IF NOT EXISTS sys_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_sso_configs (
    id integer NOT NULL,
    sso_type smallint DEFAULT 0,
    server_url character varying(500),
    bind_dn character varying(255),
    bind_password character varying(255),
    base_dn character varying(255),
    is_active boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_sso_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_subscription (
    id integer NOT NULL,
    installation_id character varying(64) NOT NULL,
    org_name character varying(200) NOT NULL,
    tier character varying(50) DEFAULT 'standard'::character varying,
    max_users integer DEFAULT 50,
    max_employees integer DEFAULT 500,
    max_devices integer DEFAULT 20,
    issue_date date DEFAULT CURRENT_DATE NOT NULL,
    expiry_date timestamp with time zone NOT NULL,
    is_active boolean DEFAULT true,
    notes text,
    created_by character varying(150),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_subscription_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_translations (
    id integer NOT NULL,
    lang_code character varying(10) NOT NULL,
    key character varying(255) NOT NULL,
    value text
);

CREATE SEQUENCE IF NOT EXISTS sys_translations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_user_roles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by character varying(100),
    expires_at timestamp with time zone,
    is_active boolean DEFAULT true,
    is_primary boolean DEFAULT false
);

CREATE SEQUENCE IF NOT EXISTS sys_user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS sys_webhooks (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    url character varying(500) NOT NULL,
    events text[],
    secret_key character varying(255),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS sys_webhooks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS system_company (
    id integer NOT NULL,
    name character varying(200) DEFAULT 'Marconi.ng EPC Limited'::character varying NOT NULL,
    short_name character varying(50),
    industry character varying(100) DEFAULT 'Oil & Gas'::character varying,
    address text,
    city character varying(100),
    state character varying(100),
    country character varying(100) DEFAULT 'Nigeria'::character varying,
    phone character varying(50),
    email character varying(100),
    website character varying(200),
    logo_url character varying(500),
    timezone character varying(50) DEFAULT 'Africa/Lagos'::character varying,
    date_format character varying(20) DEFAULT 'DD/MM/YYYY'::character varying,
    time_format character varying(10) DEFAULT '24h'::character varying,
    fiscal_year_start character varying(5) DEFAULT '01-01'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS system_company_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS training_courses (
    id integer NOT NULL,
    course_code character varying(20) NOT NULL,
    course_name character varying(200) NOT NULL,
    description text,
    duration_hours integer,
    category character varying(50),
    is_mandatory boolean DEFAULT false,
    valid_period_months integer,
    created_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS training_courses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS training_enrollment (
    id integer NOT NULL,
    personnel_id integer,
    course_id integer,
    enrollment_date date,
    completion_date date,
    status character varying(20) DEFAULT 'enrolled'::character varying,
    score numeric(5,2),
    certificate_url character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    expiry_date date,
    personnel_type character varying(20)
);

CREATE SEQUENCE IF NOT EXISTS training_enrollment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS transport (
    id integer NOT NULL,
    type smallint NOT NULL,
    identifier character varying(50) NOT NULL,
    registration_number character varying(50),
    operator character varying(100),
    capacity integer,
    current_pob integer,
    status smallint,
    base_location character varying(100),
    current_location character varying(100),
    fuel_capacity double precision,
    current_fuel double precision,
    flight_hours double precision,
    max_altitude integer,
    max_speed double precision,
    cost_per_hour double precision,
    utilization_rate double precision,
    performance_rating double precision,
    is_available boolean,
    is_maintenance_mode boolean,
    is_inspection_due boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transport_assignments (
    id integer NOT NULL,
    personnel_id integer NOT NULL,
    transport_type character varying(50) NOT NULL,
    transport_name character varying(100) NOT NULL,
    transport_code character varying(20),
    departure_location character varying(100) NOT NULL,
    destination_location character varying(100) NOT NULL,
    departure_time timestamp with time zone NOT NULL,
    arrival_time timestamp with time zone,
    return_time timestamp with time zone,
    seat_number character varying(10),
    cabin_number character varying(20),
    purpose character varying(100),
    status character varying(20),
    booked_at timestamp with time zone DEFAULT now() NOT NULL,
    booked_by integer,
    notes text
);

CREATE SEQUENCE IF NOT EXISTS transport_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS transport_crew (
    id integer NOT NULL,
    transport_id integer NOT NULL,
    personnel_id integer NOT NULL,
    role character varying(50) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    status character varying(20),
    certification_number character varying(50),
    certification_expiry date,
    medical_expiry date,
    experience_hours double precision,
    flight_hours double precision,
    last_flight_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS transport_crew_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS transport_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS transport_inventory (
    id integer NOT NULL,
    transport_id integer NOT NULL,
    item_name character varying(100) NOT NULL,
    item_type character varying(50) NOT NULL,
    item_description text,
    quantity integer,
    unit_of_measure character varying(20),
    location_on_transport character varying(50),
    expiry_date date,
    last_inspected timestamp with time zone,
    condition_status character varying(20),
    replacement_cost double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS transport_inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS transport_maintenance (
    id integer NOT NULL,
    transport_id integer NOT NULL,
    maintenance_type smallint NOT NULL,
    description text NOT NULL,
    scheduled_date timestamp with time zone NOT NULL,
    completed_date timestamp with time zone,
    status character varying(20),
    technician character varying(100),
    cost double precision,
    parts_used jsonb,
    next_maintenance timestamp with time zone,
    maintenance_hours double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS transport_maintenance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS transport_schedule (
    id integer NOT NULL,
    transport_id integer NOT NULL,
    schedule_type character varying(20) NOT NULL,
    departure_location character varying(100) NOT NULL,
    arrival_location character varying(100) NOT NULL,
    departure_time timestamp with time zone NOT NULL,
    arrival_time timestamp with time zone,
    frequency character varying(20),
    end_date timestamp with time zone,
    status character varying(20),
    priority character varying(20),
    passenger_manifest jsonb,
    cargo_manifest jsonb,
    estimated_cost double precision,
    actual_cost double precision,
    weather_requirements character varying(100),
    special_requirements text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS transport_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS user_extensions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    default_role_id integer,
    avatar_url character varying(500),
    phone character varying(20),
    last_login_ip character varying(45),
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS user_extensions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS user_roles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_by integer,
    assigned_at timestamp with time zone DEFAULT now(),
    is_active boolean
);

CREATE SEQUENCE IF NOT EXISTS user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS user_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    session_token character varying(255) NOT NULL,
    refresh_token character varying(255),
    device_info text,
    ip_address character varying(45),
    is_active boolean DEFAULT true,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE IF NOT EXISTS user_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(200),
    hashed_password character varying(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    is_superuser boolean DEFAULT false NOT NULL,
    is_verified boolean DEFAULT false NOT NULL,
    phone character varying(20),
    avatar character varying(500),
    last_login timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_global_admin boolean DEFAULT false
);

CREATE SEQUENCE IF NOT EXISTS users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vendor_compliance (
    id integer NOT NULL,
    vendor_id integer NOT NULL,
    compliance_type character varying(50) NOT NULL,
    compliance_status character varying(20) NOT NULL,
    compliance_date timestamp with time zone NOT NULL,
    expiry_date timestamp with time zone,
    certifying_authority character varying(100),
    certificate_number character varying(100),
    assessment_score double precision,
    assessment_notes text,
    corrective_actions json,
    follow_up_date timestamp with time zone,
    certificate_path character varying(500),
    supporting_documents json,
    assessed_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS vendor_compliance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vendor_contracts (
    id integer NOT NULL,
    vendor_id integer NOT NULL,
    contract_number character varying(50) NOT NULL,
    contract_name character varying(200) NOT NULL,
    contract_type character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'DRAFT'::character varying,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    renewal_date timestamp with time zone,
    notice_period_days integer DEFAULT 30,
    total_value double precision,
    currency character varying(3) DEFAULT 'USD'::character varying,
    payment_terms character varying(100),
    billing_frequency character varying(20),
    sla_requirements json,
    penalty_clauses json,
    scope_of_work text,
    deliverables json,
    key_performance_indicators json,
    contract_manager integer,
    legal_reviewer integer,
    approved_by integer,
    approved_at timestamp with time zone,
    performance_score double precision DEFAULT 0.0,
    compliance_score double precision DEFAULT 0.0,
    last_performance_review timestamp with time zone,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS vendor_contracts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vendors (
    id integer NOT NULL,
    vendor_code character varying(50) NOT NULL,
    vendor_name character varying(200) NOT NULL,
    vendor_type character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    contact_person character varying(100),
    email character varying(100),
    phone character varying(20),
    mobile character varying(20),
    fax character varying(20),
    address_line1 character varying(200),
    address_line2 character varying(200),
    city character varying(100),
    state character varying(100),
    country character varying(100),
    postal_code character varying(20),
    business_registration character varying(100),
    tax_id character varying(50),
    website character varying(200),
    description text,
    services_offered json,
    service_areas json,
    certifications json,
    payment_terms character varying(100),
    credit_limit double precision,
    currency character varying(3) DEFAULT 'USD'::character varying,
    compliance_status character varying(20) DEFAULT 'PENDING_REVIEW'::character varying,
    last_compliance_check timestamp with time zone,
    next_compliance_due timestamp with time zone,
    risk_rating character varying(10),
    performance_score double precision DEFAULT 0.0,
    total_contracts integer DEFAULT 0,
    active_contracts integer DEFAULT 0,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS vendors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vis_blacklist (
    id integer NOT NULL,
    full_name character varying(100),
    id_no character varying(50) NOT NULL,
    phone character varying(20),
    email character varying(100),
    reason character varying(255) NOT NULL,
    added_by integer,
    added_time timestamp with time zone DEFAULT now(),
    is_active boolean
);

CREATE SEQUENCE IF NOT EXISTS vis_blacklist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vis_pre_registration (
    id bigint NOT NULL,
    visitor_id bigint,
    host_emp_id integer NOT NULL,
    visit_date date NOT NULL,
    visit_time_start time without time zone,
    visit_time_end time without time zone,
    purpose character varying(255),
    area_id integer,
    vehicle_no character varying(20),
    qr_code character varying(100) NOT NULL,
    status smallint,
    approval_time timestamp with time zone,
    approval_by integer,
    approval_note character varying(255),
    safety_induction_done boolean,
    induction_doc character varying(255),
    contractor_visitor boolean,
    created_by integer,
    created_time timestamp with time zone DEFAULT now(),
    updated_time timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS vis_pre_registration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vis_type (
    id integer NOT NULL,
    type_name character varying(50) NOT NULL,
    access_level_id integer,
    badge_template character varying(100),
    induction_required boolean,
    default_visit_hours integer,
    auto_checkout boolean,
    mustering_zone_id integer,
    contractor_visitor boolean,
    safety_induction_required boolean,
    created_time timestamp with time zone DEFAULT now(),
    is_active boolean
);

CREATE SEQUENCE IF NOT EXISTS vis_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vis_visit_log (
    id bigint NOT NULL,
    visitor_id bigint NOT NULL,
    pre_reg_id bigint,
    host_emp_id integer,
    check_in_time timestamp with time zone NOT NULL,
    check_out_time timestamp with time zone,
    card_no character varying(20),
    device_sn character varying(20),
    badge_printed boolean,
    status smallint,
    area_id integer,
    mustering_zone_id integer,
    mustering_status smallint,
    overstay_alert_sent boolean,
    created_by integer,
    created_time timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS vis_visit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS vis_visitor (
    id bigint NOT NULL,
    visitor_code character varying(20) NOT NULL,
    full_name character varying(100) NOT NULL,
    phone character varying(20),
    email character varying(100),
    company character varying(100),
    id_type smallint,
    id_no character varying(50),
    photo character varying(255),
    signature character varying(255),
    visitor_type_id integer,
    is_blacklist boolean,
    blacklist_reason character varying(255),
    vendor_id integer,
    safety_induction_done boolean,
    induction_doc character varying(255),
    created_time timestamp with time zone DEFAULT now(),
    updated_time timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS vis_visitor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS zone_personnel_assignments (
    id integer NOT NULL,
    zone_id integer NOT NULL,
    personnel_id integer NOT NULL,
    role character varying(100),
    access_level character varying(20) DEFAULT 'STANDARD'::character varying,
    is_primary_zone boolean DEFAULT false,
    assigned_at timestamp with time zone DEFAULT now(),
    unassigned_at timestamp with time zone,
    is_permanent boolean DEFAULT false,
    access_times jsonb,
    device_access jsonb,
    safety_briefing_completed boolean DEFAULT false,
    safety_briefing_date timestamp with time zone,
    certifications_verified boolean DEFAULT false,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    approved_by integer,
    approved_at timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS zone_personnel_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS zone_personnel_tracking (
    id integer NOT NULL,
    zone_id integer NOT NULL,
    personnel_id integer,
    emp_code character varying(20) NOT NULL,
    device_sn character varying(50) NOT NULL,
    event_type character varying(20) DEFAULT 'CLOCK_IN'::character varying,
    punch_time timestamp with time zone NOT NULL,
    previous_zone_id integer,
    created_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS zone_personnel_tracking_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS zone_reader_assignments (
    id integer NOT NULL,
    zone_id integer NOT NULL,
    reader_id integer NOT NULL,
    assignment_type character varying(50) DEFAULT 'PERMANENT'::character varying,
    status character varying(20) DEFAULT 'active'::character varying,
    is_primary boolean DEFAULT false,
    assigned_at timestamp with time zone DEFAULT now(),
    unassigned_at timestamp with time zone,
    expires_at timestamp with time zone,
    access_level character varying(20) DEFAULT 'STANDARD'::character varying,
    access_schedule jsonb,
    reader_config jsonb,
    last_heartbeat timestamp with time zone,
    last_activity timestamp with time zone,
    error_count integer DEFAULT 0,
    notes text,
    assigned_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS zone_reader_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS zones (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(20) NOT NULL,
    zone_type character varying(30) DEFAULT 'WORK_AREA'::character varying NOT NULL,
    description text,
    status character varying(20) DEFAULT 'active'::character varying,
    state character varying(100),
    address text,
    latitude character varying(20),
    longitude character varying(20),
    max_capacity integer,
    current_occupancy integer DEFAULT 0,
    current_personnel_count integer DEFAULT 0,
    hazard_level character varying(20) DEFAULT 'LOW'::character varying,
    safety_level character varying(20) DEFAULT 'NORMAL'::character varying,
    access_level character varying(20) DEFAULT 'RESTRICTED'::character varying,
    device_count integer DEFAULT 0,
    zone_manager_id integer,
    contact_person character varying(255),
    contact_phone character varying(20),
    zkteco_sync_enabled boolean DEFAULT true,
    last_sync_at timestamp with time zone,
    floor_plan_url character varying(500),
    floor_plan_file_path character varying(500),
    floor_plan_filename character varying(255),
    floor_plan_uploaded_at timestamp with time zone,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    parent_zone_id integer,
    display_color character varying(20),
    tile_position character varying(20) DEFAULT 'auto'::character varying,
    evac_point character varying(100),
    evac_gps character varying(50),
    reader_sn character varying(50),
    map_x double precision,
    map_y double precision,
    map_connections text
);

CREATE SEQUENCE IF NOT EXISTS zones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE ONLY acc_antipassback ALTER COLUMN id SET DEFAULT nextval('acc_antipassback_id_seq'::regclass);

ALTER TABLE ONLY acc_door ALTER COLUMN id SET DEFAULT nextval('acc_door_id_seq'::regclass);

ALTER TABLE ONLY acc_event ALTER COLUMN id SET DEFAULT nextval('acc_event_id_seq'::regclass);

ALTER TABLE ONLY acc_first_card ALTER COLUMN id SET DEFAULT nextval('acc_first_card_id_seq'::regclass);

ALTER TABLE ONLY acc_guard_tour ALTER COLUMN id SET DEFAULT nextval('acc_guard_tour_id_seq'::regclass);

ALTER TABLE ONLY acc_guard_tour_checkpoint ALTER COLUMN id SET DEFAULT nextval('acc_guard_tour_checkpoint_id_seq'::regclass);

ALTER TABLE ONLY acc_guard_tour_log ALTER COLUMN id SET DEFAULT nextval('acc_guard_tour_log_id_seq'::regclass);

ALTER TABLE ONLY acc_guard_tour_schedule ALTER COLUMN id SET DEFAULT nextval('acc_guard_tour_schedule_id_seq'::regclass);

ALTER TABLE ONLY acc_interlock_door ALTER COLUMN id SET DEFAULT nextval('acc_interlock_door_id_seq'::regclass);

ALTER TABLE ONLY acc_interlock_group ALTER COLUMN id SET DEFAULT nextval('acc_interlock_group_id_seq'::regclass);

ALTER TABLE ONLY acc_level ALTER COLUMN id SET DEFAULT nextval('acc_level_id_seq'::regclass);

ALTER TABLE ONLY acc_level_door ALTER COLUMN id SET DEFAULT nextval('acc_level_door_id_seq'::regclass);

ALTER TABLE ONLY acc_linkage ALTER COLUMN id SET DEFAULT nextval('acc_linkage_id_seq'::regclass);

ALTER TABLE ONLY acc_multi_card ALTER COLUMN id SET DEFAULT nextval('acc_multi_card_id_seq'::regclass);

ALTER TABLE ONLY acc_multi_card_user ALTER COLUMN id SET DEFAULT nextval('acc_multi_card_user_id_seq'::regclass);

ALTER TABLE ONLY acc_passback_rule ALTER COLUMN id SET DEFAULT nextval('acc_passback_rule_id_seq'::regclass);

ALTER TABLE ONLY acc_timezone ALTER COLUMN id SET DEFAULT nextval('acc_timezone_id_seq'::regclass);

ALTER TABLE ONLY acc_userauthorize ALTER COLUMN id SET DEFAULT nextval('acc_userauthorize_id_seq'::regclass);

ALTER TABLE ONLY acc_visitor_access ALTER COLUMN id SET DEFAULT nextval('acc_visitor_access_id_seq'::regclass);

ALTER TABLE ONLY acc_zone ALTER COLUMN id SET DEFAULT nextval('acc_zone_id_seq'::regclass);

ALTER TABLE ONLY acc_zone_door ALTER COLUMN id SET DEFAULT nextval('acc_zone_door_id_seq'::regclass);

ALTER TABLE ONLY access_logs ALTER COLUMN id SET DEFAULT nextval('access_logs_id_seq'::regclass);

ALTER TABLE ONLY acgroup ALTER COLUMN id SET DEFAULT nextval('acgroup_id_seq'::regclass);

ALTER TABLE ONLY appraisal_cycles ALTER COLUMN id SET DEFAULT nextval('appraisal_cycles_id_seq'::regclass);

ALTER TABLE ONLY att_exception ALTER COLUMN id SET DEFAULT nextval('att_exception_id_seq'::regclass);

ALTER TABLE ONLY att_holiday ALTER COLUMN id SET DEFAULT nextval('att_holiday_id_seq'::regclass);

ALTER TABLE ONLY att_leave ALTER COLUMN id SET DEFAULT nextval('att_leave_id_seq1'::regclass);

ALTER TABLE ONLY att_leave_old ALTER COLUMN id SET DEFAULT nextval('att_leave_id_seq'::regclass);

ALTER TABLE ONLY att_leave_type ALTER COLUMN id SET DEFAULT nextval('att_leave_type_id_seq'::regclass);

ALTER TABLE ONLY att_manual_log ALTER COLUMN id SET DEFAULT nextval('att_manual_log_id_seq'::regclass);

ALTER TABLE ONLY att_overtime ALTER COLUMN id SET DEFAULT nextval('att_overtime_id_seq'::regclass);

ALTER TABLE ONLY att_overtime_rule ALTER COLUMN id SET DEFAULT nextval('att_overtime_rule_id_seq'::regclass);

ALTER TABLE ONLY att_report ALTER COLUMN id SET DEFAULT nextval('att_report_id_seq'::regclass);

ALTER TABLE ONLY att_schedule ALTER COLUMN id SET DEFAULT nextval('att_schedule_id_seq'::regclass);

ALTER TABLE ONLY att_shift ALTER COLUMN id SET DEFAULT nextval('att_shift_id_seq'::regclass);

ALTER TABLE ONLY att_shift_timetable ALTER COLUMN id SET DEFAULT nextval('att_shift_timetable_id_seq'::regclass);

ALTER TABLE ONLY att_timetable ALTER COLUMN id SET DEFAULT nextval('att_timetable_id_seq'::regclass);

ALTER TABLE ONLY attendance_logs ALTER COLUMN id SET DEFAULT nextval('attendance_logs_id_seq'::regclass);

ALTER TABLE ONLY attribute_templates ALTER COLUMN id SET DEFAULT nextval('attribute_templates_id_seq'::regclass);

ALTER TABLE ONLY attribute_validations ALTER COLUMN id SET DEFAULT nextval('attribute_validations_id_seq'::regclass);

ALTER TABLE ONLY auth_permission ALTER COLUMN id SET DEFAULT nextval('auth_permission_id_seq'::regclass);

ALTER TABLE ONLY auth_role ALTER COLUMN id SET DEFAULT nextval('auth_role_id_seq'::regclass);

ALTER TABLE ONLY auth_role_permission ALTER COLUMN id SET DEFAULT nextval('auth_role_permission_id_seq'::regclass);

ALTER TABLE ONLY auth_user ALTER COLUMN id SET DEFAULT nextval('auth_user_id_seq'::regclass);

ALTER TABLE ONLY auth_user_role ALTER COLUMN id SET DEFAULT nextval('auth_user_role_id_seq'::regclass);

ALTER TABLE ONLY base_company ALTER COLUMN id SET DEFAULT nextval('base_company_id_seq'::regclass);

ALTER TABLE ONLY base_operationlog ALTER COLUMN id SET DEFAULT nextval('base_operationlog_id_seq'::regclass);

ALTER TABLE ONLY benefit_plans ALTER COLUMN id SET DEFAULT nextval('benefit_plans_id_seq'::regclass);

ALTER TABLE ONLY biometric_devices ALTER COLUMN id SET DEFAULT nextval('biometric_devices_id_seq'::regclass);

ALTER TABLE ONLY biometric_enrollment_sessions ALTER COLUMN id SET DEFAULT nextval('biometric_enrollment_sessions_id_seq'::regclass);

ALTER TABLE ONLY biometric_templates ALTER COLUMN id SET DEFAULT nextval('biometric_templates_id_seq'::regclass);

ALTER TABLE ONLY biometric_verification_logs ALTER COLUMN id SET DEFAULT nextval('biometric_verification_logs_id_seq'::regclass);

ALTER TABLE ONLY biotime_access_levels ALTER COLUMN id SET DEFAULT nextval('biotime_access_levels_id_seq'::regclass);

ALTER TABLE ONLY biotime_access_schedules ALTER COLUMN id SET DEFAULT nextval('biotime_access_schedules_id_seq'::regclass);

ALTER TABLE ONLY biotime_biometric_templates ALTER COLUMN id SET DEFAULT nextval('biotime_biometric_templates_id_seq'::regclass);

ALTER TABLE ONLY biotime_conflict_resolutions ALTER COLUMN id SET DEFAULT nextval('biotime_conflict_resolutions_id_seq'::regclass);

ALTER TABLE ONLY biotime_device_groups ALTER COLUMN id SET DEFAULT nextval('biotime_device_groups_id_seq'::regclass);

ALTER TABLE ONLY biotime_devices ALTER COLUMN id SET DEFAULT nextval('biotime_devices_id_seq'::regclass);

ALTER TABLE ONLY biotime_sync_logs ALTER COLUMN id SET DEFAULT nextval('biotime_sync_logs_id_seq'::regclass);

ALTER TABLE ONLY certification_audits ALTER COLUMN id SET DEFAULT nextval('certification_audits_id_seq'::regclass);

ALTER TABLE ONLY certification_templates ALTER COLUMN id SET DEFAULT nextval('certification_templates_id_seq'::regclass);

ALTER TABLE ONLY certifications ALTER COLUMN id SET DEFAULT nextval('certifications_id_seq'::regclass);

ALTER TABLE ONLY checkinout ALTER COLUMN id SET DEFAULT nextval('checkinout_id_seq'::regclass);

ALTER TABLE ONLY contract_assignments ALTER COLUMN id SET DEFAULT nextval('contract_assignments_id_seq'::regclass);

ALTER TABLE ONLY contractor_compliance ALTER COLUMN id SET DEFAULT nextval('contractor_compliance_id_seq'::regclass);

ALTER TABLE ONLY contractors ALTER COLUMN id SET DEFAULT nextval('contractors_id_seq'::regclass);

ALTER TABLE ONLY custom_attribute_values ALTER COLUMN id SET DEFAULT nextval('custom_attribute_values_id_seq'::regclass);

ALTER TABLE ONLY custom_attributes ALTER COLUMN id SET DEFAULT nextval('custom_attributes_id_seq'::regclass);

ALTER TABLE ONLY department_personnel ALTER COLUMN id SET DEFAULT nextval('department_personnel_id_seq'::regclass);

ALTER TABLE ONLY departments ALTER COLUMN id SET DEFAULT nextval('departments_id_seq'::regclass);

ALTER TABLE ONLY device_blacklist ALTER COLUMN id SET DEFAULT nextval('device_blacklist_id_seq'::regclass);

ALTER TABLE ONLY device_events ALTER COLUMN id SET DEFAULT nextval('device_events_id_seq'::regclass);

ALTER TABLE ONLY device_maintenance ALTER COLUMN id SET DEFAULT nextval('device_maintenance_id_seq'::regclass);

ALTER TABLE ONLY device_schedules ALTER COLUMN id SET DEFAULT nextval('device_schedules_id_seq'::regclass);

ALTER TABLE ONLY devicemap ALTER COLUMN id SET DEFAULT nextval('devicemap_id_seq'::regclass);

ALTER TABLE ONLY devices ALTER COLUMN id SET DEFAULT nextval('devices_id_seq'::regclass);

ALTER TABLE ONLY disciplinary_cases ALTER COLUMN id SET DEFAULT nextval('disciplinary_cases_id_seq'::regclass);

ALTER TABLE ONLY emergency_device ALTER COLUMN id SET DEFAULT nextval('emergency_device_id_seq'::regclass);

ALTER TABLE ONLY emergency_device_command ALTER COLUMN id SET DEFAULT nextval('emergency_device_command_id_seq'::regclass);

ALTER TABLE ONLY emergency_device_enhanced ALTER COLUMN id SET DEFAULT nextval('emergency_device_enhanced_id_seq'::regclass);

ALTER TABLE ONLY emergency_device_maintenance ALTER COLUMN id SET DEFAULT nextval('emergency_device_maintenance_id_seq'::regclass);

ALTER TABLE ONLY emergency_event ALTER COLUMN id SET DEFAULT nextval('emergency_event_id_seq'::regclass);

ALTER TABLE ONLY emergency_event_enhanced ALTER COLUMN id SET DEFAULT nextval('emergency_event_enhanced_id_seq'::regclass);

ALTER TABLE ONLY emergency_notification ALTER COLUMN id SET DEFAULT nextval('emergency_notification_id_seq'::regclass);

ALTER TABLE ONLY emergency_notification_enhanced ALTER COLUMN id SET DEFAULT nextval('emergency_notification_enhanced_id_seq'::regclass);

ALTER TABLE ONLY emergency_panic_log ALTER COLUMN id SET DEFAULT nextval('emergency_panic_log_id_seq'::regclass);

ALTER TABLE ONLY emergency_panic_log_enhanced ALTER COLUMN id SET DEFAULT nextval('emergency_panic_log_enhanced_id_seq'::regclass);

ALTER TABLE ONLY emergency_plan ALTER COLUMN id SET DEFAULT nextval('emergency_plan_id_seq'::regclass);

ALTER TABLE ONLY emergency_template ALTER COLUMN id SET DEFAULT nextval('emergency_template_id_seq'::regclass);

ALTER TABLE ONLY employee_benefits ALTER COLUMN id SET DEFAULT nextval('employee_benefits_id_seq'::regclass);

ALTER TABLE ONLY employment_contracts ALTER COLUMN id SET DEFAULT nextval('employment_contracts_id_seq'::regclass);

ALTER TABLE ONLY events ALTER COLUMN id SET DEFAULT nextval('events_id_seq'::regclass);

ALTER TABLE ONLY face ALTER COLUMN id SET DEFAULT nextval('face_id_seq'::regclass);

ALTER TABLE ONLY fingerprint ALTER COLUMN id SET DEFAULT nextval('fingerprint_id_seq'::regclass);

ALTER TABLE ONLY flight_log ALTER COLUMN id SET DEFAULT nextval('flight_log_id_seq'::regclass);

ALTER TABLE ONLY holiday ALTER COLUMN id SET DEFAULT nextval('holiday_id_seq'::regclass);

ALTER TABLE ONLY hr_integration_config ALTER COLUMN id SET DEFAULT nextval('hr_integration_config_id_seq'::regclass);

ALTER TABLE ONLY hr_sync_log ALTER COLUMN id SET DEFAULT nextval('hr_sync_log_id_seq'::regclass);

ALTER TABLE ONLY iclock_bio_template ALTER COLUMN id SET DEFAULT nextval('iclock_bio_template_id_seq'::regclass);

ALTER TABLE ONLY iclock_devcmd ALTER COLUMN id SET DEFAULT nextval('iclock_devcmd_id_seq'::regclass);

ALTER TABLE ONLY iclock_operlog ALTER COLUMN id SET DEFAULT nextval('iclock_operlog_id_seq'::regclass);

ALTER TABLE ONLY iclock_terminal ALTER COLUMN id SET DEFAULT nextval('iclock_terminal_id_seq'::regclass);

ALTER TABLE ONLY iclock_transaction ALTER COLUMN id SET DEFAULT nextval('iclock_transaction_id_seq'::regclass);

ALTER TABLE ONLY leave_balance ALTER COLUMN id SET DEFAULT nextval('leave_balance_id_seq'::regclass);

ALTER TABLE ONLY leave_blackout ALTER COLUMN id SET DEFAULT nextval('leave_blackout_id_seq'::regclass);

ALTER TABLE ONLY leave_management ALTER COLUMN id SET DEFAULT nextval('leave_management_id_seq'::regclass);

ALTER TABLE ONLY manifest_entry ALTER COLUMN id SET DEFAULT nextval('manifest_entry_id_seq'::regclass);

ALTER TABLE ONLY mtd_audit_log ALTER COLUMN id SET DEFAULT nextval('mtd_audit_log_id_seq'::regclass);

ALTER TABLE ONLY mtd_cert_type ALTER COLUMN id SET DEFAULT nextval('mtd_cert_type_id_seq'::regclass);

ALTER TABLE ONLY mtd_certification ALTER COLUMN id SET DEFAULT nextval('mtd_certification_id_seq'::regclass);

ALTER TABLE ONLY mtd_compliance_log ALTER COLUMN id SET DEFAULT nextval('mtd_compliance_log_id_seq'::regclass);

ALTER TABLE ONLY mtd_induction_record ALTER COLUMN id SET DEFAULT nextval('mtd_induction_record_id_seq'::regclass);

ALTER TABLE ONLY mtd_induction_template ALTER COLUMN id SET DEFAULT nextval('mtd_induction_template_id_seq'::regclass);

ALTER TABLE ONLY mtd_medical_record ALTER COLUMN id SET DEFAULT nextval('mtd_medical_record_id_seq'::regclass);

ALTER TABLE ONLY mtd_ppe_issue ALTER COLUMN id SET DEFAULT nextval('mtd_ppe_issue_id_seq'::regclass);

ALTER TABLE ONLY mtd_ppe_type ALTER COLUMN id SET DEFAULT nextval('mtd_ppe_type_id_seq'::regclass);

ALTER TABLE ONLY mtg_action_item ALTER COLUMN id SET DEFAULT nextval('mtg_action_item_id_seq'::regclass);

ALTER TABLE ONLY mtg_attendance ALTER COLUMN id SET DEFAULT nextval('mtg_attendance_id_seq'::regclass);

ALTER TABLE ONLY mtg_attendee ALTER COLUMN id SET DEFAULT nextval('mtg_attendee_id_seq'::regclass);

ALTER TABLE ONLY mtg_booking ALTER COLUMN id SET DEFAULT nextval('mtg_booking_id_seq'::regclass);

ALTER TABLE ONLY mtg_equipment ALTER COLUMN id SET DEFAULT nextval('mtg_equipment_id_seq'::regclass);

ALTER TABLE ONLY mtg_minutes ALTER COLUMN id SET DEFAULT nextval('mtg_minutes_id_seq'::regclass);

ALTER TABLE ONLY mtg_room ALTER COLUMN id SET DEFAULT nextval('mtg_room_id_seq'::regclass);

ALTER TABLE ONLY mustering_drill_schedule ALTER COLUMN id SET DEFAULT nextval('mustering_drill_schedule_id_seq'::regclass);

ALTER TABLE ONLY mustering_escalation_record ALTER COLUMN id SET DEFAULT nextval('mustering_escalation_record_id_seq'::regclass);

ALTER TABLE ONLY mustering_event ALTER COLUMN id SET DEFAULT nextval('mustering_event_id_seq'::regclass);

ALTER TABLE ONLY mustering_expected ALTER COLUMN id SET DEFAULT nextval('mustering_expected_id_seq'::regclass);

ALTER TABLE ONLY mustering_log ALTER COLUMN id SET DEFAULT nextval('mustering_log_id_seq'::regclass);

ALTER TABLE ONLY mustering_search_sweep ALTER COLUMN id SET DEFAULT nextval('mustering_search_sweep_id_seq'::regclass);

ALTER TABLE ONLY mustering_template ALTER COLUMN id SET DEFAULT nextval('mustering_template_id_seq'::regclass);

ALTER TABLE ONLY onboarding_checklists ALTER COLUMN id SET DEFAULT nextval('onboarding_checklists_id_seq'::regclass);

ALTER TABLE ONLY onboarding_documents ALTER COLUMN id SET DEFAULT nextval('onboarding_documents_id_seq'::regclass);

ALTER TABLE ONLY onboarding_notifications ALTER COLUMN id SET DEFAULT nextval('onboarding_notifications_id_seq'::regclass);

ALTER TABLE ONLY onboarding_task ALTER COLUMN id SET DEFAULT nextval('onboarding_task_id_seq'::regclass);

ALTER TABLE ONLY onboarding_tasks ALTER COLUMN id SET DEFAULT nextval('onboarding_tasks_id_seq'::regclass);

ALTER TABLE ONLY onboarding_templates ALTER COLUMN id SET DEFAULT nextval('onboarding_templates_id_seq'::regclass);

ALTER TABLE ONLY onboardings ALTER COLUMN id SET DEFAULT nextval('onboardings_id_seq'::regclass);

ALTER TABLE ONLY overtime_management ALTER COLUMN id SET DEFAULT nextval('overtime_management_id_seq'::regclass);

ALTER TABLE ONLY overtime_record ALTER COLUMN id SET DEFAULT nextval('overtime_record_id_seq'::regclass);

ALTER TABLE ONLY overtime_rule ALTER COLUMN id SET DEFAULT nextval('overtime_rule_id_seq'::regclass);

ALTER TABLE ONLY overtime_rules ALTER COLUMN id SET DEFAULT nextval('overtime_rules_id_seq'::regclass);

ALTER TABLE ONLY pay_attendance_mapping ALTER COLUMN id SET DEFAULT nextval('pay_attendance_mapping_id_seq'::regclass);

ALTER TABLE ONLY pay_audit_log ALTER COLUMN id SET DEFAULT nextval('pay_audit_log_id_seq'::regclass);

ALTER TABLE ONLY pay_bank_config ALTER COLUMN id SET DEFAULT nextval('pay_bank_config_id_seq'::regclass);

ALTER TABLE ONLY pay_calculation_log ALTER COLUMN id SET DEFAULT nextval('pay_calculation_log_id_seq'::regclass);

ALTER TABLE ONLY pay_contractor_rate ALTER COLUMN id SET DEFAULT nextval('pay_contractor_rate_id_seq'::regclass);

ALTER TABLE ONLY pay_item ALTER COLUMN id SET DEFAULT nextval('pay_item_id_seq'::regclass);

ALTER TABLE ONLY pay_loan ALTER COLUMN id SET DEFAULT nextval('pay_loan_id_seq'::regclass);

ALTER TABLE ONLY pay_loan_deduction ALTER COLUMN id SET DEFAULT nextval('pay_loan_deduction_id_seq'::regclass);

ALTER TABLE ONLY pay_payslip_template ALTER COLUMN id SET DEFAULT nextval('pay_payslip_template_id_seq'::regclass);

ALTER TABLE ONLY pay_period ALTER COLUMN id SET DEFAULT nextval('pay_period_id_seq'::regclass);

ALTER TABLE ONLY pay_salary ALTER COLUMN id SET DEFAULT nextval('pay_salary_id_seq'::regclass);

ALTER TABLE ONLY pay_salary_item ALTER COLUMN id SET DEFAULT nextval('pay_salary_item_id_seq'::regclass);

ALTER TABLE ONLY pay_structure ALTER COLUMN id SET DEFAULT nextval('pay_structure_id_seq'::regclass);

ALTER TABLE ONLY pay_structure_assign ALTER COLUMN id SET DEFAULT nextval('pay_structure_assign_id_seq'::regclass);

ALTER TABLE ONLY pay_zone_allowance ALTER COLUMN id SET DEFAULT nextval('pay_zone_allowance_id_seq'::regclass);

ALTER TABLE ONLY performance_appraisals ALTER COLUMN id SET DEFAULT nextval('performance_appraisals_id_seq'::regclass);

ALTER TABLE ONLY permissions ALTER COLUMN id SET DEFAULT nextval('permissions_id_seq'::regclass);

ALTER TABLE ONLY personnel ALTER COLUMN id SET DEFAULT nextval('personnel_id_seq'::regclass);

ALTER TABLE ONLY personnel_area ALTER COLUMN id SET DEFAULT nextval('personnel_area_id_seq'::regclass);

ALTER TABLE ONLY personnel_assignments ALTER COLUMN id SET DEFAULT nextval('personnel_assignments_id_seq'::regclass);

ALTER TABLE ONLY personnel_department ALTER COLUMN id SET DEFAULT nextval('personnel_department_id_seq'::regclass);

ALTER TABLE ONLY personnel_employee ALTER COLUMN id SET DEFAULT nextval('personnel_employee_id_seq'::regclass);

ALTER TABLE ONLY pob_status ALTER COLUMN id SET DEFAULT nextval('pob_status_id_seq'::regclass);

ALTER TABLE ONLY position_assignments ALTER COLUMN id SET DEFAULT nextval('position_assignments_id_seq'::regclass);

ALTER TABLE ONLY position_levels ALTER COLUMN id SET DEFAULT nextval('position_levels_id_seq'::regclass);

ALTER TABLE ONLY position_templates ALTER COLUMN id SET DEFAULT nextval('position_templates_id_seq'::regclass);

ALTER TABLE ONLY positions ALTER COLUMN id SET DEFAULT nextval('positions_id_seq'::regclass);

ALTER TABLE ONLY promotion_transfers ALTER COLUMN id SET DEFAULT nextval('promotion_transfers_id_seq'::regclass);

ALTER TABLE ONLY resignation_documents ALTER COLUMN id SET DEFAULT nextval('resignation_documents_id_seq'::regclass);

ALTER TABLE ONLY resignation_notifications ALTER COLUMN id SET DEFAULT nextval('resignation_notifications_id_seq'::regclass);

ALTER TABLE ONLY resignation_tasks ALTER COLUMN id SET DEFAULT nextval('resignation_tasks_id_seq'::regclass);

ALTER TABLE ONLY resignation_templates ALTER COLUMN id SET DEFAULT nextval('resignation_templates_id_seq'::regclass);

ALTER TABLE ONLY resignations ALTER COLUMN id SET DEFAULT nextval('resignations_id_seq'::regclass);

ALTER TABLE ONLY role_assignments ALTER COLUMN id SET DEFAULT nextval('role_assignments_id_seq'::regclass);

ALTER TABLE ONLY role_permissions ALTER COLUMN id SET DEFAULT nextval('role_permissions_id_seq'::regclass);

ALTER TABLE ONLY roles ALTER COLUMN id SET DEFAULT nextval('roles_id_seq'::regclass);

ALTER TABLE ONLY rpt_export_log ALTER COLUMN id SET DEFAULT nextval('rpt_export_log_id_seq'::regclass);

ALTER TABLE ONLY rpt_favorite ALTER COLUMN id SET DEFAULT nextval('rpt_favorite_id_seq'::regclass);

ALTER TABLE ONLY rpt_schedule ALTER COLUMN id SET DEFAULT nextval('rpt_schedule_id_seq'::regclass);

ALTER TABLE ONLY rpt_template ALTER COLUMN id SET DEFAULT nextval('rpt_template_id_seq'::regclass);

ALTER TABLE ONLY rpt_user_preset ALTER COLUMN id SET DEFAULT nextval('rpt_user_preset_id_seq'::regclass);

ALTER TABLE ONLY schedule_management ALTER COLUMN id SET DEFAULT nextval('schedule_management_id_seq'::regclass);

ALTER TABLE ONLY shift_management ALTER COLUMN id SET DEFAULT nextval('shift_management_id_seq'::regclass);

ALTER TABLE ONLY sn ALTER COLUMN id SET DEFAULT nextval('sn_id_seq'::regclass);

ALTER TABLE ONLY ssr ALTER COLUMN id SET DEFAULT nextval('ssr_id_seq'::regclass);

ALTER TABLE ONLY sys_api_keys ALTER COLUMN id SET DEFAULT nextval('sys_api_keys_id_seq'::regclass);

ALTER TABLE ONLY sys_branding ALTER COLUMN id SET DEFAULT nextval('sys_branding_id_seq'::regclass);

ALTER TABLE ONLY sys_consent_records ALTER COLUMN id SET DEFAULT nextval('sys_consent_records_id_seq'::regclass);

ALTER TABLE ONLY sys_data_access_logs ALTER COLUMN id SET DEFAULT nextval('sys_data_access_logs_id_seq'::regclass);

ALTER TABLE ONLY sys_db_backups ALTER COLUMN id SET DEFAULT nextval('sys_db_backups_id_seq'::regclass);

ALTER TABLE ONLY sys_email_templates ALTER COLUMN id SET DEFAULT nextval('sys_email_templates_id_seq'::regclass);

ALTER TABLE ONLY sys_languages ALTER COLUMN id SET DEFAULT nextval('sys_languages_id_seq'::regclass);

ALTER TABLE ONLY sys_licenses ALTER COLUMN id SET DEFAULT nextval('sys_licenses_id_seq'::regclass);

ALTER TABLE ONLY sys_notifications ALTER COLUMN id SET DEFAULT nextval('sys_notifications_id_seq'::regclass);

ALTER TABLE ONLY sys_parameters ALTER COLUMN id SET DEFAULT nextval('sys_parameters_id_seq'::regclass);

ALTER TABLE ONLY sys_permissions ALTER COLUMN id SET DEFAULT nextval('sys_permissions_id_seq'::regclass);

ALTER TABLE ONLY sys_renewal_log ALTER COLUMN id SET DEFAULT nextval('sys_renewal_log_id_seq'::regclass);

ALTER TABLE ONLY sys_role_permissions ALTER COLUMN id SET DEFAULT nextval('sys_role_permissions_id_seq'::regclass);

ALTER TABLE ONLY sys_roles ALTER COLUMN id SET DEFAULT nextval('sys_roles_id_seq'::regclass);

ALTER TABLE ONLY sys_sso_configs ALTER COLUMN id SET DEFAULT nextval('sys_sso_configs_id_seq'::regclass);

ALTER TABLE ONLY sys_subscription ALTER COLUMN id SET DEFAULT nextval('sys_subscription_id_seq'::regclass);

ALTER TABLE ONLY sys_translations ALTER COLUMN id SET DEFAULT nextval('sys_translations_id_seq'::regclass);

ALTER TABLE ONLY sys_user_roles ALTER COLUMN id SET DEFAULT nextval('sys_user_roles_id_seq'::regclass);

ALTER TABLE ONLY sys_webhooks ALTER COLUMN id SET DEFAULT nextval('sys_webhooks_id_seq'::regclass);

ALTER TABLE ONLY system_company ALTER COLUMN id SET DEFAULT nextval('system_company_id_seq'::regclass);

ALTER TABLE ONLY training_courses ALTER COLUMN id SET DEFAULT nextval('training_courses_id_seq'::regclass);

ALTER TABLE ONLY training_enrollment ALTER COLUMN id SET DEFAULT nextval('training_enrollment_id_seq'::regclass);

ALTER TABLE ONLY transport ALTER COLUMN id SET DEFAULT nextval('transport_id_seq'::regclass);

ALTER TABLE ONLY transport_assignments ALTER COLUMN id SET DEFAULT nextval('transport_assignments_id_seq'::regclass);

ALTER TABLE ONLY transport_crew ALTER COLUMN id SET DEFAULT nextval('transport_crew_id_seq'::regclass);

ALTER TABLE ONLY transport_inventory ALTER COLUMN id SET DEFAULT nextval('transport_inventory_id_seq'::regclass);

ALTER TABLE ONLY transport_maintenance ALTER COLUMN id SET DEFAULT nextval('transport_maintenance_id_seq'::regclass);

ALTER TABLE ONLY transport_schedule ALTER COLUMN id SET DEFAULT nextval('transport_schedule_id_seq'::regclass);

ALTER TABLE ONLY user_extensions ALTER COLUMN id SET DEFAULT nextval('user_extensions_id_seq'::regclass);

ALTER TABLE ONLY user_roles ALTER COLUMN id SET DEFAULT nextval('user_roles_id_seq'::regclass);

ALTER TABLE ONLY user_sessions ALTER COLUMN id SET DEFAULT nextval('user_sessions_id_seq'::regclass);

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);

ALTER TABLE ONLY vendor_compliance ALTER COLUMN id SET DEFAULT nextval('vendor_compliance_id_seq'::regclass);

ALTER TABLE ONLY vendor_contracts ALTER COLUMN id SET DEFAULT nextval('vendor_contracts_id_seq'::regclass);

ALTER TABLE ONLY vendors ALTER COLUMN id SET DEFAULT nextval('vendors_id_seq'::regclass);

ALTER TABLE ONLY vis_blacklist ALTER COLUMN id SET DEFAULT nextval('vis_blacklist_id_seq'::regclass);

ALTER TABLE ONLY vis_pre_registration ALTER COLUMN id SET DEFAULT nextval('vis_pre_registration_id_seq'::regclass);

ALTER TABLE ONLY vis_type ALTER COLUMN id SET DEFAULT nextval('vis_type_id_seq'::regclass);

ALTER TABLE ONLY vis_visit_log ALTER COLUMN id SET DEFAULT nextval('vis_visit_log_id_seq'::regclass);

ALTER TABLE ONLY vis_visitor ALTER COLUMN id SET DEFAULT nextval('vis_visitor_id_seq'::regclass);

ALTER TABLE ONLY zone_personnel_assignments ALTER COLUMN id SET DEFAULT nextval('zone_personnel_assignments_id_seq'::regclass);

ALTER TABLE ONLY zone_personnel_tracking ALTER COLUMN id SET DEFAULT nextval('zone_personnel_tracking_id_seq'::regclass);

ALTER TABLE ONLY zone_reader_assignments ALTER COLUMN id SET DEFAULT nextval('zone_reader_assignments_id_seq'::regclass);

ALTER TABLE ONLY zones ALTER COLUMN id SET DEFAULT nextval('zones_id_seq'::regclass);

ALTER TABLE ONLY mtg_booking
    ADD CONSTRAINT _meeting_booking_qr_code_uc UNIQUE (qr_code);

ALTER TABLE ONLY acc_antipassback
    ADD CONSTRAINT acc_antipassback_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_door
    ADD CONSTRAINT acc_door_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_event
    ADD CONSTRAINT acc_event_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_first_card
    ADD CONSTRAINT acc_first_card_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_guard_tour_checkpoint
    ADD CONSTRAINT acc_guard_tour_checkpoint_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_guard_tour_log
    ADD CONSTRAINT acc_guard_tour_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_guard_tour
    ADD CONSTRAINT acc_guard_tour_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_guard_tour_schedule
    ADD CONSTRAINT acc_guard_tour_schedule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_guard_tour
    ADD CONSTRAINT acc_guard_tour_tour_name_key UNIQUE (tour_name);

ALTER TABLE ONLY acc_interlock_door
    ADD CONSTRAINT acc_interlock_door_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_interlock_group
    ADD CONSTRAINT acc_interlock_group_group_name_key UNIQUE (group_name);

ALTER TABLE ONLY acc_interlock_group
    ADD CONSTRAINT acc_interlock_group_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_level_door
    ADD CONSTRAINT acc_level_door_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_level
    ADD CONSTRAINT acc_level_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_linkage
    ADD CONSTRAINT acc_linkage_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_multi_card
    ADD CONSTRAINT acc_multi_card_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_multi_card_user
    ADD CONSTRAINT acc_multi_card_user_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_passback_rule
    ADD CONSTRAINT acc_passback_rule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_timezone
    ADD CONSTRAINT acc_timezone_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_timezone
    ADD CONSTRAINT acc_timezone_timezone_name_key UNIQUE (timezone_name);

ALTER TABLE ONLY acc_userauthorize
    ADD CONSTRAINT acc_userauthorize_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_visitor_access
    ADD CONSTRAINT acc_visitor_access_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_zone_door
    ADD CONSTRAINT acc_zone_door_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_zone_door
    ADD CONSTRAINT acc_zone_door_zone_id_door_id_key UNIQUE (zone_id, door_id);

ALTER TABLE ONLY acc_zone
    ADD CONSTRAINT acc_zone_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acc_zone
    ADD CONSTRAINT acc_zone_zone_name_key UNIQUE (zone_name);

ALTER TABLE ONLY access_logs
    ADD CONSTRAINT access_logs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY acgroup
    ADD CONSTRAINT acgroup_pkey PRIMARY KEY (id);

ALTER TABLE ONLY appraisal_cycles
    ADD CONSTRAINT appraisal_cycles_cycle_code_key UNIQUE (cycle_code);

ALTER TABLE ONLY appraisal_cycles
    ADD CONSTRAINT appraisal_cycles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_exception
    ADD CONSTRAINT att_exception_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_holiday
    ADD CONSTRAINT att_holiday_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_leave_old
    ADD CONSTRAINT att_leave_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_leave
    ADD CONSTRAINT att_leave_pkey1 PRIMARY KEY (id);

ALTER TABLE ONLY att_leave_type
    ADD CONSTRAINT att_leave_type_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_manual_log
    ADD CONSTRAINT att_manual_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_overtime
    ADD CONSTRAINT att_overtime_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_overtime_rule
    ADD CONSTRAINT att_overtime_rule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_report
    ADD CONSTRAINT att_report_emp_id_att_date_key UNIQUE (emp_id, att_date);

ALTER TABLE ONLY att_report
    ADD CONSTRAINT att_report_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_rules
    ADD CONSTRAINT att_rules_pkey PRIMARY KEY (rule_key);

ALTER TABLE ONLY att_schedule
    ADD CONSTRAINT att_schedule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_shift
    ADD CONSTRAINT att_shift_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_shift_timetable
    ADD CONSTRAINT att_shift_timetable_pkey PRIMARY KEY (id);

ALTER TABLE ONLY att_shift_timetable
    ADD CONSTRAINT att_shift_timetable_shift_id_day_of_week_key UNIQUE (shift_id, day_of_week);

ALTER TABLE ONLY att_timetable
    ADD CONSTRAINT att_timetable_pkey PRIMARY KEY (id);

ALTER TABLE ONLY attendance_logs
    ADD CONSTRAINT attendance_logs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY attribute_templates
    ADD CONSTRAINT attribute_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY attribute_validations
    ADD CONSTRAINT attribute_validations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_codename_key UNIQUE (codename);

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_name_key UNIQUE (name);

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);

ALTER TABLE ONLY auth_role
    ADD CONSTRAINT auth_role_name_key UNIQUE (name);

ALTER TABLE ONLY auth_role_permission
    ADD CONSTRAINT auth_role_permission_pkey PRIMARY KEY (id);

ALTER TABLE ONLY auth_role_permission
    ADD CONSTRAINT auth_role_permission_role_id_permission_id_key UNIQUE (role_id, permission_id);

ALTER TABLE ONLY auth_role
    ADD CONSTRAINT auth_role_pkey PRIMARY KEY (id);

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);

ALTER TABLE ONLY auth_user_role
    ADD CONSTRAINT auth_user_role_pkey PRIMARY KEY (id);

ALTER TABLE ONLY auth_user_role
    ADD CONSTRAINT auth_user_role_user_id_role_id_key UNIQUE (user_id, role_id);

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);

ALTER TABLE ONLY base_company
    ADD CONSTRAINT base_company_pkey PRIMARY KEY (id);

ALTER TABLE ONLY base_operationlog
    ADD CONSTRAINT base_operationlog_pkey PRIMARY KEY (id);

ALTER TABLE ONLY benefit_plans
    ADD CONSTRAINT benefit_plans_pkey PRIMARY KEY (id);

ALTER TABLE ONLY benefit_plans
    ADD CONSTRAINT benefit_plans_plan_code_key UNIQUE (plan_code);

ALTER TABLE ONLY biometric_devices
    ADD CONSTRAINT biometric_devices_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biometric_enrollment_sessions
    ADD CONSTRAINT biometric_enrollment_sessions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biometric_templates
    ADD CONSTRAINT biometric_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biometric_verification_logs
    ADD CONSTRAINT biometric_verification_logs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biotime_access_levels
    ADD CONSTRAINT biotime_access_levels_level_code_key UNIQUE (level_code);

ALTER TABLE ONLY biotime_access_levels
    ADD CONSTRAINT biotime_access_levels_level_name_key UNIQUE (level_name);

ALTER TABLE ONLY biotime_access_levels
    ADD CONSTRAINT biotime_access_levels_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biotime_access_schedules
    ADD CONSTRAINT biotime_access_schedules_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biotime_biometric_templates
    ADD CONSTRAINT biotime_biometric_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biotime_conflict_resolutions
    ADD CONSTRAINT biotime_conflict_resolutions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biotime_device_groups
    ADD CONSTRAINT biotime_device_groups_group_name_key UNIQUE (group_name);

ALTER TABLE ONLY biotime_device_groups
    ADD CONSTRAINT biotime_device_groups_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biotime_devices
    ADD CONSTRAINT biotime_devices_pkey PRIMARY KEY (id);

ALTER TABLE ONLY biotime_sync_logs
    ADD CONSTRAINT biotime_sync_logs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY certification_audits
    ADD CONSTRAINT certification_audits_pkey PRIMARY KEY (id);

ALTER TABLE ONLY certification_templates
    ADD CONSTRAINT certification_templates_name_key UNIQUE (name);

ALTER TABLE ONLY certification_templates
    ADD CONSTRAINT certification_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY certifications
    ADD CONSTRAINT certifications_pkey PRIMARY KEY (id);

ALTER TABLE ONLY checkinout
    ADD CONSTRAINT checkinout_pkey PRIMARY KEY (id);

ALTER TABLE ONLY contract_assignments
    ADD CONSTRAINT contract_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY contractor_compliance
    ADD CONSTRAINT contractor_compliance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY contractors
    ADD CONSTRAINT contractors_contractor_code_key UNIQUE (contractor_code);

ALTER TABLE ONLY contractors
    ADD CONSTRAINT contractors_pkey PRIMARY KEY (id);

ALTER TABLE ONLY custom_attribute_values
    ADD CONSTRAINT custom_attribute_values_pkey PRIMARY KEY (id);

ALTER TABLE ONLY custom_attributes
    ADD CONSTRAINT custom_attributes_pkey PRIMARY KEY (id);

ALTER TABLE ONLY department_personnel
    ADD CONSTRAINT department_personnel_pkey PRIMARY KEY (id);

ALTER TABLE ONLY departments
    ADD CONSTRAINT departments_code_key UNIQUE (code);

ALTER TABLE ONLY departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY device_blacklist
    ADD CONSTRAINT device_blacklist_pkey PRIMARY KEY (id);

ALTER TABLE ONLY device_events
    ADD CONSTRAINT device_events_pkey PRIMARY KEY (id);

ALTER TABLE ONLY device_maintenance
    ADD CONSTRAINT device_maintenance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY device_schedules
    ADD CONSTRAINT device_schedules_pkey PRIMARY KEY (id);

ALTER TABLE ONLY devicemap
    ADD CONSTRAINT devicemap_device_sn_key UNIQUE (device_sn);

ALTER TABLE ONLY devicemap
    ADD CONSTRAINT devicemap_pkey PRIMARY KEY (id);

ALTER TABLE ONLY devices
    ADD CONSTRAINT devices_device_id_key UNIQUE (device_id);

ALTER TABLE ONLY devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);

ALTER TABLE ONLY devices
    ADD CONSTRAINT devices_serial_number_key UNIQUE (serial_number);

ALTER TABLE ONLY disciplinary_cases
    ADD CONSTRAINT disciplinary_cases_case_number_key UNIQUE (case_number);

ALTER TABLE ONLY disciplinary_cases
    ADD CONSTRAINT disciplinary_cases_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_device_command
    ADD CONSTRAINT emergency_device_command_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_device_enhanced
    ADD CONSTRAINT emergency_device_enhanced_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_device_enhanced
    ADD CONSTRAINT emergency_device_enhanced_terminal_sn_key UNIQUE (terminal_sn);

ALTER TABLE ONLY emergency_device_maintenance
    ADD CONSTRAINT emergency_device_maintenance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_device
    ADD CONSTRAINT emergency_device_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_event_enhanced
    ADD CONSTRAINT emergency_event_enhanced_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_event
    ADD CONSTRAINT emergency_event_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_notification_enhanced
    ADD CONSTRAINT emergency_notification_enhanced_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_notification
    ADD CONSTRAINT emergency_notification_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_panic_log_enhanced
    ADD CONSTRAINT emergency_panic_log_enhanced_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_panic_log
    ADD CONSTRAINT emergency_panic_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_plan
    ADD CONSTRAINT emergency_plan_pkey PRIMARY KEY (id);

ALTER TABLE ONLY emergency_template
    ADD CONSTRAINT emergency_template_pkey PRIMARY KEY (id);

ALTER TABLE ONLY employee_benefits
    ADD CONSTRAINT employee_benefits_pkey PRIMARY KEY (id);

ALTER TABLE ONLY employment_contracts
    ADD CONSTRAINT employment_contracts_contract_number_key UNIQUE (contract_number);

ALTER TABLE ONLY employment_contracts
    ADD CONSTRAINT employment_contracts_pkey PRIMARY KEY (id);

ALTER TABLE ONLY events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);

ALTER TABLE ONLY face
    ADD CONSTRAINT face_pkey PRIMARY KEY (id);

ALTER TABLE ONLY face
    ADD CONSTRAINT face_user_id_key UNIQUE (user_id);

ALTER TABLE ONLY fingerprint
    ADD CONSTRAINT fingerprint_pkey PRIMARY KEY (id);

ALTER TABLE ONLY fingerprint
    ADD CONSTRAINT fingerprint_user_id_finger_index_key UNIQUE (user_id, finger_index);

ALTER TABLE ONLY flight_log
    ADD CONSTRAINT flight_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY holiday
    ADD CONSTRAINT holiday_holiday_date_holiday_name_key UNIQUE (holiday_date, holiday_name);

ALTER TABLE ONLY holiday
    ADD CONSTRAINT holiday_pkey PRIMARY KEY (id);

ALTER TABLE ONLY hr_integration_config
    ADD CONSTRAINT hr_integration_config_pkey PRIMARY KEY (id);

ALTER TABLE ONLY hr_sync_log
    ADD CONSTRAINT hr_sync_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY iclock_bio_template
    ADD CONSTRAINT iclock_bio_template_pkey PRIMARY KEY (id);

ALTER TABLE ONLY iclock_devcmd
    ADD CONSTRAINT iclock_devcmd_pkey PRIMARY KEY (id);

ALTER TABLE ONLY iclock_operlog
    ADD CONSTRAINT iclock_operlog_pkey PRIMARY KEY (id);

ALTER TABLE ONLY iclock_terminal
    ADD CONSTRAINT iclock_terminal_pkey PRIMARY KEY (id);

ALTER TABLE ONLY iclock_terminal
    ADD CONSTRAINT iclock_terminal_sn_key UNIQUE (sn);

ALTER TABLE ONLY iclock_transaction
    ADD CONSTRAINT iclock_transaction_pkey PRIMARY KEY (id);

ALTER TABLE ONLY leave_balance
    ADD CONSTRAINT leave_balance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY leave_blackout
    ADD CONSTRAINT leave_blackout_pkey PRIMARY KEY (id);

ALTER TABLE ONLY leave_management
    ADD CONSTRAINT leave_management_pkey PRIMARY KEY (id);

ALTER TABLE ONLY manifest_entry
    ADD CONSTRAINT manifest_entry_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_audit_log
    ADD CONSTRAINT mtd_audit_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_cert_type
    ADD CONSTRAINT mtd_cert_type_cert_name_key UNIQUE (cert_name);

ALTER TABLE ONLY mtd_cert_type
    ADD CONSTRAINT mtd_cert_type_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_certification
    ADD CONSTRAINT mtd_certification_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_compliance_log
    ADD CONSTRAINT mtd_compliance_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_induction_record
    ADD CONSTRAINT mtd_induction_record_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_induction_template
    ADD CONSTRAINT mtd_induction_template_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_medical_record
    ADD CONSTRAINT mtd_medical_record_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_ppe_issue
    ADD CONSTRAINT mtd_ppe_issue_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtd_ppe_type
    ADD CONSTRAINT mtd_ppe_type_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtg_action_item
    ADD CONSTRAINT mtg_action_item_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtg_attendance
    ADD CONSTRAINT mtg_attendance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtg_attendee
    ADD CONSTRAINT mtg_attendee_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtg_booking
    ADD CONSTRAINT mtg_booking_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtg_equipment
    ADD CONSTRAINT mtg_equipment_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtg_minutes
    ADD CONSTRAINT mtg_minutes_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mtg_room
    ADD CONSTRAINT mtg_room_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mustering_drill_schedule
    ADD CONSTRAINT mustering_drill_schedule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mustering_escalation_record
    ADD CONSTRAINT mustering_escalation_record_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mustering_event
    ADD CONSTRAINT mustering_event_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mustering_expected
    ADD CONSTRAINT mustering_expected_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mustering_log
    ADD CONSTRAINT mustering_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mustering_search_sweep
    ADD CONSTRAINT mustering_search_sweep_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mustering_template
    ADD CONSTRAINT mustering_template_pkey PRIMARY KEY (id);

ALTER TABLE ONLY onboarding_checklists
    ADD CONSTRAINT onboarding_checklists_pkey PRIMARY KEY (id);

ALTER TABLE ONLY onboarding_documents
    ADD CONSTRAINT onboarding_documents_pkey PRIMARY KEY (id);

ALTER TABLE ONLY onboarding_notifications
    ADD CONSTRAINT onboarding_notifications_pkey PRIMARY KEY (id);

ALTER TABLE ONLY onboarding_task
    ADD CONSTRAINT onboarding_task_pkey PRIMARY KEY (id);

ALTER TABLE ONLY onboarding_tasks
    ADD CONSTRAINT onboarding_tasks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY onboarding_templates
    ADD CONSTRAINT onboarding_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_pkey PRIMARY KEY (id);

ALTER TABLE ONLY overtime_management
    ADD CONSTRAINT overtime_management_pkey PRIMARY KEY (id);

ALTER TABLE ONLY overtime_record
    ADD CONSTRAINT overtime_record_pkey PRIMARY KEY (id);

ALTER TABLE ONLY overtime_rule
    ADD CONSTRAINT overtime_rule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY overtime_rules
    ADD CONSTRAINT overtime_rules_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_attendance_mapping
    ADD CONSTRAINT pay_attendance_mapping_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_audit_log
    ADD CONSTRAINT pay_audit_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_bank_config
    ADD CONSTRAINT pay_bank_config_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_calculation_log
    ADD CONSTRAINT pay_calculation_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_contractor_rate
    ADD CONSTRAINT pay_contractor_rate_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_item
    ADD CONSTRAINT pay_item_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_loan_deduction
    ADD CONSTRAINT pay_loan_deduction_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_loan
    ADD CONSTRAINT pay_loan_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_payslip_template
    ADD CONSTRAINT pay_payslip_template_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_period
    ADD CONSTRAINT pay_period_period_name_key UNIQUE (period_name);

ALTER TABLE ONLY pay_period
    ADD CONSTRAINT pay_period_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_salary_item
    ADD CONSTRAINT pay_salary_item_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_salary
    ADD CONSTRAINT pay_salary_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_structure_assign
    ADD CONSTRAINT pay_structure_assign_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_structure
    ADD CONSTRAINT pay_structure_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pay_zone_allowance
    ADD CONSTRAINT pay_zone_allowance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY performance_appraisals
    ADD CONSTRAINT performance_appraisals_pkey PRIMARY KEY (id);

ALTER TABLE ONLY permissions
    ADD CONSTRAINT permissions_code_key UNIQUE (code);

ALTER TABLE ONLY permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY personnel_area
    ADD CONSTRAINT personnel_area_pkey PRIMARY KEY (id);

ALTER TABLE ONLY personnel_assignments
    ADD CONSTRAINT personnel_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY personnel
    ADD CONSTRAINT personnel_badge_id_key UNIQUE (badge_id);

ALTER TABLE ONLY personnel_department
    ADD CONSTRAINT personnel_department_pkey PRIMARY KEY (id);

ALTER TABLE ONLY personnel
    ADD CONSTRAINT personnel_emp_code_key UNIQUE (emp_code);

ALTER TABLE ONLY personnel_employee
    ADD CONSTRAINT personnel_employee_emp_code_key UNIQUE (emp_code);

ALTER TABLE ONLY personnel_employee
    ADD CONSTRAINT personnel_employee_pkey PRIMARY KEY (id);

ALTER TABLE ONLY personnel
    ADD CONSTRAINT personnel_pkey PRIMARY KEY (id);

ALTER TABLE ONLY pob_status
    ADD CONSTRAINT pob_status_pkey PRIMARY KEY (id);

ALTER TABLE ONLY position_assignments
    ADD CONSTRAINT position_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY position_levels
    ADD CONSTRAINT position_levels_level_code_key UNIQUE (level_code);

ALTER TABLE ONLY position_levels
    ADD CONSTRAINT position_levels_level_number_key UNIQUE (level_number);

ALTER TABLE ONLY position_levels
    ADD CONSTRAINT position_levels_pkey PRIMARY KEY (id);

ALTER TABLE ONLY position_templates
    ADD CONSTRAINT position_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY position_templates
    ADD CONSTRAINT position_templates_template_code_key UNIQUE (template_code);

ALTER TABLE ONLY positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY positions
    ADD CONSTRAINT positions_position_code_key UNIQUE (position_code);

ALTER TABLE ONLY promotion_transfers
    ADD CONSTRAINT promotion_transfers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY resignation_documents
    ADD CONSTRAINT resignation_documents_pkey PRIMARY KEY (id);

ALTER TABLE ONLY resignation_notifications
    ADD CONSTRAINT resignation_notifications_pkey PRIMARY KEY (id);

ALTER TABLE ONLY resignation_tasks
    ADD CONSTRAINT resignation_tasks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY resignation_templates
    ADD CONSTRAINT resignation_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY role_assignments
    ADD CONSTRAINT role_assignments_personnel_id_role_id_key UNIQUE (personnel_id, role_id);

ALTER TABLE ONLY role_assignments
    ADD CONSTRAINT role_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY role_permissions
    ADD CONSTRAINT role_permissions_role_id_permission_code_key UNIQUE (role_id, permission_code);

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_code_key UNIQUE (code);

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY rpt_export_log
    ADD CONSTRAINT rpt_export_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY rpt_favorite
    ADD CONSTRAINT rpt_favorite_pkey PRIMARY KEY (id);

ALTER TABLE ONLY rpt_schedule
    ADD CONSTRAINT rpt_schedule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY rpt_template
    ADD CONSTRAINT rpt_template_pkey PRIMARY KEY (id);

ALTER TABLE ONLY rpt_user_preset
    ADD CONSTRAINT rpt_user_preset_pkey PRIMARY KEY (id);

ALTER TABLE ONLY schedule_management
    ADD CONSTRAINT schedule_management_pkey PRIMARY KEY (id);

ALTER TABLE ONLY shift_management
    ADD CONSTRAINT shift_management_pkey PRIMARY KEY (id);

ALTER TABLE ONLY shift_management
    ADD CONSTRAINT shift_management_shift_code_key UNIQUE (shift_code);

ALTER TABLE ONLY sn
    ADD CONSTRAINT sn_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sn
    ADD CONSTRAINT sn_sn_key UNIQUE (sn);

ALTER TABLE ONLY ssr
    ADD CONSTRAINT ssr_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_api_keys
    ADD CONSTRAINT sys_api_keys_api_key_key UNIQUE (api_key);

ALTER TABLE ONLY sys_api_keys
    ADD CONSTRAINT sys_api_keys_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_branding
    ADD CONSTRAINT sys_branding_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_consent_records
    ADD CONSTRAINT sys_consent_records_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_data_access_logs
    ADD CONSTRAINT sys_data_access_logs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_db_backups
    ADD CONSTRAINT sys_db_backups_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_email_templates
    ADD CONSTRAINT sys_email_templates_code_key UNIQUE (code);

ALTER TABLE ONLY sys_email_templates
    ADD CONSTRAINT sys_email_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_languages
    ADD CONSTRAINT sys_languages_code_key UNIQUE (code);

ALTER TABLE ONLY sys_languages
    ADD CONSTRAINT sys_languages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_licenses
    ADD CONSTRAINT sys_licenses_license_key_key UNIQUE (license_key);

ALTER TABLE ONLY sys_licenses
    ADD CONSTRAINT sys_licenses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_notifications
    ADD CONSTRAINT sys_notifications_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_parameters
    ADD CONSTRAINT sys_parameters_param_key_key UNIQUE (param_key);

ALTER TABLE ONLY sys_parameters
    ADD CONSTRAINT sys_parameters_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_permissions
    ADD CONSTRAINT sys_permissions_code_key UNIQUE (code);

ALTER TABLE ONLY sys_permissions
    ADD CONSTRAINT sys_permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_renewal_log
    ADD CONSTRAINT sys_renewal_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_role_permissions
    ADD CONSTRAINT sys_role_permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_role_permissions
    ADD CONSTRAINT sys_role_permissions_role_id_permission_code_key UNIQUE (role_id, permission_code);

ALTER TABLE ONLY sys_roles
    ADD CONSTRAINT sys_roles_name_key UNIQUE (name);

ALTER TABLE ONLY sys_roles
    ADD CONSTRAINT sys_roles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_sso_configs
    ADD CONSTRAINT sys_sso_configs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_subscription
    ADD CONSTRAINT sys_subscription_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_translations
    ADD CONSTRAINT sys_translations_lang_code_key_key UNIQUE (lang_code, key);

ALTER TABLE ONLY sys_translations
    ADD CONSTRAINT sys_translations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_user_roles
    ADD CONSTRAINT sys_user_roles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY sys_user_roles
    ADD CONSTRAINT sys_user_roles_user_id_role_id_key UNIQUE (user_id, role_id);

ALTER TABLE ONLY sys_webhooks
    ADD CONSTRAINT sys_webhooks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY system_company
    ADD CONSTRAINT system_company_pkey PRIMARY KEY (id);

ALTER TABLE ONLY training_courses
    ADD CONSTRAINT training_courses_course_code_key UNIQUE (course_code);

ALTER TABLE ONLY training_courses
    ADD CONSTRAINT training_courses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY training_enrollment
    ADD CONSTRAINT training_enrollment_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transport_assignments
    ADD CONSTRAINT transport_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transport_crew
    ADD CONSTRAINT transport_crew_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transport
    ADD CONSTRAINT transport_identifier_key UNIQUE (identifier);

ALTER TABLE ONLY transport_inventory
    ADD CONSTRAINT transport_inventory_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transport_maintenance
    ADD CONSTRAINT transport_maintenance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transport
    ADD CONSTRAINT transport_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transport_schedule
    ADD CONSTRAINT transport_schedule_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_extensions
    ADD CONSTRAINT user_extensions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_extensions
    ADD CONSTRAINT user_extensions_user_id_key UNIQUE (user_id);

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_sessions
    ADD CONSTRAINT user_sessions_refresh_token_key UNIQUE (refresh_token);

ALTER TABLE ONLY user_sessions
    ADD CONSTRAINT user_sessions_session_token_key UNIQUE (session_token);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_username_key UNIQUE (username);

ALTER TABLE ONLY vendor_compliance
    ADD CONSTRAINT vendor_compliance_pkey PRIMARY KEY (id);

ALTER TABLE ONLY vendor_contracts
    ADD CONSTRAINT vendor_contracts_contract_number_key UNIQUE (contract_number);

ALTER TABLE ONLY vendor_contracts
    ADD CONSTRAINT vendor_contracts_pkey PRIMARY KEY (id);

ALTER TABLE ONLY vendors
    ADD CONSTRAINT vendors_pkey PRIMARY KEY (id);

ALTER TABLE ONLY vendors
    ADD CONSTRAINT vendors_vendor_code_key UNIQUE (vendor_code);

ALTER TABLE ONLY vis_blacklist
    ADD CONSTRAINT vis_blacklist_pkey PRIMARY KEY (id);

ALTER TABLE ONLY vis_pre_registration
    ADD CONSTRAINT vis_pre_registration_pkey PRIMARY KEY (id);

ALTER TABLE ONLY vis_type
    ADD CONSTRAINT vis_type_pkey PRIMARY KEY (id);

ALTER TABLE ONLY vis_visit_log
    ADD CONSTRAINT vis_visit_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY vis_visitor
    ADD CONSTRAINT vis_visitor_pkey PRIMARY KEY (id);

ALTER TABLE ONLY zone_personnel_assignments
    ADD CONSTRAINT zone_personnel_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY zone_personnel_tracking
    ADD CONSTRAINT zone_personnel_tracking_pkey PRIMARY KEY (id);

ALTER TABLE ONLY zone_reader_assignments
    ADD CONSTRAINT zone_reader_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY zones
    ADD CONSTRAINT zones_code_key UNIQUE (code);

ALTER TABLE ONLY zones
    ADD CONSTRAINT zones_pkey PRIMARY KEY (id);

CREATE UNIQUE INDEX IF NOT EXISTS att_shift_shift_code_uq ON att_shift USING btree (shift_code) WHERE (shift_code IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_auth_role_perm_role ON auth_role_permission USING btree (role_id);

CREATE INDEX IF NOT EXISTS idx_auth_user_active ON auth_user USING btree (is_active);

CREATE INDEX IF NOT EXISTS idx_auth_user_role_role ON auth_user_role USING btree (role_id);

CREATE INDEX IF NOT EXISTS idx_auth_user_role_user ON auth_user_role USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_auth_user_username ON auth_user USING btree (username);

CREATE INDEX IF NOT EXISTS idx_checkinout_emp_code ON checkinout USING btree (emp_code);

CREATE INDEX IF NOT EXISTS idx_checkinout_time ON checkinout USING btree (check_time);

CREATE INDEX IF NOT EXISTS idx_devicemap_sn ON devicemap USING btree (device_sn);

CREATE INDEX IF NOT EXISTS idx_face_user_id ON face USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_fingerprint_user_id ON fingerprint USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_holiday_date ON holiday USING btree (holiday_date);

CREATE INDEX IF NOT EXISTS idx_iclock_txn_emp_time ON iclock_transaction USING btree (emp_code, punch_time DESC);

CREATE INDEX IF NOT EXISTS idx_iclock_txn_sn_time ON iclock_transaction USING btree (terminal_sn, punch_time DESC);

CREATE INDEX IF NOT EXISTS idx_manifest_schedule_id ON manifest_entry USING btree (schedule_id);

CREATE INDEX IF NOT EXISTS idx_manifest_status ON manifest_entry USING btree (status);

CREATE INDEX IF NOT EXISTS idx_mustering_event_status ON mustering_event USING btree (status);

CREATE INDEX IF NOT EXISTS idx_mustering_event_zone ON mustering_event USING btree (zone_id);

CREATE INDEX IF NOT EXISTS idx_mustering_log_emp ON mustering_log USING btree (emp_code);

CREATE INDEX IF NOT EXISTS idx_mustering_log_event ON mustering_log USING btree (event_id);

CREATE INDEX IF NOT EXISTS idx_operation_log_action ON base_operationlog USING btree (action);

CREATE INDEX IF NOT EXISTS idx_operation_log_created ON base_operationlog USING btree (created_at);

CREATE INDEX IF NOT EXISTS idx_operation_log_user ON base_operationlog USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_overtime_record_date ON overtime_record USING btree (overtime_date);

CREATE INDEX IF NOT EXISTS idx_overtime_record_emp_code ON overtime_record USING btree (emp_code);

CREATE INDEX IF NOT EXISTS idx_overtime_rule_type ON overtime_rule USING btree (rule_type);

CREATE INDEX IF NOT EXISTS idx_personnel_card_number ON personnel USING btree (card_number);

CREATE INDEX IF NOT EXISTS idx_personnel_dept_id ON personnel_employee USING btree (dept_id);

CREATE INDEX IF NOT EXISTS idx_personnel_emp_code ON personnel_employee USING btree (emp_code);

CREATE INDEX IF NOT EXISTS idx_personnel_status ON personnel_employee USING btree (status);

CREATE INDEX IF NOT EXISTS idx_rpt_export_log_export_time ON rpt_export_log USING btree (export_time);

CREATE INDEX IF NOT EXISTS idx_rpt_export_log_template_id ON rpt_export_log USING btree (template_id);

CREATE INDEX IF NOT EXISTS idx_rpt_export_log_user_id ON rpt_export_log USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_rpt_favorite_template_id ON rpt_favorite USING btree (template_id);

CREATE INDEX IF NOT EXISTS idx_rpt_favorite_user_id ON rpt_favorite USING btree (user_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rpt_favorite_user_template ON rpt_favorite USING btree (user_id, template_id);

CREATE INDEX IF NOT EXISTS idx_rpt_schedule_next_run ON rpt_schedule USING btree (next_run, is_active);

CREATE INDEX IF NOT EXISTS idx_rpt_schedule_next_run_active ON rpt_schedule USING btree (next_run, is_active);

CREATE INDEX IF NOT EXISTS idx_rpt_schedule_template ON rpt_schedule USING btree (template_id);

CREATE INDEX IF NOT EXISTS idx_rpt_schedule_template_id ON rpt_schedule USING btree (template_id);

CREATE INDEX IF NOT EXISTS idx_rpt_template_created_by ON rpt_template USING btree (created_by);

CREATE INDEX IF NOT EXISTS idx_rpt_template_is_public ON rpt_template USING btree (is_public);

CREATE INDEX IF NOT EXISTS idx_rpt_template_module_code ON rpt_template USING btree (module, report_code);

CREATE INDEX IF NOT EXISTS idx_rpt_user_preset_template_id ON rpt_user_preset USING btree (template_id);

CREATE INDEX IF NOT EXISTS idx_rpt_user_preset_user_id ON rpt_user_preset USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_ssr_status ON ssr USING btree (status);

CREATE INDEX IF NOT EXISTS idx_ssr_user_id ON ssr USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_terminal_ip ON iclock_terminal USING btree (ip_address);

CREATE INDEX IF NOT EXISTS idx_terminal_sn ON iclock_terminal USING btree (sn);

CREATE INDEX IF NOT EXISTS idx_terminal_state ON iclock_terminal USING btree (state);

CREATE INDEX IF NOT EXISTS idx_transaction_emp_code ON iclock_transaction USING btree (emp_code);

CREATE INDEX IF NOT EXISTS idx_transaction_punch_time ON iclock_transaction USING btree (punch_time);

CREATE INDEX IF NOT EXISTS idx_transaction_terminal_sn ON iclock_transaction USING btree (terminal_sn);

CREATE INDEX IF NOT EXISTS idx_transaction_upload_time ON iclock_transaction USING btree (upload_time);

CREATE INDEX IF NOT EXISTS idx_zpt_emp_code ON zone_personnel_tracking USING btree (emp_code);

CREATE INDEX IF NOT EXISTS idx_zpt_punch_time ON zone_personnel_tracking USING btree (punch_time);

CREATE INDEX IF NOT EXISTS idx_zpt_zone_id ON zone_personnel_tracking USING btree (zone_id);

CREATE INDEX IF NOT EXISTS ix_acc_antipassback_emp_code ON acc_antipassback USING btree (emp_code);

CREATE INDEX IF NOT EXISTS ix_acc_antipassback_id ON acc_antipassback USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_event_created_at ON acc_event USING btree (created_at);

CREATE INDEX IF NOT EXISTS ix_acc_event_emp_code ON acc_event USING btree (emp_code);

CREATE INDEX IF NOT EXISTS ix_acc_event_event_time ON acc_event USING btree (event_time);

CREATE INDEX IF NOT EXISTS ix_acc_event_id ON acc_event USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_event_terminal_sn ON acc_event USING btree (terminal_sn);

CREATE INDEX IF NOT EXISTS ix_acc_first_card_id ON acc_first_card USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_interlock_door_id ON acc_interlock_door USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_interlock_group_id ON acc_interlock_group USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_level_door_id ON acc_level_door USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_linkage_id ON acc_linkage USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_passback_rule_id ON acc_passback_rule USING btree (id);

CREATE INDEX IF NOT EXISTS ix_acc_timezone_id ON acc_timezone USING btree (id);

CREATE INDEX IF NOT EXISTS ix_access_logs_access_granted ON access_logs USING btree (access_granted);

CREATE INDEX IF NOT EXISTS ix_access_logs_device_id ON access_logs USING btree (device_id);

CREATE INDEX IF NOT EXISTS ix_access_logs_event_type ON access_logs USING btree (event_type);

CREATE INDEX IF NOT EXISTS ix_access_logs_id ON access_logs USING btree (id);

CREATE INDEX IF NOT EXISTS ix_access_logs_personnel_id ON access_logs USING btree (personnel_id);

CREATE INDEX IF NOT EXISTS ix_access_logs_timestamp ON access_logs USING btree ("timestamp");

CREATE INDEX IF NOT EXISTS ix_attendance_logs_id ON attendance_logs USING btree (id);

CREATE INDEX IF NOT EXISTS ix_attendance_logs_timestamp ON attendance_logs USING btree ("timestamp");

CREATE INDEX IF NOT EXISTS ix_attribute_templates_category ON attribute_templates USING btree (category);

CREATE INDEX IF NOT EXISTS ix_attribute_templates_id ON attribute_templates USING btree (id);

CREATE INDEX IF NOT EXISTS ix_attribute_templates_is_active ON attribute_templates USING btree (is_active);

CREATE UNIQUE INDEX IF NOT EXISTS ix_attribute_templates_template_code ON attribute_templates USING btree (template_code);

CREATE INDEX IF NOT EXISTS ix_attribute_templates_template_name ON attribute_templates USING btree (template_name);

CREATE INDEX IF NOT EXISTS ix_attribute_validations_attribute_value_id ON attribute_validations USING btree (attribute_value_id);

CREATE INDEX IF NOT EXISTS ix_attribute_validations_id ON attribute_validations USING btree (id);

CREATE INDEX IF NOT EXISTS ix_base_company_company_name ON base_company USING btree (company_name);

CREATE INDEX IF NOT EXISTS ix_base_company_id ON base_company USING btree (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_biometric_devices_device_serial ON biometric_devices USING btree (device_serial);

CREATE INDEX IF NOT EXISTS ix_biometric_devices_id ON biometric_devices USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biometric_devices_ip_address ON biometric_devices USING btree (ip_address);

CREATE INDEX IF NOT EXISTS ix_biometric_enrollment_sessions_id ON biometric_enrollment_sessions USING btree (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_biometric_enrollment_sessions_session_id ON biometric_enrollment_sessions USING btree (session_id);

CREATE INDEX IF NOT EXISTS ix_biometric_templates_id ON biometric_templates USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biometric_templates_is_active ON biometric_templates USING btree (is_active);

CREATE INDEX IF NOT EXISTS ix_biometric_templates_personnel_id ON biometric_templates USING btree (personnel_id);

CREATE INDEX IF NOT EXISTS ix_biometric_templates_template_type ON biometric_templates USING btree (template_type);

CREATE INDEX IF NOT EXISTS ix_biometric_verification_logs_id ON biometric_verification_logs USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biometric_verification_logs_personnel_id ON biometric_verification_logs USING btree (personnel_id);

CREATE INDEX IF NOT EXISTS ix_biotime_access_levels_id ON biotime_access_levels USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biotime_access_schedules_id ON biotime_access_schedules USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biotime_biometric_templates_id ON biotime_biometric_templates USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biotime_biometric_templates_personnel_id ON biotime_biometric_templates USING btree (personnel_id);

CREATE INDEX IF NOT EXISTS ix_biotime_biometric_templates_template_id ON biotime_biometric_templates USING btree (template_id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_biotime_conflict_resolutions_conflict_id ON biotime_conflict_resolutions USING btree (conflict_id);

CREATE INDEX IF NOT EXISTS ix_biotime_conflict_resolutions_id ON biotime_conflict_resolutions USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biotime_device_groups_id ON biotime_device_groups USING btree (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_biotime_devices_device_id ON biotime_devices USING btree (device_id);

CREATE INDEX IF NOT EXISTS ix_biotime_devices_id ON biotime_devices USING btree (id);

CREATE INDEX IF NOT EXISTS ix_biotime_sync_logs_id ON biotime_sync_logs USING btree (id);

CREATE INDEX IF NOT EXISTS ix_certification_audits_id ON certification_audits USING btree (id);

CREATE INDEX IF NOT EXISTS ix_certification_templates_id ON certification_templates USING btree (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_certifications_certificate_number ON certifications USING btree (certificate_number);

CREATE INDEX IF NOT EXISTS ix_certifications_expire_date ON certifications USING btree (expire_date);

CREATE INDEX IF NOT EXISTS ix_certifications_id ON certifications USING btree (id);

CREATE INDEX IF NOT EXISTS ix_certifications_issuer ON certifications USING btree (issuer);

CREATE INDEX IF NOT EXISTS ix_certifications_name ON certifications USING btree (name);

CREATE INDEX IF NOT EXISTS ix_certifications_personnel_id ON certifications USING btree (personnel_id);

CREATE INDEX IF NOT EXISTS ix_custom_attribute_values_attribute_id ON custom_attribute_values USING btree (attribute_id);

CREATE INDEX IF NOT EXISTS ix_custom_attribute_values_id ON custom_attribute_values USING btree (id);

CREATE INDEX IF NOT EXISTS ix_custom_attribute_values_personnel_id ON custom_attribute_values USING btree (personnel_id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_custom_attributes_attribute_code ON custom_attributes USING btree (attribute_code);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_attribute_name ON custom_attributes USING btree (attribute_name);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_category ON custom_attributes USING btree (category);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_group_name ON custom_attributes USING btree (group_name);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_id ON custom_attributes USING btree (id);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_is_active ON custom_attributes USING btree (is_active);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_is_required ON custom_attributes USING btree (is_required);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_is_searchable ON custom_attributes USING btree (is_searchable);

CREATE INDEX IF NOT EXISTS ix_custom_attributes_is_visible_in_list ON custom_attributes USING btree (is_visible_in_list);

CREATE INDEX IF NOT EXISTS ix_department_personnel_id ON department_personnel USING btree (id);

CREATE INDEX IF NOT EXISTS ix_device_blacklist_emp_code ON device_blacklist USING btree (emp_code);

CREATE INDEX IF NOT EXISTS ix_device_blacklist_id ON device_blacklist USING btree (id);

CREATE INDEX IF NOT EXISTS ix_device_events_device_id ON device_events USING btree (device_id);

CREATE INDEX IF NOT EXISTS ix_device_events_event_type ON device_events USING btree (event_type);

CREATE INDEX IF NOT EXISTS ix_device_events_id ON device_events USING btree (id);

CREATE INDEX IF NOT EXISTS ix_device_events_timestamp ON device_events USING btree ("timestamp");

CREATE INDEX IF NOT EXISTS ix_device_maintenance_device_id ON device_maintenance USING btree (device_id);

CREATE INDEX IF NOT EXISTS ix_device_maintenance_id ON device_maintenance USING btree (id);

CREATE INDEX IF NOT EXISTS ix_device_schedules_device_id ON device_schedules USING btree (device_id);

CREATE INDEX IF NOT EXISTS ix_device_schedules_id ON device_schedules USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_device_command_created_at ON emergency_device_command USING btree (created_at);

CREATE INDEX IF NOT EXISTS ix_emergency_device_command_id ON emergency_device_command USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_device_enhanced_id ON emergency_device_enhanced USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_device_enhanced_status ON emergency_device_enhanced USING btree (status);

CREATE INDEX IF NOT EXISTS ix_emergency_device_maintenance_id ON emergency_device_maintenance USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_event_enhanced_event_type ON emergency_event_enhanced USING btree (event_type);

CREATE INDEX IF NOT EXISTS ix_emergency_event_enhanced_id ON emergency_event_enhanced USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_event_enhanced_start_time ON emergency_event_enhanced USING btree (start_time);

CREATE INDEX IF NOT EXISTS ix_emergency_event_enhanced_status ON emergency_event_enhanced USING btree (status);

CREATE INDEX IF NOT EXISTS ix_emergency_event_event_type ON emergency_event USING btree (event_type);

CREATE INDEX IF NOT EXISTS ix_emergency_event_id ON emergency_event USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_event_status ON emergency_event USING btree (status);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_emergency_event_id ON emergency_notification USING btree (emergency_event_id);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_enhanced_channel ON emergency_notification_enhanced USING btree (channel);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_enhanced_created_at ON emergency_notification_enhanced USING btree (created_at);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_enhanced_emergency_event_id ON emergency_notification_enhanced USING btree (emergency_event_id);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_enhanced_id ON emergency_notification_enhanced USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_enhanced_status ON emergency_notification_enhanced USING btree (status);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_id ON emergency_notification USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_notification_status ON emergency_notification USING btree (status);

CREATE INDEX IF NOT EXISTS ix_emergency_panic_log_enhanced_id ON emergency_panic_log_enhanced USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_panic_log_enhanced_panic_time ON emergency_panic_log_enhanced USING btree (panic_time);

CREATE INDEX IF NOT EXISTS ix_emergency_panic_log_id ON emergency_panic_log USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_plan_id ON emergency_plan USING btree (id);

CREATE INDEX IF NOT EXISTS ix_emergency_template_id ON emergency_template USING btree (id);

CREATE INDEX IF NOT EXISTS ix_events_id ON events USING btree (id);

CREATE INDEX IF NOT EXISTS ix_flight_log_id ON flight_log USING btree (id);

CREATE INDEX IF NOT EXISTS ix_iclock_bio_template_emp ON iclock_bio_template USING btree (emp_code);

CREATE INDEX IF NOT EXISTS ix_iclock_devcmd_id ON iclock_devcmd USING btree (id);

CREATE INDEX IF NOT EXISTS ix_iclock_devcmd_sn ON iclock_devcmd USING btree (sn);

CREATE INDEX IF NOT EXISTS ix_iclock_devcmd_status ON iclock_devcmd USING btree (status);

CREATE INDEX IF NOT EXISTS ix_iclock_operlog_event_time ON iclock_operlog USING btree (event_time);

CREATE INDEX IF NOT EXISTS ix_iclock_operlog_oper_event ON iclock_operlog USING btree (oper_event);

CREATE INDEX IF NOT EXISTS ix_iclock_operlog_terminal_sn ON iclock_operlog USING btree (terminal_sn);

CREATE INDEX IF NOT EXISTS ix_mtg_action_item_assignee_emp_id ON mtg_action_item USING btree (assignee_emp_id);

CREATE INDEX IF NOT EXISTS ix_mtg_action_item_booking_id ON mtg_action_item USING btree (booking_id);

CREATE INDEX IF NOT EXISTS ix_mtg_action_item_created_time ON mtg_action_item USING btree (created_time);

CREATE INDEX IF NOT EXISTS ix_mtg_action_item_id ON mtg_action_item USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mtg_action_item_status ON mtg_action_item USING btree (status);

CREATE INDEX IF NOT EXISTS ix_mtg_attendance_attendee_id ON mtg_attendance USING btree (attendee_id);

CREATE INDEX IF NOT EXISTS ix_mtg_attendance_booking_id ON mtg_attendance USING btree (booking_id);

CREATE INDEX IF NOT EXISTS ix_mtg_attendance_check_in_time ON mtg_attendance USING btree (check_in_time);

CREATE INDEX IF NOT EXISTS ix_mtg_attendance_id ON mtg_attendance USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mtg_attendee_booking_id ON mtg_attendee USING btree (booking_id);

CREATE INDEX IF NOT EXISTS ix_mtg_attendee_id ON mtg_attendee USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_created_time ON mtg_booking USING btree (created_time);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_end_time ON mtg_booking USING btree (end_time);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_id ON mtg_booking USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_meeting_code ON mtg_booking USING btree (meeting_code);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_organizer_emp_id ON mtg_booking USING btree (organizer_emp_id);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_room_id ON mtg_booking USING btree (room_id);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_start_time ON mtg_booking USING btree (start_time);

CREATE INDEX IF NOT EXISTS ix_mtg_booking_status ON mtg_booking USING btree (status);

CREATE INDEX IF NOT EXISTS ix_mtg_equipment_equip_name ON mtg_equipment USING btree (equip_name);

CREATE INDEX IF NOT EXISTS ix_mtg_equipment_id ON mtg_equipment USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mtg_equipment_room_id ON mtg_equipment USING btree (room_id);

CREATE INDEX IF NOT EXISTS ix_mtg_minutes_booking_id ON mtg_minutes USING btree (booking_id);

CREATE INDEX IF NOT EXISTS ix_mtg_minutes_id ON mtg_minutes USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mtg_minutes_uploaded_time ON mtg_minutes USING btree (uploaded_time);

CREATE INDEX IF NOT EXISTS ix_mtg_room_id ON mtg_room USING btree (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_mtg_room_room_name ON mtg_room USING btree (room_name);

CREATE INDEX IF NOT EXISTS ix_mustering_escalation_record_emp_code ON mustering_escalation_record USING btree (emp_code);

CREATE INDEX IF NOT EXISTS ix_mustering_escalation_record_event_id ON mustering_escalation_record USING btree (event_id);

CREATE INDEX IF NOT EXISTS ix_mustering_escalation_record_id ON mustering_escalation_record USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mustering_expected_emp_code ON mustering_expected USING btree (emp_code);

CREATE INDEX IF NOT EXISTS ix_mustering_expected_event_id ON mustering_expected USING btree (event_id);

CREATE INDEX IF NOT EXISTS ix_mustering_expected_id ON mustering_expected USING btree (id);

CREATE INDEX IF NOT EXISTS ix_mustering_search_sweep_emp_code ON mustering_search_sweep USING btree (emp_code);

CREATE INDEX IF NOT EXISTS ix_mustering_search_sweep_event_id ON mustering_search_sweep USING btree (event_id);

CREATE INDEX IF NOT EXISTS ix_mustering_search_sweep_id ON mustering_search_sweep USING btree (id);

CREATE INDEX IF NOT EXISTS ix_onboarding_checklists_checklist_name ON onboarding_checklists USING btree (checklist_name);

CREATE INDEX IF NOT EXISTS ix_onboarding_checklists_checklist_type ON onboarding_checklists USING btree (checklist_type);

CREATE INDEX IF NOT EXISTS ix_onboarding_checklists_id ON onboarding_checklists USING btree (id);

CREATE INDEX IF NOT EXISTS ix_onboarding_checklists_is_completed ON onboarding_checklists USING btree (is_completed);

CREATE INDEX IF NOT EXISTS ix_onboarding_checklists_is_required ON onboarding_checklists USING btree (is_required);

CREATE INDEX IF NOT EXISTS ix_onboarding_checklists_onboarding_id ON onboarding_checklists USING btree (onboarding_id);

CREATE INDEX IF NOT EXISTS ix_onboarding_documents_document_type ON onboarding_documents USING btree (document_type);

CREATE INDEX IF NOT EXISTS ix_onboarding_documents_id ON onboarding_documents USING btree (id);

CREATE INDEX IF NOT EXISTS ix_onboarding_documents_is_required ON onboarding_documents USING btree (is_required);

CREATE INDEX IF NOT EXISTS ix_onboarding_documents_onboarding_id ON onboarding_documents USING btree (onboarding_id);

CREATE INDEX IF NOT EXISTS ix_onboarding_notifications_id ON onboarding_notifications USING btree (id);

CREATE INDEX IF NOT EXISTS ix_onboarding_notifications_is_read ON onboarding_notifications USING btree (is_read);

CREATE INDEX IF NOT EXISTS ix_onboarding_notifications_notification_type ON onboarding_notifications USING btree (notification_type);

CREATE INDEX IF NOT EXISTS ix_onboarding_notifications_onboarding_id ON onboarding_notifications USING btree (onboarding_id);

CREATE INDEX IF NOT EXISTS ix_onboarding_notifications_recipient_id ON onboarding_notifications USING btree (recipient_id);

CREATE INDEX IF NOT EXISTS ix_onboarding_tasks_id ON onboarding_tasks USING btree (id);

CREATE INDEX IF NOT EXISTS ix_onboarding_tasks_is_required ON onboarding_tasks USING btree (is_required);

CREATE INDEX IF NOT EXISTS ix_onboarding_tasks_onboarding_id ON onboarding_tasks USING btree (onboarding_id);

CREATE INDEX IF NOT EXISTS ix_onboarding_tasks_status ON onboarding_tasks USING btree (status);

CREATE INDEX IF NOT EXISTS ix_onboarding_tasks_task_name ON onboarding_tasks USING btree (task_name);

CREATE INDEX IF NOT EXISTS ix_onboarding_templates_id ON onboarding_templates USING btree (id);

CREATE INDEX IF NOT EXISTS ix_onboarding_templates_is_active ON onboarding_templates USING btree (is_active);

CREATE UNIQUE INDEX IF NOT EXISTS ix_onboarding_templates_template_code ON onboarding_templates USING btree (template_code);

CREATE INDEX IF NOT EXISTS ix_onboarding_templates_template_name ON onboarding_templates USING btree (template_name);

CREATE INDEX IF NOT EXISTS ix_onboardings_id ON onboardings USING btree (id);

CREATE INDEX IF NOT EXISTS ix_onboardings_personnel_id ON onboardings USING btree (personnel_id);

CREATE INDEX IF NOT EXISTS ix_onboardings_status ON onboardings USING btree (status);

CREATE INDEX IF NOT EXISTS ix_pay_attendance_mapping_id ON pay_attendance_mapping USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_audit_log_id ON pay_audit_log USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_bank_config_id ON pay_bank_config USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_calculation_log_id ON pay_calculation_log USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_contractor_rate_id ON pay_contractor_rate USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_item_id ON pay_item USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_loan_deduction_id ON pay_loan_deduction USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_loan_id ON pay_loan USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_loan_status ON pay_loan USING btree (status);

CREATE INDEX IF NOT EXISTS ix_pay_payslip_template_id ON pay_payslip_template USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_period_id ON pay_period USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_period_status ON pay_period USING btree (status);

CREATE INDEX IF NOT EXISTS ix_pay_salary_id ON pay_salary USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_salary_item_id ON pay_salary_item USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_structure_assign_id ON pay_structure_assign USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_structure_id ON pay_structure USING btree (id);

CREATE INDEX IF NOT EXISTS ix_pay_structure_is_active ON pay_structure USING btree (is_active);

CREATE INDEX IF NOT EXISTS ix_pay_structure_structure_name ON pay_structure USING btree (structure_name);

CREATE INDEX IF NOT EXISTS ix_pay_zone_allowance_id ON pay_zone_allowance USING btree (id);

CREATE INDEX IF NOT EXISTS ix_personnel_assignments_id ON personnel_assignments USING btree (id);

CREATE INDEX IF NOT EXISTS ix_resignation_documents_document_type ON resignation_documents USING btree (document_type);

CREATE INDEX IF NOT EXISTS ix_resignation_documents_id ON resignation_documents USING btree (id);

CREATE INDEX IF NOT EXISTS ix_resignation_documents_resignation_id ON resignation_documents USING btree (resignation_id);

CREATE INDEX IF NOT EXISTS ix_resignation_notifications_id ON resignation_notifications USING btree (id);

CREATE INDEX IF NOT EXISTS ix_resignation_notifications_is_read ON resignation_notifications USING btree (is_read);

CREATE INDEX IF NOT EXISTS ix_resignation_notifications_recipient_id ON resignation_notifications USING btree (recipient_id);

CREATE INDEX IF NOT EXISTS ix_resignation_notifications_resignation_id ON resignation_notifications USING btree (resignation_id);

CREATE INDEX IF NOT EXISTS ix_resignation_tasks_id ON resignation_tasks USING btree (id);

CREATE INDEX IF NOT EXISTS ix_resignation_tasks_is_completed ON resignation_tasks USING btree (is_completed);

CREATE INDEX IF NOT EXISTS ix_resignation_tasks_is_required ON resignation_tasks USING btree (is_required);

CREATE INDEX IF NOT EXISTS ix_resignation_tasks_resignation_id ON resignation_tasks USING btree (resignation_id);

CREATE INDEX IF NOT EXISTS ix_resignation_tasks_task_name ON resignation_tasks USING btree (task_name);

CREATE INDEX IF NOT EXISTS ix_resignation_templates_id ON resignation_templates USING btree (id);

CREATE INDEX IF NOT EXISTS ix_resignation_templates_is_active ON resignation_templates USING btree (is_active);

CREATE UNIQUE INDEX IF NOT EXISTS ix_resignation_templates_template_code ON resignation_templates USING btree (template_code);

CREATE INDEX IF NOT EXISTS ix_resignation_templates_template_name ON resignation_templates USING btree (template_name);

CREATE INDEX IF NOT EXISTS ix_resignations_id ON resignations USING btree (id);

CREATE INDEX IF NOT EXISTS ix_resignations_personnel_id ON resignations USING btree (personnel_id);

CREATE INDEX IF NOT EXISTS ix_resignations_status ON resignations USING btree (status);

CREATE INDEX IF NOT EXISTS ix_rpt_export_log_id ON rpt_export_log USING btree (id);

CREATE INDEX IF NOT EXISTS ix_rpt_favorite_id ON rpt_favorite USING btree (id);

CREATE INDEX IF NOT EXISTS ix_rpt_schedule_id ON rpt_schedule USING btree (id);

CREATE INDEX IF NOT EXISTS ix_rpt_template_id ON rpt_template USING btree (id);

CREATE INDEX IF NOT EXISTS ix_rpt_user_preset_id ON rpt_user_preset USING btree (id);

CREATE INDEX IF NOT EXISTS ix_transport_assignments_id ON transport_assignments USING btree (id);

CREATE INDEX IF NOT EXISTS ix_transport_crew_id ON transport_crew USING btree (id);

CREATE INDEX IF NOT EXISTS ix_transport_id ON transport USING btree (id);

CREATE INDEX IF NOT EXISTS ix_transport_inventory_id ON transport_inventory USING btree (id);

CREATE INDEX IF NOT EXISTS ix_transport_maintenance_id ON transport_maintenance USING btree (id);

CREATE INDEX IF NOT EXISTS ix_transport_schedule_id ON transport_schedule USING btree (id);

CREATE INDEX IF NOT EXISTS ix_transport_status ON transport USING btree (status);

CREATE INDEX IF NOT EXISTS ix_user_roles_id ON user_roles USING btree (id);

CREATE INDEX IF NOT EXISTS ix_user_sessions_id ON user_sessions USING btree (id);

CREATE INDEX IF NOT EXISTS ix_vis_blacklist_email ON vis_blacklist USING btree (email);

CREATE INDEX IF NOT EXISTS ix_vis_blacklist_id ON vis_blacklist USING btree (id);

CREATE INDEX IF NOT EXISTS ix_vis_blacklist_id_no ON vis_blacklist USING btree (id_no);

CREATE INDEX IF NOT EXISTS ix_vis_blacklist_phone ON vis_blacklist USING btree (phone);

CREATE INDEX IF NOT EXISTS ix_vis_pre_registration_host_emp_id ON vis_pre_registration USING btree (host_emp_id);

CREATE INDEX IF NOT EXISTS ix_vis_pre_registration_id ON vis_pre_registration USING btree (id);

CREATE INDEX IF NOT EXISTS ix_vis_pre_registration_qr_code ON vis_pre_registration USING btree (qr_code);

CREATE INDEX IF NOT EXISTS ix_vis_pre_registration_status ON vis_pre_registration USING btree (status);

CREATE INDEX IF NOT EXISTS ix_vis_pre_registration_visit_date ON vis_pre_registration USING btree (visit_date);

CREATE INDEX IF NOT EXISTS ix_vis_type_id ON vis_type USING btree (id);

CREATE INDEX IF NOT EXISTS ix_vis_type_type_name ON vis_type USING btree (type_name);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_card_no ON vis_visit_log USING btree (card_no);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_check_in_time ON vis_visit_log USING btree (check_in_time);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_check_out_time ON vis_visit_log USING btree (check_out_time);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_host_emp_id ON vis_visit_log USING btree (host_emp_id);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_id ON vis_visit_log USING btree (id);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_pre_reg_id ON vis_visit_log USING btree (pre_reg_id);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_status ON vis_visit_log USING btree (status);

CREATE INDEX IF NOT EXISTS ix_vis_visit_log_visitor_id ON vis_visit_log USING btree (visitor_id);

CREATE INDEX IF NOT EXISTS ix_vis_visitor_email ON vis_visitor USING btree (email);

CREATE INDEX IF NOT EXISTS ix_vis_visitor_id ON vis_visitor USING btree (id);

CREATE INDEX IF NOT EXISTS ix_vis_visitor_id_no ON vis_visitor USING btree (id_no);

CREATE INDEX IF NOT EXISTS ix_vis_visitor_is_blacklist ON vis_visitor USING btree (is_blacklist);

CREATE INDEX IF NOT EXISTS ix_vis_visitor_phone ON vis_visitor USING btree (phone);

CREATE INDEX IF NOT EXISTS ix_vis_visitor_visitor_code ON vis_visitor USING btree (visitor_code);

CREATE UNIQUE INDEX IF NOT EXISTS sys_notifications_dedup_idx ON sys_notifications USING btree (dedup_key);

CREATE INDEX IF NOT EXISTS sys_notifications_user_idx ON sys_notifications USING btree (user_id, is_read, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_bio_template_emp_finger ON iclock_bio_template USING btree (emp_code, finger_id);

ALTER TABLE ONLY acc_antipassback
    ADD CONSTRAINT acc_antipassback_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_door
    ADD CONSTRAINT acc_door_acc_level_id_fkey FOREIGN KEY (acc_level_id) REFERENCES acc_level(id);

ALTER TABLE ONLY acc_door
    ADD CONSTRAINT acc_door_terminal_sn_fkey FOREIGN KEY (terminal_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY acc_event
    ADD CONSTRAINT acc_event_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_first_card
    ADD CONSTRAINT acc_first_card_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_first_card
    ADD CONSTRAINT acc_first_card_timezone_id_fkey FOREIGN KEY (timezone_id) REFERENCES acc_timezone(id);

ALTER TABLE ONLY acc_guard_tour_checkpoint
    ADD CONSTRAINT acc_guard_tour_checkpoint_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_guard_tour_checkpoint
    ADD CONSTRAINT acc_guard_tour_checkpoint_tour_id_fkey FOREIGN KEY (tour_id) REFERENCES acc_guard_tour(id) ON DELETE CASCADE;

ALTER TABLE ONLY acc_guard_tour_log
    ADD CONSTRAINT acc_guard_tour_log_checkpoint_id_fkey FOREIGN KEY (checkpoint_id) REFERENCES acc_guard_tour_checkpoint(id);

ALTER TABLE ONLY acc_guard_tour_log
    ADD CONSTRAINT acc_guard_tour_log_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES acc_guard_tour_schedule(id) ON DELETE CASCADE;

ALTER TABLE ONLY acc_guard_tour_schedule
    ADD CONSTRAINT acc_guard_tour_schedule_tour_id_fkey FOREIGN KEY (tour_id) REFERENCES acc_guard_tour(id) ON DELETE CASCADE;

ALTER TABLE ONLY acc_interlock_door
    ADD CONSTRAINT acc_interlock_door_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_interlock_door
    ADD CONSTRAINT acc_interlock_door_group_id_fkey FOREIGN KEY (group_id) REFERENCES acc_interlock_group(id);

ALTER TABLE ONLY acc_level_door
    ADD CONSTRAINT acc_level_door_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_level_door
    ADD CONSTRAINT acc_level_door_level_id_fkey FOREIGN KEY (level_id) REFERENCES acc_level(id);

ALTER TABLE ONLY acc_level_door
    ADD CONSTRAINT acc_level_door_timezone_id_fkey FOREIGN KEY (timezone_id) REFERENCES acc_timezone(id);

ALTER TABLE ONLY acc_linkage
    ADD CONSTRAINT acc_linkage_output_door_id_fkey FOREIGN KEY (output_door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_multi_card
    ADD CONSTRAINT acc_multi_card_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id) ON DELETE CASCADE;

ALTER TABLE ONLY acc_multi_card_user
    ADD CONSTRAINT acc_multi_card_user_multi_card_id_fkey FOREIGN KEY (multi_card_id) REFERENCES acc_multi_card(id) ON DELETE CASCADE;

ALTER TABLE ONLY acc_passback_rule
    ADD CONSTRAINT acc_passback_rule_in_door_id_fkey FOREIGN KEY (in_door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_passback_rule
    ADD CONSTRAINT acc_passback_rule_out_door_id_fkey FOREIGN KEY (out_door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_userauthorize
    ADD CONSTRAINT acc_userauthorize_acc_level_id_fkey FOREIGN KEY (acc_level_id) REFERENCES acc_level(id);

ALTER TABLE ONLY acc_visitor_access
    ADD CONSTRAINT acc_visitor_access_acc_level_id_fkey FOREIGN KEY (acc_level_id) REFERENCES acc_level(id);

ALTER TABLE ONLY acc_visitor_access
    ADD CONSTRAINT acc_visitor_access_level_id_fkey FOREIGN KEY (level_id) REFERENCES acc_level(id) ON DELETE SET NULL;

ALTER TABLE ONLY acc_zone_door
    ADD CONSTRAINT acc_zone_door_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY acc_zone_door
    ADD CONSTRAINT acc_zone_door_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES acc_zone(id) ON DELETE CASCADE;

ALTER TABLE ONLY access_logs
    ADD CONSTRAINT access_logs_device_id_fkey FOREIGN KEY (device_id) REFERENCES devices(device_id);

ALTER TABLE ONLY access_logs
    ADD CONSTRAINT access_logs_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY access_logs
    ADD CONSTRAINT access_logs_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id);

ALTER TABLE ONLY acgroup
    ADD CONSTRAINT acgroup_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES acgroup(id);

ALTER TABLE ONLY att_exception
    ADD CONSTRAINT att_exception_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY att_leave
    ADD CONSTRAINT att_leave_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY att_leave
    ADD CONSTRAINT att_leave_leave_type_id_fkey FOREIGN KEY (leave_type_id) REFERENCES att_leave_type(id);

ALTER TABLE ONLY att_manual_log
    ADD CONSTRAINT att_manual_log_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY att_overtime
    ADD CONSTRAINT att_overtime_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY att_report
    ADD CONSTRAINT att_report_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY att_report
    ADD CONSTRAINT att_report_shift_id_fkey FOREIGN KEY (shift_id) REFERENCES att_shift(id);

ALTER TABLE ONLY att_report
    ADD CONSTRAINT att_report_timetable_id_fkey FOREIGN KEY (timetable_id) REFERENCES att_timetable(id);

ALTER TABLE ONLY att_schedule
    ADD CONSTRAINT att_schedule_shift_id_fkey FOREIGN KEY (shift_id) REFERENCES att_shift(id);

ALTER TABLE ONLY att_shift
    ADD CONSTRAINT att_shift_timetable_id_fkey FOREIGN KEY (timetable_id) REFERENCES att_timetable(id);

ALTER TABLE ONLY att_shift_timetable
    ADD CONSTRAINT att_shift_timetable_shift_id_fkey FOREIGN KEY (shift_id) REFERENCES att_shift(id) ON DELETE CASCADE;

ALTER TABLE ONLY att_shift_timetable
    ADD CONSTRAINT att_shift_timetable_timetable_id_fkey FOREIGN KEY (timetable_id) REFERENCES att_timetable(id);

ALTER TABLE ONLY attendance_logs
    ADD CONSTRAINT attendance_logs_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY attribute_templates
    ADD CONSTRAINT attribute_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY attribute_validations
    ADD CONSTRAINT attribute_validations_attribute_value_id_fkey FOREIGN KEY (attribute_value_id) REFERENCES custom_attribute_values(id);

ALTER TABLE ONLY auth_role_permission
    ADD CONSTRAINT auth_role_permission_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth_permission(id) ON DELETE CASCADE;

ALTER TABLE ONLY auth_role_permission
    ADD CONSTRAINT auth_role_permission_role_id_fkey FOREIGN KEY (role_id) REFERENCES auth_role(id) ON DELETE CASCADE;

ALTER TABLE ONLY auth_user_role
    ADD CONSTRAINT auth_user_role_role_id_fkey FOREIGN KEY (role_id) REFERENCES auth_role(id) ON DELETE CASCADE;

ALTER TABLE ONLY auth_user_role
    ADD CONSTRAINT auth_user_role_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;

ALTER TABLE ONLY base_company
    ADD CONSTRAINT base_company_parent_company_id_fkey FOREIGN KEY (parent_company_id) REFERENCES base_company(id);

ALTER TABLE ONLY base_operationlog
    ADD CONSTRAINT base_operationlog_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id);

ALTER TABLE ONLY biometric_enrollment_sessions
    ADD CONSTRAINT biometric_enrollment_sessions_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY biometric_templates
    ADD CONSTRAINT biometric_templates_enrolled_by_fkey FOREIGN KEY (enrolled_by) REFERENCES users(id);

ALTER TABLE ONLY biometric_templates
    ADD CONSTRAINT biometric_templates_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY biometric_verification_logs
    ADD CONSTRAINT biometric_verification_logs_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY biometric_verification_logs
    ADD CONSTRAINT biometric_verification_logs_template_used_fkey FOREIGN KEY (template_used) REFERENCES biometric_templates(id);

ALTER TABLE ONLY biotime_biometric_templates
    ADD CONSTRAINT biotime_biometric_templates_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY biotime_conflict_resolutions
    ADD CONSTRAINT biotime_conflict_resolutions_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES users(id);

ALTER TABLE ONLY biotime_device_groups
    ADD CONSTRAINT biotime_device_groups_parent_group_id_fkey FOREIGN KEY (parent_group_id) REFERENCES biotime_device_groups(id);

ALTER TABLE ONLY biotime_devices
    ADD CONSTRAINT biotime_devices_device_group_id_fkey FOREIGN KEY (device_group_id) REFERENCES biotime_device_groups(id);

ALTER TABLE ONLY certification_audits
    ADD CONSTRAINT certification_audits_certification_id_fkey FOREIGN KEY (certification_id) REFERENCES certifications(id);

ALTER TABLE ONLY certification_audits
    ADD CONSTRAINT certification_audits_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(id);

ALTER TABLE ONLY certification_audits
    ADD CONSTRAINT certification_audits_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY certifications
    ADD CONSTRAINT certifications_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY checkinout
    ADD CONSTRAINT checkinout_terminal_sn_fkey FOREIGN KEY (terminal_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY checkinout
    ADD CONSTRAINT checkinout_user_id_fkey FOREIGN KEY (user_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY custom_attribute_values
    ADD CONSTRAINT custom_attribute_values_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES custom_attributes(id);

ALTER TABLE ONLY custom_attribute_values
    ADD CONSTRAINT custom_attribute_values_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY custom_attribute_values
    ADD CONSTRAINT custom_attribute_values_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY custom_attribute_values
    ADD CONSTRAINT custom_attribute_values_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES users(id);

ALTER TABLE ONLY custom_attributes
    ADD CONSTRAINT custom_attributes_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY custom_attributes
    ADD CONSTRAINT custom_attributes_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES users(id);

ALTER TABLE ONLY department_personnel
    ADD CONSTRAINT department_personnel_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(id);

ALTER TABLE ONLY department_personnel
    ADD CONSTRAINT department_personnel_department_id_fkey FOREIGN KEY (department_id) REFERENCES departments(id);

ALTER TABLE ONLY department_personnel
    ADD CONSTRAINT department_personnel_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY departments
    ADD CONSTRAINT departments_default_shift_id_fkey FOREIGN KEY (default_shift_id) REFERENCES att_shift(id) ON DELETE SET NULL;

ALTER TABLE ONLY departments
    ADD CONSTRAINT departments_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES departments(id);

ALTER TABLE ONLY device_blacklist
    ADD CONSTRAINT device_blacklist_blocked_by_fkey FOREIGN KEY (blocked_by) REFERENCES users(id);

ALTER TABLE ONLY device_events
    ADD CONSTRAINT device_events_acknowledged_by_fkey FOREIGN KEY (acknowledged_by) REFERENCES users(id);

ALTER TABLE ONLY device_events
    ADD CONSTRAINT device_events_device_id_fkey FOREIGN KEY (device_id) REFERENCES devices(device_id);

ALTER TABLE ONLY device_maintenance
    ADD CONSTRAINT device_maintenance_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES users(id);

ALTER TABLE ONLY device_maintenance
    ADD CONSTRAINT device_maintenance_terminal_fkey FOREIGN KEY (device_id) REFERENCES iclock_terminal(sn) ON DELETE SET NULL;

ALTER TABLE ONLY device_schedules
    ADD CONSTRAINT device_schedules_terminal_fkey FOREIGN KEY (device_id) REFERENCES iclock_terminal(sn) ON DELETE SET NULL;

ALTER TABLE ONLY devicemap
    ADD CONSTRAINT devicemap_area_id_fkey FOREIGN KEY (area_id) REFERENCES personnel_area(id);

ALTER TABLE ONLY devices
    ADD CONSTRAINT devices_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id);

ALTER TABLE ONLY emergency_device_command
    ADD CONSTRAINT emergency_device_command_device_id_fkey FOREIGN KEY (device_id) REFERENCES emergency_device_enhanced(id);

ALTER TABLE ONLY emergency_device_command
    ADD CONSTRAINT emergency_device_command_emergency_event_id_fkey FOREIGN KEY (emergency_event_id) REFERENCES emergency_event_enhanced(id);

ALTER TABLE ONLY emergency_device_command
    ADD CONSTRAINT emergency_device_command_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES auth_user(id);

ALTER TABLE ONLY emergency_device_command
    ADD CONSTRAINT emergency_device_command_parent_command_fkey FOREIGN KEY (parent_command) REFERENCES emergency_device_command(id);

ALTER TABLE ONLY emergency_device_enhanced
    ADD CONSTRAINT emergency_device_enhanced_terminal_sn_fkey FOREIGN KEY (terminal_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY emergency_device_maintenance
    ADD CONSTRAINT emergency_device_maintenance_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES auth_user(id);

ALTER TABLE ONLY emergency_device_maintenance
    ADD CONSTRAINT emergency_device_maintenance_device_id_fkey FOREIGN KEY (device_id) REFERENCES emergency_device_enhanced(id);

ALTER TABLE ONLY emergency_device_maintenance
    ADD CONSTRAINT emergency_device_maintenance_supervisor_id_fkey FOREIGN KEY (supervisor_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY emergency_device_maintenance
    ADD CONSTRAINT emergency_device_maintenance_technician_id_fkey FOREIGN KEY (technician_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY emergency_device
    ADD CONSTRAINT emergency_device_terminal_sn_fkey FOREIGN KEY (terminal_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY emergency_device
    ADD CONSTRAINT emergency_device_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY emergency_event_enhanced
    ADD CONSTRAINT emergency_event_enhanced_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES auth_user(id);

ALTER TABLE ONLY emergency_event_enhanced
    ADD CONSTRAINT emergency_event_enhanced_mustering_event_id_fkey FOREIGN KEY (mustering_event_id) REFERENCES mustering_event(id);

ALTER TABLE ONLY emergency_event
    ADD CONSTRAINT emergency_event_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES auth_user(id);

ALTER TABLE ONLY emergency_event
    ADD CONSTRAINT emergency_event_mustering_event_id_fkey FOREIGN KEY (mustering_event_id) REFERENCES mustering_event(id);

ALTER TABLE ONLY emergency_notification
    ADD CONSTRAINT emergency_notification_emergency_event_id_fkey FOREIGN KEY (emergency_event_id) REFERENCES emergency_event(id);

ALTER TABLE ONLY emergency_notification_enhanced
    ADD CONSTRAINT emergency_notification_enhanced_emergency_event_id_fkey FOREIGN KEY (emergency_event_id) REFERENCES emergency_event_enhanced(id);

ALTER TABLE ONLY emergency_panic_log
    ADD CONSTRAINT emergency_panic_log_emergency_event_id_fkey FOREIGN KEY (emergency_event_id) REFERENCES emergency_event(id);

ALTER TABLE ONLY emergency_panic_log_enhanced
    ADD CONSTRAINT emergency_panic_log_enhanced_emergency_event_id_fkey FOREIGN KEY (emergency_event_id) REFERENCES emergency_event_enhanced(id);

ALTER TABLE ONLY emergency_panic_log_enhanced
    ADD CONSTRAINT emergency_panic_log_enhanced_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES auth_user(id);

ALTER TABLE ONLY emergency_panic_log_enhanced
    ADD CONSTRAINT emergency_panic_log_enhanced_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES auth_user(id);

ALTER TABLE ONLY emergency_panic_log
    ADD CONSTRAINT emergency_panic_log_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES auth_user(id);

ALTER TABLE ONLY emergency_plan
    ADD CONSTRAINT emergency_plan_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY emergency_device_enhanced
    ADD CONSTRAINT emg_dev_enh_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY emergency_template
    ADD CONSTRAINT emg_tmpl_muster_zone_fkey FOREIGN KEY (auto_mustering_zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY events
    ADD CONSTRAINT events_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY events
    ADD CONSTRAINT events_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY face
    ADD CONSTRAINT face_user_id_fkey FOREIGN KEY (user_id) REFERENCES personnel_employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY fingerprint
    ADD CONSTRAINT fingerprint_user_id_fkey FOREIGN KEY (user_id) REFERENCES personnel_employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY flight_log
    ADD CONSTRAINT flight_log_transport_id_fkey FOREIGN KEY (transport_id) REFERENCES transport(id);

ALTER TABLE ONLY iclock_bio_template
    ADD CONSTRAINT iclock_bio_template_source_sn_fkey FOREIGN KEY (source_sn) REFERENCES iclock_terminal(sn) ON DELETE SET NULL;

ALTER TABLE ONLY iclock_devcmd
    ADD CONSTRAINT iclock_devcmd_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth_user(id);

ALTER TABLE ONLY iclock_devcmd
    ADD CONSTRAINT iclock_devcmd_sn_fkey FOREIGN KEY (sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY iclock_operlog
    ADD CONSTRAINT iclock_operlog_terminal_sn_fkey FOREIGN KEY (terminal_sn) REFERENCES iclock_terminal(sn) ON DELETE CASCADE;

ALTER TABLE ONLY iclock_terminal
    ADD CONSTRAINT iclock_terminal_area_id_fkey FOREIGN KEY (area_id) REFERENCES personnel_area(id);

ALTER TABLE ONLY iclock_terminal
    ADD CONSTRAINT iclock_terminal_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id);

ALTER TABLE ONLY iclock_transaction
    ADD CONSTRAINT iclock_transaction_terminal_sn_fkey FOREIGN KEY (terminal_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY manifest_entry
    ADD CONSTRAINT manifest_entry_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE SET NULL;

ALTER TABLE ONLY manifest_entry
    ADD CONSTRAINT manifest_entry_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES transport_schedule(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_audit_log
    ADD CONSTRAINT mtd_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE SET NULL;

ALTER TABLE ONLY mtd_certification
    ADD CONSTRAINT mtd_certification_cert_type_id_fkey FOREIGN KEY (cert_type_id) REFERENCES mtd_cert_type(id);

ALTER TABLE ONLY mtd_certification
    ADD CONSTRAINT mtd_certification_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_certification
    ADD CONSTRAINT mtd_certification_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES auth_user(id);

ALTER TABLE ONLY mtd_certification
    ADD CONSTRAINT mtd_certification_visitor_id_fkey FOREIGN KEY (visitor_id) REFERENCES vis_visitor(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_compliance_log
    ADD CONSTRAINT mtd_compliance_log_cert_type_id_fkey FOREIGN KEY (cert_type_id) REFERENCES mtd_cert_type(id) ON DELETE SET NULL;

ALTER TABLE ONLY mtd_compliance_log
    ADD CONSTRAINT mtd_compliance_log_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth_user(id);

ALTER TABLE ONLY mtd_compliance_log
    ADD CONSTRAINT mtd_compliance_log_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_induction_record
    ADD CONSTRAINT mtd_induction_record_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_induction_record
    ADD CONSTRAINT mtd_induction_record_template_id_fkey FOREIGN KEY (template_id) REFERENCES mtd_induction_template(id);

ALTER TABLE ONLY mtd_induction_record
    ADD CONSTRAINT mtd_induction_record_trainer_emp_id_fkey FOREIGN KEY (trainer_emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY mtd_induction_record
    ADD CONSTRAINT mtd_induction_record_visitor_id_fkey FOREIGN KEY (visitor_id) REFERENCES vis_visitor(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_medical_record
    ADD CONSTRAINT mtd_medical_record_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_medical_record
    ADD CONSTRAINT mtd_medical_record_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES auth_user(id);

ALTER TABLE ONLY mtd_medical_record
    ADD CONSTRAINT mtd_medical_record_visitor_id_fkey FOREIGN KEY (visitor_id) REFERENCES vis_visitor(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_ppe_issue
    ADD CONSTRAINT mtd_ppe_issue_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY mtd_ppe_issue
    ADD CONSTRAINT mtd_ppe_issue_issued_by_fkey FOREIGN KEY (issued_by) REFERENCES auth_user(id);

ALTER TABLE ONLY mtd_ppe_issue
    ADD CONSTRAINT mtd_ppe_issue_ppe_type_id_fkey FOREIGN KEY (ppe_type_id) REFERENCES mtd_ppe_type(id);

ALTER TABLE ONLY mtg_action_item
    ADD CONSTRAINT mtg_action_item_assignee_emp_id_fkey FOREIGN KEY (assignee_emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY mtg_action_item
    ADD CONSTRAINT mtg_action_item_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES mtg_booking(id);

ALTER TABLE ONLY mtg_action_item
    ADD CONSTRAINT mtg_action_item_created_by_fkey FOREIGN KEY (created_by) REFERENCES personnel_employee(id);

ALTER TABLE ONLY mtg_attendance
    ADD CONSTRAINT mtg_attendance_attendee_id_fkey FOREIGN KEY (attendee_id) REFERENCES mtg_attendee(id);

ALTER TABLE ONLY mtg_attendance
    ADD CONSTRAINT mtg_attendance_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES mtg_booking(id);

ALTER TABLE ONLY mtg_attendance
    ADD CONSTRAINT mtg_attendance_device_sn_fkey FOREIGN KEY (device_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY mtg_attendee
    ADD CONSTRAINT mtg_attendee_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES mtg_booking(id);

ALTER TABLE ONLY mtg_attendee
    ADD CONSTRAINT mtg_attendee_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY mtg_attendee
    ADD CONSTRAINT mtg_attendee_pre_reg_id_fkey FOREIGN KEY (pre_reg_id) REFERENCES vis_pre_registration(id);

ALTER TABLE ONLY mtg_attendee
    ADD CONSTRAINT mtg_attendee_visitor_id_fkey FOREIGN KEY (visitor_id) REFERENCES vis_visitor(id);

ALTER TABLE ONLY mtg_booking
    ADD CONSTRAINT mtg_booking_approval_by_fkey FOREIGN KEY (approval_by) REFERENCES personnel_employee(id);

ALTER TABLE ONLY mtg_booking
    ADD CONSTRAINT mtg_booking_organizer_emp_id_fkey FOREIGN KEY (organizer_emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY mtg_booking
    ADD CONSTRAINT mtg_booking_room_id_fkey FOREIGN KEY (room_id) REFERENCES mtg_room(id);

ALTER TABLE ONLY mtg_equipment
    ADD CONSTRAINT mtg_equipment_room_id_fkey FOREIGN KEY (room_id) REFERENCES mtg_room(id);

ALTER TABLE ONLY mtg_minutes
    ADD CONSTRAINT mtg_minutes_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES mtg_booking(id);

ALTER TABLE ONLY mtg_minutes
    ADD CONSTRAINT mtg_minutes_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES personnel_employee(id);

ALTER TABLE ONLY mtg_room
    ADD CONSTRAINT mtg_room_area_id_fkey FOREIGN KEY (area_id) REFERENCES personnel_area(id);

ALTER TABLE ONLY mtg_room
    ADD CONSTRAINT mtg_room_door_id_fkey FOREIGN KEY (door_id) REFERENCES acc_door(id);

ALTER TABLE ONLY mtg_room
    ADD CONSTRAINT mtg_room_mustering_zone_fkey FOREIGN KEY (mustering_zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY mustering_drill_schedule
    ADD CONSTRAINT mustering_drill_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY mustering_escalation_record
    ADD CONSTRAINT mustering_escalation_record_event_id_fkey FOREIGN KEY (event_id) REFERENCES mustering_event(id);

ALTER TABLE ONLY mustering_event
    ADD CONSTRAINT mustering_event_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES auth_user(id);

ALTER TABLE ONLY mustering_event
    ADD CONSTRAINT mustering_event_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY mustering_expected
    ADD CONSTRAINT mustering_expected_dept_id_fkey FOREIGN KEY (dept_id) REFERENCES personnel_department(id);

ALTER TABLE ONLY mustering_expected
    ADD CONSTRAINT mustering_expected_event_id_fkey FOREIGN KEY (event_id) REFERENCES mustering_event(id);

ALTER TABLE ONLY mustering_expected
    ADD CONSTRAINT mustering_expected_shift_id_fkey FOREIGN KEY (shift_id) REFERENCES att_shift(id);

ALTER TABLE ONLY mustering_log
    ADD CONSTRAINT mustering_log_device_sn_fkey FOREIGN KEY (device_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY mustering_log
    ADD CONSTRAINT mustering_log_event_id_fkey FOREIGN KEY (event_id) REFERENCES mustering_event(id);

ALTER TABLE ONLY mustering_search_sweep
    ADD CONSTRAINT mustering_search_sweep_event_id_fkey FOREIGN KEY (event_id) REFERENCES mustering_event(id);

ALTER TABLE ONLY mustering_search_sweep
    ADD CONSTRAINT mustering_search_sweep_searcher_id_fkey FOREIGN KEY (searcher_id) REFERENCES auth_user(id);

ALTER TABLE ONLY onboarding_checklists
    ADD CONSTRAINT onboarding_checklists_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(id);

ALTER TABLE ONLY onboarding_checklists
    ADD CONSTRAINT onboarding_checklists_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY onboarding_checklists
    ADD CONSTRAINT onboarding_checklists_onboarding_id_fkey FOREIGN KEY (onboarding_id) REFERENCES onboardings(id);

ALTER TABLE ONLY onboarding_documents
    ADD CONSTRAINT onboarding_documents_onboarding_id_fkey FOREIGN KEY (onboarding_id) REFERENCES onboardings(id);

ALTER TABLE ONLY onboarding_documents
    ADD CONSTRAINT onboarding_documents_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES users(id);

ALTER TABLE ONLY onboarding_documents
    ADD CONSTRAINT onboarding_documents_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES users(id);

ALTER TABLE ONLY onboarding_notifications
    ADD CONSTRAINT onboarding_notifications_onboarding_id_fkey FOREIGN KEY (onboarding_id) REFERENCES onboardings(id);

ALTER TABLE ONLY onboarding_notifications
    ADD CONSTRAINT onboarding_notifications_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES users(id);

ALTER TABLE ONLY onboarding_task
    ADD CONSTRAINT onboarding_task_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES auth_user(id);

ALTER TABLE ONLY onboarding_task
    ADD CONSTRAINT onboarding_task_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY onboarding_tasks
    ADD CONSTRAINT onboarding_tasks_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(id);

ALTER TABLE ONLY onboarding_tasks
    ADD CONSTRAINT onboarding_tasks_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY onboarding_tasks
    ADD CONSTRAINT onboarding_tasks_onboarding_id_fkey FOREIGN KEY (onboarding_id) REFERENCES onboardings(id);

ALTER TABLE ONLY onboarding_templates
    ADD CONSTRAINT onboarding_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_buddy_id_fkey FOREIGN KEY (buddy_id) REFERENCES personnel(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_department_id_fkey FOREIGN KEY (department_id) REFERENCES departments(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_exit_interview_conducted_by_fkey FOREIGN KEY (exit_interview_conducted_by) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_position_id_fkey FOREIGN KEY (position_id) REFERENCES positions(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_reporting_to_fkey FOREIGN KEY (reporting_to) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES users(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_template_id_fkey FOREIGN KEY (template_id) REFERENCES onboarding_templates(id);

ALTER TABLE ONLY onboardings
    ADD CONSTRAINT onboardings_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES users(id);

ALTER TABLE ONLY overtime_record
    ADD CONSTRAINT overtime_record_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES auth_user(id);

ALTER TABLE ONLY overtime_record
    ADD CONSTRAINT overtime_record_emp_code_fkey FOREIGN KEY (emp_code) REFERENCES personnel_employee(emp_code);

ALTER TABLE ONLY overtime_record
    ADD CONSTRAINT overtime_record_overtime_rule_id_fkey FOREIGN KEY (overtime_rule_id) REFERENCES overtime_rule(id);

ALTER TABLE ONLY overtime_rule
    ADD CONSTRAINT overtime_rule_area_id_fkey FOREIGN KEY (area_id) REFERENCES personnel_area(id);

ALTER TABLE ONLY overtime_rule
    ADD CONSTRAINT overtime_rule_department_id_fkey FOREIGN KEY (department_id) REFERENCES personnel_department(id);

ALTER TABLE ONLY pay_audit_log
    ADD CONSTRAINT pay_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY pay_calculation_log
    ADD CONSTRAINT pay_calculation_log_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY pay_calculation_log
    ADD CONSTRAINT pay_calculation_log_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel(id);

ALTER TABLE ONLY pay_calculation_log
    ADD CONSTRAINT pay_calculation_log_period_id_fkey FOREIGN KEY (period_id) REFERENCES pay_period(id);

ALTER TABLE ONLY pay_contractor_rate
    ADD CONSTRAINT pay_contractor_rate_position_id_fkey FOREIGN KEY (position_id) REFERENCES positions(id);

ALTER TABLE ONLY pay_contractor_rate
    ADD CONSTRAINT pay_contractor_rate_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES vendors(id);

ALTER TABLE ONLY pay_item
    ADD CONSTRAINT pay_item_structure_id_fkey FOREIGN KEY (structure_id) REFERENCES pay_structure(id);

ALTER TABLE ONLY pay_loan
    ADD CONSTRAINT pay_loan_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(id);

ALTER TABLE ONLY pay_loan_deduction
    ADD CONSTRAINT pay_loan_deduction_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel(id);

ALTER TABLE ONLY pay_loan_deduction
    ADD CONSTRAINT pay_loan_deduction_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES pay_loan(id);

ALTER TABLE ONLY pay_loan_deduction
    ADD CONSTRAINT pay_loan_deduction_period_id_fkey FOREIGN KEY (period_id) REFERENCES pay_period(id);

ALTER TABLE ONLY pay_loan_deduction
    ADD CONSTRAINT pay_loan_deduction_salary_id_fkey FOREIGN KEY (salary_id) REFERENCES pay_salary(id);

ALTER TABLE ONLY pay_loan
    ADD CONSTRAINT pay_loan_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel(id);

ALTER TABLE ONLY pay_payslip_template
    ADD CONSTRAINT pay_payslip_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY pay_period
    ADD CONSTRAINT pay_period_closed_by_fkey FOREIGN KEY (closed_by) REFERENCES users(id);

ALTER TABLE ONLY pay_period
    ADD CONSTRAINT pay_period_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY pay_salary
    ADD CONSTRAINT pay_salary_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(id);

ALTER TABLE ONLY pay_salary
    ADD CONSTRAINT pay_salary_calc_by_fkey FOREIGN KEY (calc_by) REFERENCES users(id);

ALTER TABLE ONLY pay_salary
    ADD CONSTRAINT pay_salary_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES personnel(id);

ALTER TABLE ONLY pay_salary_item
    ADD CONSTRAINT pay_salary_item_item_id_fkey FOREIGN KEY (item_id) REFERENCES pay_item(id);

ALTER TABLE ONLY pay_salary_item
    ADD CONSTRAINT pay_salary_item_salary_id_fkey FOREIGN KEY (salary_id) REFERENCES pay_salary(id);

ALTER TABLE ONLY pay_salary
    ADD CONSTRAINT pay_salary_period_id_fkey FOREIGN KEY (period_id) REFERENCES pay_period(id);

ALTER TABLE ONLY pay_salary
    ADD CONSTRAINT pay_salary_structure_id_fkey FOREIGN KEY (structure_id) REFERENCES pay_structure(id);

ALTER TABLE ONLY pay_salary
    ADD CONSTRAINT pay_salary_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES users(id);

ALTER TABLE ONLY pay_structure_assign
    ADD CONSTRAINT pay_structure_assign_structure_id_fkey FOREIGN KEY (structure_id) REFERENCES pay_structure(id);

ALTER TABLE ONLY pay_structure
    ADD CONSTRAINT pay_structure_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY pay_zone_allowance
    ADD CONSTRAINT pay_zone_allowance_area_id_fkey FOREIGN KEY (area_id) REFERENCES zones(id);

ALTER TABLE ONLY pay_zone_allowance
    ADD CONSTRAINT pay_zone_allowance_structure_id_fkey FOREIGN KEY (structure_id) REFERENCES pay_structure(id);

ALTER TABLE ONLY personnel_assignments
    ADD CONSTRAINT personnel_assignments_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY personnel
    ADD CONSTRAINT personnel_current_zone_id_fkey FOREIGN KEY (current_zone_id) REFERENCES zones(id);

ALTER TABLE ONLY personnel_department
    ADD CONSTRAINT personnel_department_default_shift_id_fkey FOREIGN KEY (default_shift_id) REFERENCES att_shift(id) ON DELETE SET NULL;

ALTER TABLE ONLY personnel
    ADD CONSTRAINT personnel_department_id_fkey FOREIGN KEY (department_id) REFERENCES departments(id);

ALTER TABLE ONLY personnel_department
    ADD CONSTRAINT personnel_department_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES personnel_department(id);

ALTER TABLE ONLY personnel_employee
    ADD CONSTRAINT personnel_employee_area_id_fkey FOREIGN KEY (area_id) REFERENCES personnel_area(id);

ALTER TABLE ONLY personnel_employee
    ADD CONSTRAINT personnel_employee_dept_id_fkey FOREIGN KEY (dept_id) REFERENCES departments(id);

ALTER TABLE ONLY personnel
    ADD CONSTRAINT personnel_primary_role_id_fkey FOREIGN KEY (primary_role_id) REFERENCES roles(id);

ALTER TABLE ONLY personnel
    ADD CONSTRAINT personnel_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY pob_status
    ADD CONSTRAINT pob_status_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY resignation_documents
    ADD CONSTRAINT resignation_documents_resignation_id_fkey FOREIGN KEY (resignation_id) REFERENCES resignations(id);

ALTER TABLE ONLY resignation_documents
    ADD CONSTRAINT resignation_documents_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES users(id);

ALTER TABLE ONLY resignation_documents
    ADD CONSTRAINT resignation_documents_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES users(id);

ALTER TABLE ONLY resignation_notifications
    ADD CONSTRAINT resignation_notifications_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES users(id);

ALTER TABLE ONLY resignation_notifications
    ADD CONSTRAINT resignation_notifications_resignation_id_fkey FOREIGN KEY (resignation_id) REFERENCES resignations(id);

ALTER TABLE ONLY resignation_tasks
    ADD CONSTRAINT resignation_tasks_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(id);

ALTER TABLE ONLY resignation_tasks
    ADD CONSTRAINT resignation_tasks_resignation_id_fkey FOREIGN KEY (resignation_id) REFERENCES resignations(id);

ALTER TABLE ONLY resignation_templates
    ADD CONSTRAINT resignation_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_assets_return_conducted_by_fkey FOREIGN KEY (assets_return_conducted_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_completed_by_fkey FOREIGN KEY (completed_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_exit_interview_conducted_by_fkey FOREIGN KEY (exit_interview_conducted_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_financial_clearance_conducted_by_fkey FOREIGN KEY (financial_clearance_conducted_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_handover_conducted_by_fkey FOREIGN KEY (handover_conducted_by) REFERENCES users(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY resignations
    ADD CONSTRAINT resignations_system_access_revoked_by_fkey FOREIGN KEY (system_access_revoked_by) REFERENCES users(id);

ALTER TABLE ONLY role_assignments
    ADD CONSTRAINT role_assignments_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id) ON DELETE CASCADE;

ALTER TABLE ONLY role_assignments
    ADD CONSTRAINT role_assignments_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY role_permissions
    ADD CONSTRAINT role_permissions_permission_code_fkey FOREIGN KEY (permission_code) REFERENCES permissions(code) ON DELETE CASCADE;

ALTER TABLE ONLY role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY rpt_export_log
    ADD CONSTRAINT rpt_export_log_template_id_fkey FOREIGN KEY (template_id) REFERENCES rpt_template(id);

ALTER TABLE ONLY rpt_export_log
    ADD CONSTRAINT rpt_export_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id);

ALTER TABLE ONLY rpt_favorite
    ADD CONSTRAINT rpt_favorite_template_id_fkey FOREIGN KEY (template_id) REFERENCES rpt_template(id);

ALTER TABLE ONLY rpt_favorite
    ADD CONSTRAINT rpt_favorite_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id);

ALTER TABLE ONLY rpt_schedule
    ADD CONSTRAINT rpt_schedule_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth_user(id);

ALTER TABLE ONLY rpt_schedule
    ADD CONSTRAINT rpt_schedule_template_id_fkey FOREIGN KEY (template_id) REFERENCES rpt_template(id);

ALTER TABLE ONLY rpt_template
    ADD CONSTRAINT rpt_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth_user(id);

ALTER TABLE ONLY rpt_user_preset
    ADD CONSTRAINT rpt_user_preset_template_id_fkey FOREIGN KEY (template_id) REFERENCES rpt_template(id);

ALTER TABLE ONLY rpt_user_preset
    ADD CONSTRAINT rpt_user_preset_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id);

ALTER TABLE ONLY ssr
    ADD CONSTRAINT ssr_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES auth_user(id);

ALTER TABLE ONLY ssr
    ADD CONSTRAINT ssr_user_id_fkey FOREIGN KEY (user_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY sys_renewal_log
    ADD CONSTRAINT sys_renewal_log_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES sys_subscription(id) ON DELETE CASCADE;

ALTER TABLE ONLY sys_role_permissions
    ADD CONSTRAINT sys_role_permissions_permission_code_fkey FOREIGN KEY (permission_code) REFERENCES sys_permissions(code) ON DELETE CASCADE;

ALTER TABLE ONLY sys_role_permissions
    ADD CONSTRAINT sys_role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES sys_roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY sys_user_roles
    ADD CONSTRAINT sys_user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES sys_roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY transport_assignments
    ADD CONSTRAINT transport_assignments_booked_by_fkey FOREIGN KEY (booked_by) REFERENCES users(id);

ALTER TABLE ONLY transport_assignments
    ADD CONSTRAINT transport_assignments_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY transport_crew
    ADD CONSTRAINT transport_crew_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY transport_crew
    ADD CONSTRAINT transport_crew_transport_id_fkey FOREIGN KEY (transport_id) REFERENCES transport(id);

ALTER TABLE ONLY transport_inventory
    ADD CONSTRAINT transport_inventory_transport_id_fkey FOREIGN KEY (transport_id) REFERENCES transport(id);

ALTER TABLE ONLY transport_maintenance
    ADD CONSTRAINT transport_maintenance_transport_id_fkey FOREIGN KEY (transport_id) REFERENCES transport(id);

ALTER TABLE ONLY transport_schedule
    ADD CONSTRAINT transport_schedule_transport_id_fkey FOREIGN KEY (transport_id) REFERENCES transport(id);

ALTER TABLE ONLY user_extensions
    ADD CONSTRAINT user_extensions_default_role_id_fkey FOREIGN KEY (default_role_id) REFERENCES sys_roles(id);

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES users(id);

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id);

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY vis_blacklist
    ADD CONSTRAINT vis_blacklist_added_by_fkey FOREIGN KEY (added_by) REFERENCES auth_user(id);

ALTER TABLE ONLY vis_pre_registration
    ADD CONSTRAINT vis_pre_registration_approval_by_fkey FOREIGN KEY (approval_by) REFERENCES personnel_employee(id);

ALTER TABLE ONLY vis_pre_registration
    ADD CONSTRAINT vis_pre_registration_area_id_fkey FOREIGN KEY (area_id) REFERENCES personnel_area(id);

ALTER TABLE ONLY vis_pre_registration
    ADD CONSTRAINT vis_pre_registration_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth_user(id);

ALTER TABLE ONLY vis_pre_registration
    ADD CONSTRAINT vis_pre_registration_host_emp_id_fkey FOREIGN KEY (host_emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY vis_pre_registration
    ADD CONSTRAINT vis_pre_registration_visitor_id_fkey FOREIGN KEY (visitor_id) REFERENCES vis_visitor(id);

ALTER TABLE ONLY vis_type
    ADD CONSTRAINT vis_type_access_level_id_fkey FOREIGN KEY (access_level_id) REFERENCES acc_level(id);

ALTER TABLE ONLY vis_type
    ADD CONSTRAINT vis_type_mustering_zone_fkey FOREIGN KEY (mustering_zone_id) REFERENCES zones(id) ON DELETE SET NULL;

ALTER TABLE ONLY vis_visit_log
    ADD CONSTRAINT vis_visit_log_area_id_fkey FOREIGN KEY (area_id) REFERENCES personnel_area(id);

ALTER TABLE ONLY vis_visit_log
    ADD CONSTRAINT vis_visit_log_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth_user(id);

ALTER TABLE ONLY vis_visit_log
    ADD CONSTRAINT vis_visit_log_device_sn_fkey FOREIGN KEY (device_sn) REFERENCES iclock_terminal(sn);

ALTER TABLE ONLY vis_visit_log
    ADD CONSTRAINT vis_visit_log_host_emp_id_fkey FOREIGN KEY (host_emp_id) REFERENCES personnel_employee(id);

ALTER TABLE ONLY vis_visit_log
    ADD CONSTRAINT vis_visit_log_pre_reg_id_fkey FOREIGN KEY (pre_reg_id) REFERENCES vis_pre_registration(id);

ALTER TABLE ONLY vis_visit_log
    ADD CONSTRAINT vis_visit_log_visitor_id_fkey FOREIGN KEY (visitor_id) REFERENCES vis_visitor(id);

ALTER TABLE ONLY vis_visitor
    ADD CONSTRAINT vis_visitor_visitor_type_id_fkey FOREIGN KEY (visitor_type_id) REFERENCES vis_type(id);

ALTER TABLE ONLY zone_personnel_assignments
    ADD CONSTRAINT zone_personnel_assignments_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES users(id);

ALTER TABLE ONLY zone_personnel_assignments
    ADD CONSTRAINT zone_personnel_assignments_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY zone_personnel_assignments
    ADD CONSTRAINT zone_personnel_assignments_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id);

ALTER TABLE ONLY zone_personnel_tracking
    ADD CONSTRAINT zone_personnel_tracking_personnel_id_fkey FOREIGN KEY (personnel_id) REFERENCES personnel(id);

ALTER TABLE ONLY zone_personnel_tracking
    ADD CONSTRAINT zone_personnel_tracking_previous_zone_id_fkey FOREIGN KEY (previous_zone_id) REFERENCES zones(id);

ALTER TABLE ONLY zone_personnel_tracking
    ADD CONSTRAINT zone_personnel_tracking_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id);

ALTER TABLE ONLY zone_reader_assignments
    ADD CONSTRAINT zone_reader_assignments_reader_id_fkey FOREIGN KEY (reader_id) REFERENCES devices(id);

ALTER TABLE ONLY zone_reader_assignments
    ADD CONSTRAINT zone_reader_assignments_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES zones(id);


-- ── Business Central integration (created by API on first use; included here for
--    new-server deployments so alembic upgrade head is sufficient) ─────────────

CREATE SEQUENCE IF NOT EXISTS bc_integration_config_id_seq
    AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;

CREATE TABLE IF NOT EXISTS bc_integration_config (
    id             integer NOT NULL DEFAULT nextval('bc_integration_config_id_seq'),
    tenant_id      character varying(200),
    client_id      character varying(200),
    client_secret  character varying(500),
    environment    character varying(50)  DEFAULT 'Production',
    company_id     character varying(100),
    company_name   character varying(200),
    is_enabled     boolean              DEFAULT false,
    sync_time      character varying(10) DEFAULT '01:00',
    updated_at     timestamp with time zone DEFAULT now(),
    CONSTRAINT bc_integration_config_pkey PRIMARY KEY (id)
);

CREATE SEQUENCE IF NOT EXISTS bc_sync_log_id_seq
    AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;

CREATE TABLE IF NOT EXISTS bc_sync_log (
    id              integer NOT NULL DEFAULT nextval('bc_sync_log_id_seq'),
    sync_date       date,
    triggered_by    character varying(50),
    status          character varying(20),
    records_built   integer DEFAULT 0,
    records_sent    integer DEFAULT 0,
    records_failed  integer DEFAULT 0,
    message         character varying(500),
    created_at      timestamp with time zone DEFAULT now(),
    CONSTRAINT bc_sync_log_pkey PRIMARY KEY (id)
);
