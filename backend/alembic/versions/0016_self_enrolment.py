"""Face self-enrolment

Until now a reference face could only be created by calling the admin API
directly — there was no screen for it anywhere, so in practice nobody was
enrolled and every punch selfie landed in the review queue unmatched.

Two additions:

  * ``geofence_policy.allow_self_enrolment`` — lets staff register their own
    face from the app the first time they clock in. Trust-on-first-use, which
    is the only thing that scales to thousands of staff across 500 sites.
  * ``personnel_face_enrollment.enrolled_source`` — records whether a reference
    came from an administrator or from the employee themselves, so a supervisor
    can tell which references have actually been vouched for.

Self-enrolment can only CREATE a reference, never replace one; overwriting is
an administrator action. Otherwise anyone who got hold of an account could
quietly re-point it at their own face.

Revision ID: 0016_self_enrolment
Revises: 0015_bc_integration_options
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0016_self_enrolment"
down_revision = "0015_bc_integration_options"
branch_labels = None
depends_on = None


def upgrade():
    mh.add_column("geofence_policy", sa.Column(
        "allow_self_enrolment", sa.Boolean(), nullable=False, server_default="true"))
    mh.add_column("personnel_face_enrollment", sa.Column(
        "enrolled_source", sa.String(10), nullable=False, server_default="ADMIN"))
    # Anything already on file predates self-enrolment, so it came from an admin.
    op.execute("UPDATE personnel_face_enrollment SET enrolled_source = 'ADMIN' "
               "WHERE enrolled_source IS NULL")


def downgrade():
    op.execute("ALTER TABLE IF EXISTS personnel_face_enrollment "
               "DROP COLUMN IF EXISTS enrolled_source")
    op.execute("ALTER TABLE IF EXISTS geofence_policy "
               "DROP COLUMN IF EXISTS allow_self_enrolment")
