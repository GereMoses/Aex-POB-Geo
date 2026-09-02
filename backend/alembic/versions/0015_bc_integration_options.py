"""Add bc_integration_config.options

``BCIntegrationConfig.options`` is mapped and the Business Central connector
reads it, but the baseline never created the column — the running database
acquired it out of band, so only a FRESH install was broken. Found by diffing a
clean `alembic upgrade head` against the live schema.

Its sibling ``hr_integration_config.options`` was repaired in
0014_repair_remaining_drift for the same reason.

Revision ID: 0015_bc_integration_options
Revises: 0014_repair_remaining_drift
"""
from alembic import op

revision = "0015_bc_integration_options"
down_revision = "0014_repair_remaining_drift"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE IF EXISTS bc_integration_config "
        "ADD COLUMN IF NOT EXISTS options jsonb;"
    )


def downgrade():
    op.execute(
        "ALTER TABLE IF EXISTS bc_integration_config "
        "DROP COLUMN IF EXISTS options;"
    )
