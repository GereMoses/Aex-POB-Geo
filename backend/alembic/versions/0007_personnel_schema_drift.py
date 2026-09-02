"""Reconcile personnel columns missing from the alembic baseline

The Personnel model declares hr_source, hr_synced_at, on_leave and
leave_end_date. database/init/complete_schema.sql creates them, but
alembic/versions/schema_ddl.sql does not — the two seeds have drifted.

A database built from the alembic baseline therefore fails every personnel
query with UndefinedColumn, which takes out the personnel list, the employee
reports and anything else that selects the whole model. Adding them here means
a database converges on the same shape whichever seed it started from.

Revision ID: 0007_personnel_schema_drift
Revises: 0006_geofence_policy
Create Date: 2026-08-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_personnel_schema_drift"
down_revision = "0006_geofence_policy"
branch_labels = None
depends_on = None


COLUMNS = [
    ("hr_source", "VARCHAR(50)"),
    ("hr_synced_at", "TIMESTAMPTZ"),
    ("on_leave", "BOOLEAN DEFAULT FALSE"),
    ("leave_end_date", "DATE"),
]


def upgrade():
    # IF NOT EXISTS throughout: a database seeded from complete_schema.sql
    # already has these, and this must be a no-op there rather than an error.
    for name, ddl in COLUMNS:
        op.execute(f"ALTER TABLE personnel ADD COLUMN IF NOT EXISTS {name} {ddl}")


def downgrade():
    # Deliberately not dropped. These columns are part of the model and are
    # present in the primary schema file; removing them would break the
    # application rather than restore an earlier state.
    pass
