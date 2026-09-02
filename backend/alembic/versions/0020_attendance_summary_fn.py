"""Create the missing get_attendance_summary function

`GET /api/v1/self-service/my-attendance` calls this function, which was never
created — the endpoint returned a 500 with the raw psycopg2 text
("function get_attendance_summary(unknown, date, date) does not exist"), which
also leaked driver internals to the caller in production.

Column order matches how the endpoint indexes the row (0..7).

Revision ID: 0020_attendance_summary_fn
Revises: 0019_exception_resolution
"""
from alembic import op

revision = "0020_attendance_summary_fn"
down_revision = "0019_exception_resolution"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
CREATE OR REPLACE FUNCTION get_attendance_summary(
    p_emp_code  varchar,
    p_start     date,
    p_end       date
)
RETURNS TABLE (
    att_date        date,
    check_in        timestamptz,
    check_out       timestamptz,
    work_hours      numeric,
    late_minutes    integer,
    early_minutes   integer,
    att_status      smallint,
    is_holiday      boolean
)
LANGUAGE sql
STABLE
AS $$
    SELECT r.att_date,
           r.check_in,
           r.check_out,
           ROUND(COALESCE(r.work_minutes, 0) / 60.0, 2)::numeric AS work_hours,
           COALESCE(r.late_minutes, 0)::integer,
           COALESCE(r.early_minutes, 0)::integer,
           COALESCE(r.att_status, 0)::smallint,
           EXISTS (
               -- Holidays are stored as a range, not a single date.
               SELECT 1 FROM att_holiday h
               WHERE r.att_date BETWEEN h.start_date
                                    AND COALESCE(h.end_date, h.start_date)
                 AND COALESCE(h.is_active, TRUE)
           ) AS is_holiday
    FROM att_report r
    JOIN personnel_employee pe ON pe.id = r.emp_id
    WHERE UPPER(pe.emp_code) = UPPER(p_emp_code)
      AND r.att_date BETWEEN p_start AND p_end
    ORDER BY r.att_date;
$$;
    """)


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS get_attendance_summary(varchar, date, date)")
