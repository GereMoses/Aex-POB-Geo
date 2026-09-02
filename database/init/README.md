# database/init

## `incremental.sql` — still applied

Idempotent legacy DDL that lives outside the Alembic chain (access-control and
visitor-module tables and columns). Applied by `docker/db-init.sh` on every
`docker compose up`, and by the backend at startup when its checksum changes.

## `complete_schema.sql` — **no longer applied**

A `pg_dump --schema-only` of an older validated system. It is kept for reference
only and is **not** mounted into any container.

It was the schema source until it caused a real defect: `db-init.sh` loaded this
dump and never ran Alembic, so a fresh deploy came up with none of the geofence
work — `mobile_punch_evidence`, `geofence_policy`, `personnel_face_enrollment`
and the fence columns on `zones` were all missing, because they only exist in
migrations `0004`–`0015`.

Alembic is now the single source of truth. The equivalent baseline lives at
`backend/alembic/versions/schema_ddl.sql` and is applied by revision
`0001_complete_schema`.

**If you change the schema, add an Alembic revision.** Editing either dump has
no effect on any environment.
