"""Global clock-in rules + staff-to-warehouse assignment index

Revision ID: 0006_geofence_policy
Revises: 0005_spoof_detection
Create Date: 2026-08-29
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0006_geofence_policy"
down_revision = "0005_spoof_detection"
branch_labels = None
depends_on = None


def upgrade():
    # Single-row table, following the per-module config pattern already used by
    # bc_integration_config and hr_integration_config. These thresholds were
    # module constants; an administrator has to be able to tune them without a
    # redeploy, because the right values only emerge from real GPS behaviour at
    # the client's own sites.
    mh.create_table(
        "geofence_policy",
        sa.Column("id", sa.Integer(), primary_key=True),

        # Hard limits.
        sa.Column("impossible_travel_kmh", sa.Float(), nullable=False, server_default="900"),
        sa.Column("approach_max_ground_speed_kmh", sa.Float(), nullable=False, server_default="200"),
        sa.Column("reject_risk_threshold", sa.Integer(), nullable=False, server_default="80"),

        # Detector sensitivity.
        sa.Column("min_expected_drift_m", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("min_drift_samples", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("altitude_tolerance_m", sa.Float(), nullable=False, server_default="150"),
        sa.Column("clock_skew_flag_seconds", sa.Float(), nullable=False, server_default="300"),

        # Risk weights. Exposed because the balance between catching fraud and
        # stranding honest staff at the gate is a business decision, not ours.
        sa.Column("risk_rooted_device", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("risk_static_gps", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("risk_implausible_altitude", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("risk_zero_altitude", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("risk_implausible_accuracy", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("risk_clock_skew", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("risk_accuracy_buffer", sa.Integer(), nullable=False, server_default="10"),

        # Some sites will want a rooted handset refused outright rather than
        # merely flagged; others cannot afford the support load.
        sa.Column("block_rooted_devices", sa.Boolean(), nullable=False, server_default="false"),

        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_by", sa.String(150), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_geofence_policy_singleton"),
    )
    op.execute("INSERT INTO geofence_policy (id) VALUES (1) ON CONFLICT (id) DO NOTHING")

    # The punch path resolves an employee's warehouses on every clock-in, so the
    # assignment lookup is the hottest query in the system.
    mh.create_index(
        "idx_zpa_personnel_active", "zone_personnel_assignments",
        ["personnel_id", "status"],
        postgresql_where=sa.text("unassigned_at IS NULL"),
    )


def downgrade():
    op.drop_index("idx_zpa_personnel_active", table_name="zone_personnel_assignments")
    op.drop_table("geofence_policy")
