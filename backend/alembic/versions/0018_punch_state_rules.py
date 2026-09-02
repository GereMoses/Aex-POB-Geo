"""Duplicate-punch suppression and clock-state rules

The punch endpoint accepted an unlimited number of identical punches: three
clock-ins 1.3 seconds apart were all recorded, and a clock-out with no
preceding clock-in was accepted and paired to (None, out_time), contributing
zero worked minutes. An employee whose clock-in was rejected for GPS accuracy
but whose clock-out succeeded was therefore silently recorded as having worked
nothing.

Both are policy so a site can tune them: a warehouse with a single gate wants a
longer window than one where staff legitimately re-punch at different doors.

Revision ID: 0018_punch_state_rules
Revises: 0017_sync_personnel_employee
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0018_punch_state_rules"
down_revision = "0017_sync_personnel_employee"
branch_labels = None
depends_on = None


def upgrade():
    mh.add_column("geofence_policy", sa.Column(
        "duplicate_punch_seconds", sa.Integer(), nullable=False, server_default="120"))
    mh.add_column("geofence_policy", sa.Column(
        "enforce_punch_order", sa.Boolean(), nullable=False, server_default="true"))


def downgrade():
    op.execute("ALTER TABLE IF EXISTS geofence_policy DROP COLUMN IF EXISTS enforce_punch_order")
    op.execute("ALTER TABLE IF EXISTS geofence_policy DROP COLUMN IF EXISTS duplicate_punch_seconds")
