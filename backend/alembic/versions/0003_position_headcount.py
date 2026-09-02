"""Add headcount column to positions table

Revision ID: 0003_position_headcount
Revises: 0002_security_columns
Create Date: 2026-06-13
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0003_position_headcount"
down_revision = "0002_security_columns"
branch_labels = None
depends_on = None


def upgrade():
    mh.add_column(
        "positions",
        sa.Column("headcount", sa.Integer(), nullable=True, server_default="1"),
    )


def downgrade():
    op.drop_column("positions", "headcount")
