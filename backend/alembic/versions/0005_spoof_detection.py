"""Anti-spoofing signals and punch selfie capture

Adds the evidence fields behind three spoofing detectors — GPS drift, altitude
plausibility, approach-path continuity — plus selfie capture at punch time.

Revision ID: 0005_spoof_detection
Revises: 0004_geofence
Create Date: 2026-08-29
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0005_spoof_detection"
down_revision = "0004_geofence"
branch_labels = None
depends_on = None


EVIDENCE_COLUMNS = [
    # Altitude plausibility. Most fake-GPS apps either omit altitude or report a
    # flat zero, so a large delta against the site's known elevation is a tell.
    ("altitude_m", sa.Float(), {"nullable": True}),
    ("altitude_delta_m", sa.Float(), {"nullable": True}),

    # GPS drift. A genuine fix jitters by a few metres between samples; a
    # spoofed one is pinned to an exact coordinate and does not move at all.
    ("gps_drift_m", sa.Float(), {"nullable": True}),
    ("sample_count", sa.Integer(), {"nullable": True}),

    # Approach continuity. A real arrival leaves a contiguous track; a spoof
    # teleports between consecutive fixes.
    ("approach_max_speed_kmh", sa.Float(), {"nullable": True}),
    ("approach_teleport", sa.Boolean(), {"nullable": True}),

    # Selfie captured at the moment of punch. Geofencing proves a phone was on
    # site; only the photo speaks to who was holding it.
    ("selfie_path", sa.String(500), {"nullable": True}),
    ("face_verdict", sa.String(32), {"nullable": True}),
    ("face_score", sa.Float(), {"nullable": True}),
]


def upgrade():
    for name, type_, kwargs in EVIDENCE_COLUMNS:
        mh.add_column("mobile_punch_evidence", sa.Column(name, type_, **kwargs))

    # Site elevation in metres, for the altitude check. Null disables it.
    mh.add_column("zones", sa.Column("elevation_m", sa.Float(), nullable=True))

    # Surfaces the review queue: punches awaiting a supervisor's look at the
    # selfie, newest first.
    mh.create_index(
        "idx_mpe_face_pending", "mobile_punch_evidence",
        ["face_verdict", sa.text("server_time DESC")],
        postgresql_where=sa.text("face_verdict = 'PENDING_REVIEW'"),
    )


def downgrade():
    op.drop_index("idx_mpe_face_pending", table_name="mobile_punch_evidence")
    op.drop_column("zones", "elevation_m")
    for name, _, _ in EVIDENCE_COLUMNS:
        op.drop_column("mobile_punch_evidence", name)
