"""Client trust level, late-reason capture and request IP on punches

A browser cannot run Play Integrity, App Attest, mock-location detection or
root checks — those APIs are native-only. A PWA is therefore a strictly
lower-assurance client, and if the server treats it identically to the native
app then the PWA becomes the easiest route for anyone wanting to spoof a
punch. The server has to know which client it is talking to.

Revision ID: 0009_client_trust_and_reasons
Revises: 0008_repair_missing_tables
Create Date: 2026-08-29
"""
from alembic import op
import migration_helpers as mh
import sqlalchemy as sa

revision = "0009_client_trust_and_reasons"
down_revision = "0008_repair_missing_tables"
branch_labels = None
depends_on = None


def upgrade():
    mh.add_column("mobile_punch_evidence",
                  sa.Column("client_type", sa.String(16), nullable=True))
    # The address the punch actually arrived from. A punch routed through a VPN
    # or a hosting provider is worth a second look — spoofing tools are
    # routinely paired with one.
    mh.add_column("mobile_punch_evidence",
                  sa.Column("client_ip", sa.String(64), nullable=True))
    # Why somebody was late, captured at the moment they clock in rather than
    # reconstructed by a supervisor days later.
    mh.add_column("mobile_punch_evidence",
                  sa.Column("late_reason", sa.String(500), nullable=True))

    mh.add_column("geofence_policy",
                  sa.Column("allow_pwa_punches", sa.Boolean(), nullable=False,
                            server_default="true"))
    # Browser punches carry no device attestation, so they start with a standing
    # risk score. Set to 0 during a pilot; raise it once the native app is out.
    mh.add_column("geofence_policy",
                  sa.Column("risk_pwa_client", sa.Integer(), nullable=False,
                            server_default="0"))
    # Minutes past shift start after which the app asks for a reason.
    mh.add_column("geofence_policy",
                  sa.Column("late_reason_after_minutes", sa.Integer(), nullable=False,
                            server_default="15"))

    mh.create_index("idx_mpe_client_type", "mobile_punch_evidence", ["client_type"])


def downgrade():
    op.drop_index("idx_mpe_client_type", table_name="mobile_punch_evidence")
    for col in ("late_reason_after_minutes", "risk_pwa_client", "allow_pwa_punches"):
        op.drop_column("geofence_policy", col)
    for col in ("late_reason", "client_ip", "client_type"):
        op.drop_column("mobile_punch_evidence", col)
