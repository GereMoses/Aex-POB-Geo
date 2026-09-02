"""Make the mock-location block configurable

Every other integrity signal is tunable through geofence_policy; mock location
alone was a hardcoded hard refusal. That is the right default, but it also
makes an emulator useless for testing the accepted path — an emulator feeds
position through Android's mock provider, so it can never produce a punch that
succeeds.

Defaults to on, so an existing deployment behaves exactly as before.

Revision ID: 0011_mock_location_policy
Revises: 0010_face_verification
Create Date: 2026-08-30
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0011_mock_location_policy"
down_revision = "0010_face_verification"
branch_labels = None
depends_on = None


def upgrade():
    mh.add_column("geofence_policy",
                  sa.Column("block_mock_location", sa.Boolean(), nullable=False,
                            server_default="true"))
    # Weight applied when the block is off, so a mock-location punch is still
    # recorded as suspicious rather than passing unremarked.
    mh.add_column("geofence_policy",
                  sa.Column("risk_mock_location", sa.Integer(), nullable=False,
                            server_default="50"))


def downgrade():
    op.drop_column("geofence_policy", "risk_mock_location")
    op.drop_column("geofence_policy", "block_mock_location")
