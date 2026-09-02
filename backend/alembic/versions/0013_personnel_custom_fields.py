"""Add personnel.custom_fields

The BioTime-compatible personnel layer has always read and written
``Personnel.custom_fields`` (see ``personnel_biotime_service`` and the
``EmployeeCreate`` / ``EmployeeResponse`` schemas), but the column was never
created. Every read raised ``AttributeError`` — which is what made
``GET /api/v1/personnel/employees/export/`` return 500 — and
``create_employee`` passed it as a constructor kwarg the model did not accept.

Revision ID: 0013_personnel_custom_fields
Revises: 0012_sync_zone_coordinates
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013_personnel_custom_fields"
down_revision = "0012_sync_zone_coordinates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    existing = {
        r[0] for r in conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'personnel'"
        ))
    }
    if "custom_fields" not in existing:
        op.add_column(
            "personnel",
            sa.Column("custom_fields", postgresql.JSONB(), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    existing = {
        r[0] for r in conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'personnel'"
        ))
    }
    if "custom_fields" in existing:
        op.drop_column("personnel", "custom_fields")
