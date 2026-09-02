# Geofenced Mobile Attendance — Deployment Runbook

Location-enforced clock-in for warehouse staff, using GPS only. Employees punch
from their own phones over mobile data; a punch is refused unless the device is
inside the fence of a warehouse the employee is assigned to.

Server-side enforcement lives in `app/services/geofence_service.py`. The mobile
app performs the same check locally so it can grey out the button, but that is
advisory — a patched app can always claim it passed.

---

## 1. What was added

| Component | Path |
|---|---|
| Fence config + evidence schema | `backend/alembic/versions/0004_geofence.py` |
| Anti-spoofing fields, selfie capture | `backend/alembic/versions/0005_spoof_detection.py` |
| Validation engine | `backend/app/services/geofence_service.py` |
| Punch endpoints | `backend/app/api/mobile.py` |
| Admin + exception queue API | `backend/app/api/geofence_admin.py` |
| Admin UI | `frontend-react/src/pages/Geofence/` |

Route permissions were added to `backend/app/core/rbac.py`, and a private volume
for punch selfies to both compose files.

---

## 2. Deployment steps

### 2.1 Apply the migrations

Alembic is the single source of truth for the schema, and three paths now run it,
so a normal deploy needs no manual step:

| Path | When it runs |
|---|---|
| `docker/db-init.sh` | every `docker compose up` |
| backend startup (`_upgrade_schema_to_head`) | every boot, including `restart` |
| manual | `docker compose -f docker-compose.prod.yml exec backend alembic upgrade head` |

The backend takes a Postgres advisory lock before upgrading, so replicas cannot
race, and a failed upgrade is logged loudly rather than blocking start-up.

> **This used to be broken.** `db-init.sh` previously loaded
> `database/init/complete_schema.sql` and never ran Alembic, so a FRESH deploy
> came up with none of the geofence schema — no `mobile_punch_evidence`, no
> `geofence_policy`, no `personnel_face_enrollment`, and no fence columns on
> `zones`. Only databases that had been migrated by hand had them. If you are
> bringing up an environment from an older bundle, check
> `select version_num from alembic_version;` before trusting it.

Both starting points are tested end to end:

* **Empty database** → `alembic upgrade head` builds all 240 tables and every
  revision through `0015`.
* **Legacy database** built by the old `complete_schema.sql` path → db-init
  stamps `0001_complete_schema`, then applies `0002`–`0015` on top.

Revisions `0003`–`0011` were made idempotent (see
`backend/alembic/migration_helpers.py`) precisely so the legacy path does not
abort on objects the dump already created.

The migrations are reversible; `alembic downgrade 0003_position_headcount`
was tested and round-trips cleanly.

`0004` backfills `geofence_lat` / `geofence_lng` from the existing varchar
`latitude` / `longitude` columns wherever they parse as valid coordinates, so
sites already carrying coordinates do not need re-entering. It also assigns
every zone a virtual terminal (`MOB-000123`).

### 2.2 Recreate the backend container

The new `punch_selfies_data` volume is mounted at `/app/private`. A plain
restart will not pick it up:

```bash
docker compose -f docker-compose.prod.yml up -d --force-recreate backend
```

**This volume matters.** Punch selfies are biometric data. They must not live
under `/app/uploads` or `/app/media`, because `nginx/conf.d/pob.conf` serves
both of those directly from disk with no authentication — anything placed there
is readable by anyone who can guess a path. Selfies are served only through
`GET /api/v1/geofence/exceptions/{id}/photo`, which enforces permissions.

### 2.3 Reload nginx

`nginx/conf.d/pob.conf` gained a `return 404` for `/uploads/punch_selfies/` as
defence in depth. Config syntax was validated with `nginx -t`.

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### 2.4 Configure fences

Either through the UI at **Operations → Geofenced Attendance → Warehouse
fences**, or by CSV bulk import:

```csv
code,latitude,longitude,radius_m,elevation_m,require_selfie
IKJ,6.6018,3.3515,250,39,true
APP,6.4433,3.3620,300,8,true
```

`code` must match an existing active zone — import configures fences on
warehouses that already exist, it does not create them. Rows are validated
individually and failures reported per line, so one bad coordinate does not
cost the whole import.

---

## 3. Prerequisites that are easy to miss

### 3.1 Employee accounts must resolve to an employee record

`get_current_user` returns a `SimpleUser` that carries no `emp_code`. The punch
endpoints resolve it in this order:

1. `emp_code` attribute, if ever present
2. `personnel.user_id` → the authenticated user's id
3. `auth_user.username` matched against `personnel.emp_code`

In the current schema `personnel.user_id` references the `users` table, which is
empty and unused — authentication runs on `auth_user`. **So in practice route 3
is the working path: provision each employee's login with their employee code as
the username.** This matches what `app/api/self_service.py` already assumes.

An account that resolves to nothing gets a clear 403 rather than a 500.

### 3.2 Staff must be assigned to a warehouse

A fence has no effect until employees are linked through
`zone_personnel_assignments` with `status = 'ACTIVE'` and `unassigned_at IS
NULL`. Unassigned staff are refused with `NO_ASSIGNMENT`.

### 3.3 Permissions

Geofence reads require `attendance.view`; writes require `attendance.change`.
Reads expose staff locations and their photos, so they are deliberately not open
to any authenticated account — warehouse employees hold valid tokens too.

---

## 4. Mobile client contract

`POST /api/v1/mobile/check-in` and `/check-out`:

```jsonc
{
  "location": {
    "latitude": 6.60195, "longitude": 3.35162,
    "accuracy": 22,          // metres; drives the fence allowance
    "altitude": 40,          // see the warning below
    "timestamp": "..."       // evidence only; never used for attendance
  },
  "samples": [ /* 3+ fixes over a few seconds — drift check */ ],
  "approach_path": [ /* fixes from the minutes before the punch */ ],
  "device": {
    "device_id": "...", "platform": "android", "app_version": "1.0.0",
    "is_mock_location": false, "is_rooted": false, "is_emulator": false,
    "attestation_verdict": "PASS"   // Play Integrity / App Attest
  },
  "selfie_base64": "..."     // required where the site sets require_selfie
}
```

`200` on success. `422` with `{reason, message}` when the punch is refused —
show `message` to the employee verbatim. `400` for a malformed photo.

### Three client rules that matter

1. **Send `null` for altitude when it is unavailable — never `0`.** An exact
   zero is treated as a spoofing sentinel, because real GNSS essentially never
   reports 0.000. Handsets that use zero to mean "unknown" would generate false
   flags.
2. **Send at least 3 samples**, spaced far enough apart that the OS returns
   fresh fixes rather than a cached one. Fewer than 3 disables the drift check.
3. **The punch time is the server's.** Device time is stored only as tamper
   evidence, so a manipulated handset clock cannot shift a shift boundary.

`GET /api/v1/mobile/my-sites` returns the employee's fences so the app can show
status before a punch is attempted.

A generated OpenAPI spec for these endpoints is available from
`/api/v1/openapi.json` in non-production environments.

---

## 5. How a punch is judged

**Refused outright:** mock location, emulator, failed attestation, outside every
assigned fence, GPS accuracy worse than the site allows, a teleport inside the
approach trail, missing photo where required, no warehouse assignment.

**Risk-scored, refused at 80+:**

| Signal | Score |
|---|---|
| No GPS drift across samples | 50 |
| Altitude mismatch vs site elevation | 40 |
| Rooted device | 40 |
| Impossibly precise fix (≤1m) | 30 |
| Altitude reported as exactly zero | 30 |
| Device clock off by >5 min | 20 |
| Admitted only by the accuracy allowance | 10 |

No single soft signal blocks a punch — a rooted phone alone scores 40 and passes
flagged. Rooted *plus* static GPS reaches 90 and is refused. Individually these
all have innocent explanations; stacked they do not, and judging on the total is
what keeps false positives off the gate at 6am.

### Tuning

Per site: `geofence_radius_m`, `gps_accuracy_max_m`, `accuracy_buffer_cap_m`,
`elevation_m`, `require_selfie`.

Global constants in `geofence_service.py`: `IMPOSSIBLE_TRAVEL_KMH` (900, punch
to punch — generous enough for a flight), `APPROACH_MAX_GROUND_SPEED_KMH` (200,
within the approach trail — ground movement only), `REJECT_RISK_THRESHOLD` (80).

**The accuracy allowance is capped deliberately.** The fence widens by the
reported GPS accuracy so someone at the gate with a weak fix is not turned away,
but the widening stops at `accuracy_buffer_cap_m`. Without a cap, a spoofed
device would report `accuracy: 5000` and inflate the fence over half the city.

---

## 6. Operating it

**Exceptions** lists blocked and flagged punches with the signals that fired.
**Summary** separates deliberate tampering (mock location, static GPS, teleport)
from operational problems (weak signal, unconfigured fence) — they are coloured
differently because handing HR a single "blocked punches" number has them
investigating people whose real offence is standing under a steel roof.

A site blocking most of its punches almost always has a badly placed or
undersized fence, not a workforce problem. Check the boundary before escalating.

Repeat offenders are counted by **distinct days**, not raw attempts: someone
retrying five times one morning is one day's problem, not five.

Marking a photo `MISMATCH` records the finding and the reviewer's name. It does
**not** remove the punch — correction goes through the existing manual
adjustment workflow, which carries its own approval trail.

---

## 7. Field guidance for Continental

GPS needs sky. Under a steel warehouse roof, fixes degrade badly and cell-tower
fallback is accurate only to hundreds of metres. **Staff should clock in at the
gate or in the yard, not deep inside the building.** Put this in the SOP; it
will prevent most `LOW_GPS_ACCURACY` rejections.

Large distribution centres commonly need 200–400m radii. Cover the yard and
gate, not just the building footprint.

---

## 8. Known gaps

- **Face matching is not automated.** The selfie pipeline is complete —
  mandatory capture, private storage, review queue, verdict recording — but
  `face_verdict` lands on `PENDING_REVIEW` for a human. Automating it needs a
  face-recognition dependency (InsightFace + ONNX Runtime, or DeepFace +
  TensorFlow), several hundred MB on the image, plus model-hosting and accuracy
  threshold decisions. `face_score` exists in the schema, unused, ready for it.
- **Offline punching is not supported, by design.** Requiring connectivity is
  what allows server-side timestamping. Offline queues accept a device-supplied
  time, which is the easiest attendance fraud there is.
- **No mobile app yet.** This is the server and admin side only.

## 9. Staff assignment, rules and governance

### Assigning staff

**Geofenced Attendance → Staff.** An employee can only clock in at a warehouse
they are assigned to; with no assignment every punch is refused with
`NO_ASSIGNMENT`. The tab shows who is assigned to each site, a picker to add
more, and a **"Not assigned anywhere"** panel listing the people who would be
turned away at the gate — check that it is empty before go-live.

Bulk assignment takes a CSV of `emp_code,site_code`. Staff may hold several
warehouses; the nearest fence wins at punch time.

Unassignment closes the row with `unassigned_at` rather than deleting it, so a
punch refused last month can still be explained by the assignment in force at
the time.

### Clock-in rules

**Geofenced Attendance → Clock-in rules** holds the global anti-spoofing
policy: the refusal threshold, the seven signal weights, the hard limits
(approach speed, punch-to-punch travel, whether rooted phones are refused
outright) and detector sensitivity. Per-warehouse settings — radius, accuracy
limits, elevation, photo required — stay on the site itself.

Changes apply to the next punch. If `geofence_policy` is ever unreadable the
service falls back to built-in defaults rather than failing the punch: an
administrative table being absent must never stop a warehouse clocking in.

### Audit trail

Every change to a fence, an assignment, the rules or a photo verdict is written
to `base_operationlog` with before-and-after values, readable at
`/api/v1/audit/logs`. These settings govern a fraud control and are reversible
in seconds — without a trail the only thing visible afterwards is the final
state, which is exactly what an insider would rely on.

Recorded actions: `FENCE_UPDATE`, `FENCE_BULK_IMPORT`, `STAFF_ASSIGN`,
`STAFF_UNASSIGN`, `STAFF_BULK_ASSIGN`, `RULES_UPDATE`, `PUNCH_PHOTO_REVIEW`.

### Alerts

Three generators run with the existing notification checks:

- **Suspected tampering** — a mock location, emulator, teleport or composite-risk
  rejection in the last hour. Deduplicated per person per hour.
- **Repeated failed clock-ins** — blocked on three or more separate days in a
  week. Counted by distinct days, so one bad morning of retries never trips it.
- **Staff who cannot clock in** — any active employee with no warehouse.

Only deliberate-tampering reasons raise the critical alert. Paging a supervisor
every time somebody's signal drops under a steel roof is how alerting gets muted.

### Live occupancy

`/api/v1/geofence/occupancy` reports who is on site per warehouse, derived from
today's punches rather than a stored counter — the old occupancy column was
incremented by the reader ingest and is now never written. Scoped to today, so
a missed clock-out on Friday is not still counted on Monday.

## 10. Face verification (optional)

Automated matching of the punch selfie against an enrolled reference face.
Kept out of the base image because the runtime and models add roughly 300MB —
a deployment happy with supervisor review should not carry that.

### Enabling it

```bash
docker build -f backend/Dockerfile.face -t pob_backend_face:latest backend/
```

Models download to `/root/.insightface` on first use (about 280MB). Mount a
pre-seeded volume there for an air-gapped install or to avoid the first-run
delay. `GET /api/v1/geofence/face/status` reports whether it is running.

**This upgrades pandas.** insightface requires numpy 2.x, whose ABI breaks the
pandas 2.1.4 in the base image — the application will not boot. The face
requirements therefore move pandas to 2.2.3+. Regression-test reporting and
payroll after enabling.

### Enrolling

`POST /api/v1/geofence/face/enrolment/{personnel_id}` with a clear,
front-facing photo. What is stored for matching is a 512-float embedding, not
the image: an embedding cannot be inverted back into a face, so a database
leak does not hand anyone a biometric photo library. The source photo is kept
on the private volume so a supervisor can compare by eye if a match is
disputed.

### Thresholds

Measured against the reference model: different people scored at most **0.23**,
the same person at least **0.93**. The default threshold of **0.40** sits well
clear of both. Real captures vary more than a test set, so it is tunable in
**Clock-in rules**.

`block_on_face_mismatch` is **off** by default. Until every employee has a good
enrolment photo, a mismatch is more often a poor reference than an impostor,
and turning somebody away at the gate is the worse error. With it off, a
mismatch is recorded and flagged; with it on, the punch is refused.

Every outcome other than MATCH or MISMATCH — model unavailable, employee not
enrolled, no face found in the photo — leaves the punch for a supervisor.
Those are reasons to ask a human, never to accuse one.

## 11. The employee clock PWA

A browser client at `/clock/`, installable to a home screen. Built for pilots
and testing: it needs no app store, no Xcode and no Android Studio.

**It is not a substitute for the native app.** A browser cannot run Play
Integrity, App Attest, mock-location detection or root checks — those APIs are
native-only. A PWA can report a position and a photo and nothing else.

So the server is told which client it is talking to. `client_type` is recorded
on every punch, and two policy settings govern browser punches:

- `allow_pwa_punches` — off refuses them outright
- `risk_pwa_client` — a standing risk score for punches with no device
  attestation behind them

Run a pilot with the risk at 0. Once the native app is distributed, raising it
(or switching the flag off) closes the browser as a spoofing route without
another deployment.

For production, the recommended path is wrapping this same page in Capacitor:
the native integrity modules already written in Kotlin and Swift attach to it,
without maintaining a second UI codebase.

## 12. Modules removed for this deployment

The Marconi offshore modules and everything driving physical readers were
stripped out, since Continental has no hardware at any warehouse:

**Offshore/POB** — mustering, emergency, POB status, transport manifest,
journey management, MTD, visitor management, meeting rooms.

**Hardware** — ZKTeco/ADMS protocol, device management, discovery, enrolment,
access control, device-side biometrics, BioTime device sync.

About 108,000 lines. What stayed: attendance, shifts, schedules, overtime,
leave, payroll, personnel, HR, zones/geofence, auth, RBAC, reports, settings.

Two things moved rather than being deleted, because they were misfiled:

- **The Celery app** was defined inside `mustering_celery_tasks.py`. It now
  lives in `app/services/celery_app.py` with the SMS, email and WhatsApp
  notification tasks; the drill and siren tasks went with mustering.
- **The punch SSE subscriber registry** was inside the ZKTeco live-capture
  loop. It now lives in `app/services/punch_stream.py`, and mobile punches
  publish to it — so the supervisor's live view works with no device code
  behind it.

`EmailSetup.jsx` was sitting under `pages/Emergency/` despite being the
Settings email tab; it moved to `pages/Settings/`.

### Schema left in place

Dropping columns needs a migration and they are inert, so these were left:
`zones.evac_point`, `evac_gps`, `reader_sn`, `map_x`, `map_y`,
`map_connections`, `device_count`, `zkteco_sync_enabled`. The mustering and
device tables also remain in the database. Removing them is a follow-up.

### Pre-existing bugs found and fixed along the way

- `audit.py` queried `created_time`, `operation_type`, `module`, `object_id` and
  `description` — none of which exist on `base_operationlog`. The whole audit
  module returned 500. Realigned with the real columns.
- Five notification generators (`_check_offline_devices`, `_check_pob_summary`,
  `_check_pob_zone_discrepancy`, `_check_mtd_certifications`,
  `_check_access_denied`) belonged to removed modules and were dropped.

### Pre-existing issues found while testing (not introduced here, not fixed)

- `GET /api/v1/openapi.json` returns 500 in non-production environments. Four
  routes under `/api/v1/report/` (`/templates`, `/schedules`, `/builder/meta/`,
  `/builder/preview`) contain a Pydantic model with a `Callable` field, which
  cannot be expressed as JSON Schema. This breaks `/docs` for the whole app.
- `personnel.user_id` references `users`, which is empty; authentication uses
  `auth_user`. The two are not linked.
