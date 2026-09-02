"""Keep personnel_employee in step with personnel

The attendance calculator, self-service and the reports all join through
``personnel_employee``, but nothing outside a rarely-used BioTime-compatibility
endpoint ever inserted into it. The table was empty while ``personnel`` held
every employee, so ``_process_employee`` hit its ``if not pe: return`` guard for
everybody and wrote no attendance at all — while the batch loop still counted
each employee as processed and the API reported success. No timesheet, worked
hours, lateness or overtime figure was ever produced.

A trigger rather than application code, because employees arrive through several
paths — the personnel API, CSV/Excel import, bulk provisioning and direct SQL —
and every one of them has to keep the pair in step. ``sync_auth_user_to_users``
already establishes this pattern in the schema.

Revision ID: 0017_sync_personnel_employee
Revises: 0016_self_enrolment
"""
from alembic import op

revision = "0017_sync_personnel_employee"
down_revision = "0016_self_enrolment"
branch_labels = None
depends_on = None


def upgrade():
    # last_name is NOT NULL on personnel_employee, so fall back through
    # full_name to emp_code rather than dropping the row.
    op.execute("""
CREATE OR REPLACE FUNCTION sync_personnel_to_employee() RETURNS trigger AS $$
BEGIN
    INSERT INTO personnel_employee
        (emp_code, first_name, last_name, dept_id, hire_date,
         photo, card_no, status, created_at, updated_at)
    VALUES (
        NEW.emp_code,
        NEW.first_name,
        COALESCE(NULLIF(NEW.last_name, ''), NULLIF(NEW.full_name, ''), NEW.emp_code),
        NEW.department_id,
        NEW.hire_date,
        NEW.photo_url,
        NEW.badge_id,
        CASE WHEN COALESCE(NEW.is_active, TRUE) THEN 0 ELSE 1 END,
        now(), now()
    )
    ON CONFLICT (emp_code) DO UPDATE SET
        first_name = EXCLUDED.first_name,
        last_name  = EXCLUDED.last_name,
        dept_id    = EXCLUDED.dept_id,
        hire_date  = EXCLUDED.hire_date,
        photo      = EXCLUDED.photo,
        card_no    = EXCLUDED.card_no,
        status     = EXCLUDED.status,
        updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
    """)

    # emp_code is the join key everywhere; the upsert above needs it unique.
    op.execute("""
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'personnel_employee_emp_code_key'
    ) THEN
        ALTER TABLE personnel_employee
            ADD CONSTRAINT personnel_employee_emp_code_key UNIQUE (emp_code);
    END IF;
END $$;
    """)

    op.execute("DROP TRIGGER IF EXISTS trg_sync_personnel_employee ON personnel")
    op.execute("""
CREATE TRIGGER trg_sync_personnel_employee
AFTER INSERT OR UPDATE ON personnel
FOR EACH ROW EXECUTE FUNCTION sync_personnel_to_employee();
    """)

    # Backfill everyone who already exists.
    op.execute("""
INSERT INTO personnel_employee
    (emp_code, first_name, last_name, dept_id, hire_date,
     photo, card_no, status, created_at, updated_at)
SELECT p.emp_code,
       p.first_name,
       COALESCE(NULLIF(p.last_name, ''), NULLIF(p.full_name, ''), p.emp_code),
       p.department_id,
       p.hire_date,
       p.photo_url,
       p.badge_id,
       CASE WHEN COALESCE(p.is_active, TRUE) THEN 0 ELSE 1 END,
       now(), now()
FROM personnel p
ON CONFLICT (emp_code) DO NOTHING;
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_sync_personnel_employee ON personnel")
    op.execute("DROP FUNCTION IF EXISTS sync_personnel_to_employee()")
