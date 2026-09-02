#!/bin/bash
# Database initializer — runs once on first deploy (and harmlessly on redeploys).
# Runs inside the BACKEND image, which has psql, python and the app code.
#   1. Waits for PostgreSQL.
#   2. Brings the schema to head with Alembic (the single source of truth).
#   3. Applies the idempotent incremental SQL for legacy objects Alembic omits.
#   4. Seeds the global admin user so the system is immediately loginable.
set -e

HOST="${DATABASE_HOST:-postgres}"
PORT="${DATABASE_PORT:-5432}"

echo "Waiting for PostgreSQL at ${HOST}:${PORT}..."
until pg_isready -h "$HOST" -p "$PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" -q; do
  sleep 2
done
echo "PostgreSQL is ready."

export PGPASSWORD="$DATABASE_PASSWORD"
PSQL="psql -h $HOST -p $PORT -U $DATABASE_USER -d $DATABASE_NAME"

# ── 1. Schema — Alembic is authoritative ─────────────────────────────────────
# This previously loaded database/init/complete_schema.sql and never ran Alembic,
# so a FRESH deploy shipped without anything added by a migration — including the
# entire geofence feature set (mobile_punch_evidence, geofence_policy,
# personnel_face_enrollment and the fence columns on zones). Alembic's 0001
# baseline builds the same schema that dump did, and every revision after it is
# then applied, so one path produces a complete database.
SCHEMA_PRESENT="$($PSQL -tAc "SELECT to_regclass('public.auth_user')" 2>/dev/null | tr -d '[:space:]')"
ALEMBIC_AT="$($PSQL -tAc "SELECT version_num FROM alembic_version LIMIT 1" 2>/dev/null | tr -d '[:space:]')"

cd /app

if [ "$SCHEMA_PRESENT" = "auth_user" ] && [ -z "$ALEMBIC_AT" ]; then
  # Database predates Alembic (built by the old complete_schema.sql path).
  # Stamp the baseline so only the revisions AFTER it are applied — replaying
  # 0001 over a populated database would fail on existing constraints.
  echo "Existing pre-Alembic database detected — stamping baseline..."
  alembic stamp 0001_complete_schema
  echo "  ✓ Stamped 0001_complete_schema"
fi

echo "Applying database migrations..."
alembic upgrade head
echo "  ✓ Schema at head ($(alembic current 2>/dev/null | tail -1))"

# ── 1b. Incremental SQL (idempotent — runs on fresh AND existing DBs) ────────
# Legacy objects that live outside the Alembic chain (access-control and
# visitor-module tables and columns). Every statement is guarded, so this is a
# no-op once applied. Optional file, so an older bundle without it still boots.
if [ -f /migrations/incremental.sql ]; then
  echo "Applying incremental migrations..."
  $PSQL -v ON_ERROR_STOP=1 -f /migrations/incremental.sql
  echo "  ✓ Incremental migrations applied"
fi

# ── 2. Seed initial data (idempotent — creates global admin only if missing) ──
echo "Seeding initial data..."
python /app/seed_initial.py

echo "Database initialization complete."
