"""Reconnect warehouses to their coordinates and their virtual terminals

Zones carry two coordinate pairs: the original varchar latitude/longitude, and
the numeric geofence_lat/geofence_lng added for the geofence engine. Configuring
a fence only ever wrote the second pair, so everything still reading the first —
the warehouse GPS map among them — saw empty values and plotted nothing.

Backfills from the fence coordinates, which are the ones an administrator has
actually placed on a map.

Separately, each warehouse owns a virtual terminal (MOB-nnnnnn) that mobile
punches are written against, but those terminal rows were created without a
zone_id. Live occupancy is computed by joining punches to zones through exactly
that column, so every warehouse reported zero people on site no matter how many
had clocked in.

Revision ID: 0012_sync_zone_coordinates
Revises: 0011_mock_location_policy
Create Date: 2026-08-30
"""
from alembic import op

revision = "0012_sync_zone_coordinates"
down_revision = "0011_mock_location_policy"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE zones
        SET latitude  = ROUND(geofence_lat, 7)::text,
            longitude = ROUND(geofence_lng, 7)::text
        WHERE geofence_lat IS NOT NULL
          AND geofence_lng IS NOT NULL
          AND (latitude IS NULL OR latitude = '' OR longitude IS NULL OR longitude = '')
    """)


    # Point each virtual terminal at the warehouse that owns it, so occupancy
    # queries joining through iclock_terminal.zone_id find the punches.
    op.execute("""
        UPDATE iclock_terminal t
        SET zone_id = z.id
        FROM zones z
        WHERE z.mobile_terminal_sn = t.sn
          AND (t.zone_id IS NULL OR t.zone_id <> z.id)
    """)


def downgrade():
    # Nothing to undo: the values written here are the correct coordinates for
    # these sites, and clearing them would restore a bug rather than a state.
    pass
