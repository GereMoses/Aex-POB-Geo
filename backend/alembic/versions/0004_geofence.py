"""Geofenced mobile attendance: zone fence config + punch evidence trail

Revision ID: 0004_geofence
Revises: 0003_position_headcount
Create Date: 2026-08-29
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_geofence"
down_revision = "0003_position_headcount"
branch_labels = None
depends_on = None


# Fence configuration lives on zones — a warehouse is a zone.
# Existing latitude/longitude are varchar and read as strings elsewhere
# (zones.py:85), so we add numeric columns rather than alter them in place.
ZONE_COLUMNS = [
    ("geofence_enabled", sa.Boolean(), {"nullable": False, "server_default": "false"}),
    ("geofence_lat", sa.Numeric(10, 7), {"nullable": True}),
    ("geofence_lng", sa.Numeric(10, 7), {"nullable": True}),
    ("geofence_radius_m", sa.Integer(), {"nullable": False, "server_default": "200"}),
    ("geofence_polygon", postgresql.JSONB(), {"nullable": True}),
    ("gps_accuracy_max_m", sa.Integer(), {"nullable": False, "server_default": "100"}),
    ("accuracy_buffer_cap_m", sa.Integer(), {"nullable": False, "server_default": "50"}),
    ("require_selfie", sa.Boolean(), {"nullable": False, "server_default": "false"}),
    ("mobile_terminal_sn", sa.String(20), {"nullable": True}),
]


def upgrade():
    for name, type_, kwargs in ZONE_COLUMNS:
        mh.add_column("zones", sa.Column(name, type_, **kwargs))

    # Backfill numeric coords from the legacy varchar columns where they parse
    # cleanly, so existing sites do not need re-entering.
    op.execute("""
        UPDATE zones
        SET geofence_lat = latitude::numeric,
            geofence_lng = longitude::numeric
        WHERE latitude  ~ '^-?[0-9]{1,3}(\\.[0-9]+)?$'
          AND longitude ~ '^-?[0-9]{1,3}(\\.[0-9]+)?$'
          AND latitude::numeric BETWEEN -90  AND 90
          AND longitude::numeric BETWEEN -180 AND 180
    """)

    # Each warehouse gets a virtual terminal so mobile punches flow into
    # iclock_transaction exactly like a physical reader's would. terminal_sn is
    # varchar(20), so the id-based form stays well inside the limit.
    op.execute("UPDATE zones SET mobile_terminal_sn = 'MOB-' || LPAD(id::text, 6, '0')")
    mh.create_unique_constraint("uq_zones_mobile_terminal_sn", "zones", ["mobile_terminal_sn"])

    mh.create_table(
        "mobile_punch_evidence",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        # Null for rejected punches — they never become transactions.
        sa.Column("transaction_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("emp_code", sa.String(20), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("punch_state", sa.SmallInteger(), nullable=True),

        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(64), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),

        # Where the device claimed to be, and how that scored against the fence.
        sa.Column("device_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("device_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("gps_accuracy_m", sa.Float(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("effective_radius_m", sa.Float(), nullable=True),

        # server_time is authoritative. device_time is retained only as evidence
        # of clock tampering — never used for attendance calculation.
        sa.Column("device_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("server_time", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("clock_skew_seconds", sa.Float(), nullable=True),

        sa.Column("device_id", sa.String(128), nullable=True, index=True),
        sa.Column("platform", sa.String(16), nullable=True),
        sa.Column("app_version", sa.String(32), nullable=True),

        # Device integrity signals. With Wi-Fi verification out of scope these
        # carry the whole anti-spoofing burden.
        sa.Column("is_mock_location", sa.Boolean(), nullable=True),
        sa.Column("is_rooted", sa.Boolean(), nullable=True),
        sa.Column("is_emulator", sa.Boolean(), nullable=True),
        sa.Column("attestation_verdict", sa.String(32), nullable=True),
        sa.Column("travel_speed_kmh", sa.Float(), nullable=True),

        sa.Column("raw", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    mh.create_index("idx_mpe_emp_time", "mobile_punch_evidence",
                    ["emp_code", sa.text("server_time DESC")])
    mh.create_index("idx_mpe_zone_time", "mobile_punch_evidence",
                    ["zone_id", sa.text("server_time DESC")])
    mh.create_index("idx_mpe_decision", "mobile_punch_evidence", ["decision"])


def downgrade():
    op.drop_table("mobile_punch_evidence")
    op.drop_constraint("uq_zones_mobile_terminal_sn", "zones", type_="unique")
    for name, _, _ in ZONE_COLUMNS:
        op.drop_column("zones", name)
