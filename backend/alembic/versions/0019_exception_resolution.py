"""Give punch exceptions a resolution state

The queue could never be cleared. `mobile_punch_evidence` had no resolved flag,
and the review endpoint only wrote `face_verdict` — so a punch REJECTED for
location was untouched by a review and reappeared in the default queue forever.
With a 42% block rate on the demo estate, the pilot activity that depends on
this queue (tuning fence radii against real GPS behaviour) becomes impossible
within days.

Resolving records a decision about an exception; it never alters the punch, its
risk score or its decision, which stay as the evidence they are.

Revision ID: 0019_exception_resolution
Revises: 0018_punch_state_rules
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0019_exception_resolution"
down_revision = "0018_punch_state_rules"
branch_labels = None
depends_on = None


def upgrade():
    mh.add_column("mobile_punch_evidence",
                  sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    mh.add_column("mobile_punch_evidence",
                  sa.Column("resolved_by", sa.String(150), nullable=True))
    mh.add_column("mobile_punch_evidence",
                  sa.Column("resolution", sa.String(32), nullable=True))
    mh.add_column("mobile_punch_evidence",
                  sa.Column("resolution_note", sa.Text(), nullable=True))
    # The open queue is the hot read: unresolved rows, newest first.
    mh.create_index("idx_mpe_unresolved", "mobile_punch_evidence",
                    ["server_time"], postgresql_where=sa.text("resolved_at IS NULL"))


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_mpe_unresolved")
    for c in ("resolution_note", "resolution", "resolved_by", "resolved_at"):
        op.execute(f"ALTER TABLE IF EXISTS mobile_punch_evidence DROP COLUMN IF EXISTS {c}")
