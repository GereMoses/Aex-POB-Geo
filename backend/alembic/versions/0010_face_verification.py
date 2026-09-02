"""Automated face verification at clock-in

Geofencing proves a phone was at the warehouse; it says nothing about who was
holding it. Until now the punch selfie was queued for a supervisor to eyeball.
This stores a reference embedding per employee so the comparison happens at the
moment of the punch.

Embeddings, not photos, are what gets stored for matching: a 512-float vector
cannot be turned back into a face, so a database leak does not hand anyone a
biometric photo library.

Revision ID: 0010_face_verification
Revises: 0009_client_trust_and_reasons
Create Date: 2026-08-29
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0010_face_verification"
down_revision = "0009_client_trust_and_reasons"
branch_labels = None
depends_on = None


def upgrade():
    mh.create_table(
        "personnel_face_enrollment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("personnel_id", sa.Integer(), nullable=False, unique=True, index=True),
        # 512 float32s, stored raw. Not reversible to an image.
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        # Embeddings are only comparable within the same model, so the model
        # that produced this one is recorded; a model change invalidates them.
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        # The reference photo, kept on the private volume for a supervisor to
        # compare against by eye when a match is disputed.
        sa.Column("reference_photo_path", sa.String(500), nullable=True),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("enrolled_by", sa.String(150), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Cosine similarity above which two faces are treated as the same person.
    # Measured against the reference model: different people scored at most
    # 0.23, the same person at least 0.93, so 0.40 sits well clear of both.
    # Real-world captures vary more than a test set, so this is tunable.
    mh.add_column("geofence_policy",
                  sa.Column("face_match_threshold", sa.Float(), nullable=False,
                            server_default="0.40"))
    mh.add_column("geofence_policy",
                  sa.Column("face_matching_enabled", sa.Boolean(), nullable=False,
                            server_default="true"))
    # Whether a mismatch refuses the punch or merely flags it. Off by default:
    # a false rejection strands somebody at the gate, and until an estate has
    # good enrolment photos the failure mode is more likely to be a bad
    # reference than an impostor.
    mh.add_column("geofence_policy",
                  sa.Column("block_on_face_mismatch", sa.Boolean(), nullable=False,
                            server_default="false"))


def downgrade():
    for c in ("block_on_face_mismatch", "face_matching_enabled", "face_match_threshold"):
        op.drop_column("geofence_policy", c)
    op.drop_table("personnel_face_enrollment")
