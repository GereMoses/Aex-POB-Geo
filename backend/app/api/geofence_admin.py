"""
Geofence administration and the mobile-punch exception queue.

Two audiences. Administrators configure warehouse fences here — individually or
by bulk CSV import across hundreds of sites. Supervisors work the exception
queue: punches that were blocked, punches that were accepted but flagged, and
photos awaiting review.

The queue is the part HR actually cares about. A geofence that silently blocks
a clock-in solves nothing on its own — someone has to see that an employee has
tried to punch in from a residential address four mornings running.
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import get_current_user

from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geofence", tags=["Geofence Administration"])

# Selfies are served only from inside this root, never by a caller-supplied path.
SELFIE_ROOT = Path("/app/private/punch_selfies")

REVIEW_VERDICTS = {"MATCH", "MISMATCH"}


def _audit(db: Session, user, action: str, table: str,
           record_id: Optional[int] = None,
           old: Optional[dict] = None, new: Optional[dict] = None) -> None:
    """
    Record a geofence configuration change in the shared audit trail.

    These settings govern a fraud control: widening a fence, lowering the risk
    threshold or assigning somebody to a warehouse they do not work at would
    each let a bad punch through, and each is reversible in seconds. Without a
    trail the only thing visible afterwards is the final state, which is
    exactly what an insider would rely on.

    Never raises — an audit failure must not roll back the change the operator
    just made, but it is logged loudly so a silently broken trail is noticed.
    """
    try:
        db.execute(text("""
            INSERT INTO base_operationlog
                (user_id, action, table_name, record_id, old_values, new_values, created_at)
            VALUES (:uid, :action, :tbl, :rid, :old, :new, now())
        """), {
            "uid": getattr(user, "id", None),
            # action/table_name are varchar(50) — an over-long value fails the
            # whole insert and loses the audit row rather than truncating.
            "action": (action or "")[:50],
            "tbl": (table or "")[:50],
            "rid": record_id,
            "old": json.dumps(old, default=str) if old is not None else None,
            "new": json.dumps(new, default=str) if new is not None else None,
        })
    except Exception:
        logger.exception("Failed to write geofence audit entry (%s on %s)", action, table)


class FenceConfig(BaseModel):
    """Fence settings for one warehouse."""
    geofence_enabled: bool = True
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    radius_m: int = Field(default=200, ge=25, le=5000)
    polygon: Optional[list[list[float]]] = None
    gps_accuracy_max_m: int = Field(default=100, ge=10, le=1000)
    accuracy_buffer_cap_m: int = Field(default=50, ge=0, le=500)
    elevation_m: Optional[float] = None
    require_selfie: bool = False

    @field_validator("polygon")
    @classmethod
    def _validate_polygon(cls, v):
        if v is None:
            return v
        if len(v) < 3:
            raise ValueError("A polygon needs at least three points")
        for point in v:
            if len(point) != 2:
                raise ValueError("Each polygon point must be [latitude, longitude]")
            lat, lng = point
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise ValueError(f"Point out of range: {point}")
        return v


class ReviewDecision(BaseModel):
    verdict: str
    note: Optional[str] = None

    @field_validator("verdict")
    @classmethod
    def _validate_verdict(cls, v):
        if v.upper() not in REVIEW_VERDICTS:
            raise ValueError(f"verdict must be one of {sorted(REVIEW_VERDICTS)}")
        return v.upper()


@router.get("/sites")
def list_sites(
    configured_only: bool = Query(False, description="Only sites with a fence set up"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Warehouses and their fence configuration, for the admin map view."""
    rows = db.execute(text(f"""
        SELECT z.id, z.name, z.code, z.address, z.state,
               z.geofence_enabled, z.geofence_lat, z.geofence_lng,
               z.geofence_radius_m, z.geofence_polygon, z.gps_accuracy_max_m,
               z.accuracy_buffer_cap_m, z.elevation_m, z.require_selfie,
               z.mobile_terminal_sn,
               (SELECT COUNT(*) FROM zone_personnel_assignments zpa
                 WHERE zpa.zone_id = z.id AND zpa.status = 'ACTIVE'
                   AND zpa.unassigned_at IS NULL) AS assigned_staff
        FROM zones z
        WHERE z.is_active IS TRUE
          {"AND z.geofence_enabled IS TRUE" if configured_only else ""}
        ORDER BY z.name
    """)).fetchall()

    return {
        "success": True,
        "count": len(rows),
        "sites": [{
            "id": r.id, "name": r.name, "code": r.code,
            "address": r.address, "state": r.state,
            "geofence_enabled": r.geofence_enabled,
            "latitude": float(r.geofence_lat) if r.geofence_lat is not None else None,
            "longitude": float(r.geofence_lng) if r.geofence_lng is not None else None,
            "radius_m": r.geofence_radius_m,
            "polygon": r.geofence_polygon,
            "gps_accuracy_max_m": r.gps_accuracy_max_m,
            "accuracy_buffer_cap_m": r.accuracy_buffer_cap_m,
            "elevation_m": r.elevation_m,
            "require_selfie": r.require_selfie,
            "terminal_sn": r.mobile_terminal_sn,
            "assigned_staff": r.assigned_staff,
        } for r in rows],
    }


@router.put("/sites/{zone_id}")
def configure_site(
    zone_id: int,
    config: FenceConfig,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Configure one warehouse's fence.

    Enabling a fence without geometry would lock every assigned employee out of
    clocking in, so that combination is refused rather than saved.
    """
    if config.geofence_enabled and config.polygon is None and (
        config.latitude is None or config.longitude is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A fence needs either a centre point or a polygon before it can be enabled",
        )

    before = db.execute(text("""
        SELECT geofence_enabled, geofence_lat, geofence_lng, geofence_radius_m,
               gps_accuracy_max_m, accuracy_buffer_cap_m, elevation_m, require_selfie
        FROM zones WHERE id = :zid
    """), {"zid": zone_id}).fetchone()

    result = db.execute(text("""
        UPDATE zones SET
            geofence_enabled = :enabled,
            geofence_lat = :lat, geofence_lng = :lng,
            -- Mirrored into the legacy columns so the warehouse GPS map and
            -- anything else still reading them stays in step.
            -- CAST(...) rather than the :param::type shorthand: SQLAlchemy's
            -- bind-parameter parser mis-handles a cast applied directly to a
            -- named parameter and Postgres receives a stray colon, so the whole
            -- statement fails with a syntax error.
            latitude  = CASE WHEN :lat IS NULL THEN latitude
                        ELSE CAST(ROUND(CAST(:lat AS numeric), 7) AS text) END,
            longitude = CASE WHEN :lng IS NULL THEN longitude
                        ELSE CAST(ROUND(CAST(:lng AS numeric), 7) AS text) END,
            geofence_radius_m = :radius,
            geofence_polygon = CAST(:polygon AS jsonb),
            gps_accuracy_max_m = :accuracy_max,
            accuracy_buffer_cap_m = :buffer_cap,
            elevation_m = :elevation,
            require_selfie = :require_selfie,
            updated_at = now()
        WHERE id = :zone_id AND is_active IS TRUE
        RETURNING id, name, mobile_terminal_sn
    """), {
        "zone_id": zone_id,
        "enabled": config.geofence_enabled,
        "lat": config.latitude, "lng": config.longitude,
        "radius": config.radius_m,
        "polygon": json.dumps({"points": config.polygon}) if config.polygon else None,
        "accuracy_max": config.gps_accuracy_max_m,
        "buffer_cap": config.accuracy_buffer_cap_m,
        "elevation": config.elevation_m,
        "require_selfie": config.require_selfie,
    }).fetchone()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    # A site provisioned before the geofence migration may have no terminal yet.
    if not result.mobile_terminal_sn:
        db.execute(text(
            "UPDATE zones SET mobile_terminal_sn = 'MOB-' || LPAD(id::text, 6, '0') "
            "WHERE id = :zone_id"
        ), {"zone_id": zone_id})

    # The warehouse's virtual terminal must exist and point back at it. Live
    # occupancy is computed by joining punches to zones through
    # iclock_terminal.zone_id, so a terminal without one makes every punch at
    # this site invisible on the warehouse dashboard.
    db.execute(text("""
        INSERT INTO iclock_terminal (sn, alias, ip_address, state, zone_id)
        SELECT z.mobile_terminal_sn, LEFT(z.name, 50), '0.0.0.0', 1, z.id
        FROM zones z WHERE z.id = :zone_id AND z.mobile_terminal_sn IS NOT NULL
        ON CONFLICT (sn) DO UPDATE SET zone_id = EXCLUDED.zone_id
    """), {"zone_id": zone_id})

    _audit(db, current_user, "FENCE_UPDATE", "zones", zone_id,
           old=dict(before._mapping) if before else None,
           new=config.model_dump())
    db.commit()
    return {"success": True, "zone_id": result.id, "name": result.name}


@router.post("/sites/bulk-import")
async def bulk_import_sites(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Configure fences for many warehouses from a CSV.

    Expected columns: code, latitude, longitude, and optionally radius_m,
    elevation_m, require_selfie. Sites are matched on their existing zone code
    — this configures fences on warehouses that already exist, it does not
    create new ones.

    Rows are validated individually and reported per row: at 500+ sites, one
    malformed coordinate should not cost the operator the entire import.
    """
    raw = await file.read()
    try:
        text_body = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded CSV",
        )

    reader = csv.DictReader(io.StringIO(text_body))
    if not reader.fieldnames or "code" not in reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must have a 'code' column",
        )

    updated, errors = [], []
    for line_no, row in enumerate(reader, start=2):
        code = (row.get("code") or "").strip()
        if not code:
            errors.append({"line": line_no, "error": "Missing code"})
            continue
        try:
            lat = float(row["latitude"])
            lng = float(row["longitude"])
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise ValueError("Coordinates out of range")
            radius = int(row.get("radius_m") or 200)
            if not (25 <= radius <= 5000):
                raise ValueError("radius_m must be between 25 and 5000")
            elevation = float(row["elevation_m"]) if row.get("elevation_m") else None
            selfie = str(row.get("require_selfie", "")).strip().lower() in {"1", "true", "yes", "y"}
        except (KeyError, TypeError, ValueError) as e:
            errors.append({"line": line_no, "code": code, "error": str(e)})
            continue

        result = db.execute(text("""
            UPDATE zones SET
                geofence_enabled = TRUE,
                geofence_lat = :lat, geofence_lng = :lng,
                latitude  = CAST(ROUND(CAST(:lat AS numeric), 7) AS text),
                longitude = CAST(ROUND(CAST(:lng AS numeric), 7) AS text),
                geofence_radius_m = :radius,
                elevation_m = COALESCE(:elevation, elevation_m),
                require_selfie = :selfie,
                mobile_terminal_sn = COALESCE(
                    mobile_terminal_sn, 'MOB-' || LPAD(id::text, 6, '0')),
                updated_at = now()
            WHERE code = :code AND is_active IS TRUE
            RETURNING id
        """), {
            "code": code, "lat": lat, "lng": lng, "radius": radius,
            "elevation": elevation, "selfie": selfie,
        }).fetchone()

        if result:
            updated.append(code)
        else:
            errors.append({"line": line_no, "code": code, "error": "No active warehouse with this code"})

    _audit(db, current_user, "FENCE_BULK_IMPORT", "zones",
           new={"configured": updated, "failed": len(errors)})
    db.commit()
    return {
        "success": True,
        "configured": len(updated),
        "failed": len(errors),
        "errors": errors[:100],
    }


@router.get("/exceptions")
def list_exceptions(
    days: int = Query(7, ge=1, le=90),
    zone_id: Optional[int] = None,
    emp_code: Optional[str] = None,
    only: Optional[str] = Query(
        None, description="blocked | flagged | photo_review"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Mobile punch exceptions for supervisor review.

    Defaults to everything worth a human look — blocked attempts and accepted
    punches carrying risk — because the pattern across an employee's week is
    usually more telling than any single punch.
    """
    filters = ["e.server_time >= :since"]
    params: dict[str, Any] = {
        "since": datetime.now(timezone.utc) - timedelta(days=days),
        "limit": limit, "offset": offset,
    }
    if zone_id is not None:
        filters.append("e.zone_id = :zone_id")
        params["zone_id"] = zone_id
    if emp_code:
        filters.append("e.emp_code = :emp_code")
        params["emp_code"] = emp_code

    if only == "blocked":
        filters.append("e.decision = 'REJECTED'")
    elif only == "flagged":
        filters.append("e.decision = 'ACCEPTED_FLAGGED'")
    elif only == "photo_review":
        filters.append("e.face_verdict = 'PENDING_REVIEW'")
    elif only == "resolved":
        filters.append("e.resolved_at IS NOT NULL")
    else:
        # The working queue: things needing a human, minus anything already
        # dealt with. Without the resolved_at test a blocked punch reappeared
        # forever and the queue could never be worked down.
        filters.append("(e.decision <> 'ACCEPTED' OR e.face_verdict = 'PENDING_REVIEW')")
        filters.append("e.resolved_at IS NULL")

    where = " AND ".join(filters)
    rows = db.execute(text(f"""
        SELECT e.id, e.emp_code, e.zone_id, e.punch_state, e.decision, e.reason,
               e.risk_score, e.device_lat, e.device_lng, e.gps_accuracy_m,
               e.distance_m, e.server_time, e.clock_skew_seconds,
               e.gps_drift_m, e.altitude_delta_m, e.approach_teleport,
               e.platform, e.device_id, e.selfie_path, e.face_verdict, e.raw,
               e.resolved_at, e.resolved_by, e.resolution, e.resolution_note,
               z.name AS zone_name,
               p.first_name, p.last_name
        FROM mobile_punch_evidence e
        LEFT JOIN zones z     ON z.id = e.zone_id
        LEFT JOIN personnel p ON p.emp_code = e.emp_code
        WHERE {where}
        -- Most recent first. Ordering by risk instead buries today's activity
        -- under weeks of accumulated rejections, so somebody who has just
        -- punched cannot find their own record and concludes nothing was
        -- saved. Risk is shown on every row and remains sortable in the table.
        ORDER BY e.server_time DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    total = db.execute(text(
        f"SELECT COUNT(*) FROM mobile_punch_evidence e WHERE {where}"
    ), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar()

    return {
        "success": True,
        "total": total,
        "exceptions": [{
            "id": r.id,
            "emp_code": r.emp_code,
            "employee_name": " ".join(filter(None, [r.first_name, r.last_name])) or None,
            "zone_id": r.zone_id,
            "zone_name": r.zone_name,
            "direction": "IN" if r.punch_state == 0 else "OUT",
            "decision": r.decision,
            "reason": r.reason,
            "risk_score": r.risk_score,
            "flags": (r.raw or {}).get("flags", []),
            "latitude": float(r.device_lat) if r.device_lat is not None else None,
            "longitude": float(r.device_lng) if r.device_lng is not None else None,
            "gps_accuracy_m": r.gps_accuracy_m,
            "metres_outside_fence": r.distance_m,
            "gps_drift_m": r.gps_drift_m,
            "altitude_delta_m": r.altitude_delta_m,
            "approach_teleport": r.approach_teleport,
            "clock_skew_seconds": r.clock_skew_seconds,
            "platform": r.platform,
            "device_id": r.device_id,
            "has_photo": bool(r.selfie_path),
            "face_verdict": r.face_verdict,
            "occurred_at": r.server_time.isoformat() if r.server_time else None,
        } for r in rows],
    }


@router.get("/exceptions/summary")
def exceptions_summary(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Repeat offenders and problem sites.

    A single blocked punch is usually a weak GPS fix. The same employee blocked
    every morning is the thing HR asked to be told about, so the summary counts
    distinct days rather than raw attempts — one person retrying five times in
    a row is one day's problem, not five.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    offenders = db.execute(text("""
        SELECT e.emp_code,
               COUNT(*) AS attempts,
               COUNT(DISTINCT DATE(e.server_time)) AS days_affected,
               MAX(e.risk_score) AS peak_risk,
               MAX(e.server_time) AS last_seen,
               p.first_name, p.last_name
        FROM mobile_punch_evidence e
        LEFT JOIN personnel p ON p.emp_code = e.emp_code
        WHERE e.server_time >= :since AND e.decision = 'REJECTED'
        GROUP BY e.emp_code, p.first_name, p.last_name
        HAVING COUNT(DISTINCT DATE(e.server_time)) > 1
        ORDER BY days_affected DESC, attempts DESC
        LIMIT 50
    """), {"since": since}).fetchall()

    by_reason = db.execute(text("""
        SELECT reason, COUNT(*) AS count
        FROM mobile_punch_evidence
        WHERE server_time >= :since AND decision = 'REJECTED' AND reason IS NOT NULL
        GROUP BY reason ORDER BY count DESC
    """), {"since": since}).fetchall()

    # A site where almost everyone is being blocked is far more likely to have a
    # badly placed fence than a warehouse full of fraudsters.
    by_site = db.execute(text("""
        SELECT e.zone_id, z.name AS zone_name,
               COUNT(*) FILTER (WHERE e.decision = 'REJECTED') AS blocked,
               COUNT(*) AS total
        FROM mobile_punch_evidence e
        LEFT JOIN zones z ON z.id = e.zone_id
        WHERE e.server_time >= :since AND e.zone_id IS NOT NULL
        GROUP BY e.zone_id, z.name
        HAVING COUNT(*) FILTER (WHERE e.decision = 'REJECTED') > 0
        ORDER BY blocked DESC LIMIT 25
    """), {"since": since}).fetchall()

    return {
        "success": True,
        "period_days": days,
        "repeat_offenders": [{
            "emp_code": r.emp_code,
            "employee_name": " ".join(filter(None, [r.first_name, r.last_name])) or None,
            "attempts": r.attempts,
            "days_affected": r.days_affected,
            "peak_risk": r.peak_risk,
            "last_seen": r.last_seen.isoformat() if r.last_seen else None,
        } for r in offenders],
        "by_reason": [{"reason": r.reason, "count": r.count} for r in by_reason],
        "by_site": [{
            "zone_id": r.zone_id, "zone_name": r.zone_name,
            "blocked": r.blocked, "total_punches": r.total,
            "blocked_rate": round(r.blocked / r.total, 3) if r.total else 0,
        } for r in by_site],
    }


@router.get("/exceptions/{evidence_id}/photo")
def get_punch_photo(
    evidence_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Serve the selfie captured at a punch, for identity review."""
    row = db.execute(text(
        "SELECT selfie_path FROM mobile_punch_evidence WHERE id = :id"
    ), {"id": evidence_id}).fetchone()

    if not row or not row.selfie_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No photo for this punch")

    # The stored path comes from our own writer, but it is still resolved and
    # confined to the selfie root before being served — a path that escapes the
    # root means the row is corrupt, not that the file should be returned.
    path = Path(row.selfie_path).resolve()
    if not path.is_relative_to(SELFIE_ROOT.resolve()) or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo is no longer available")

    return FileResponse(path, media_type="image/jpeg")


class PhotoPurge(BaseModel):
    """Delete stored punch photos to reclaim disk."""
    older_than_days: int = Field(default=90, ge=1, le=3650)
    # A photo still awaiting a supervisor's verdict is the evidence that verdict
    # rests on, so it is kept unless deletion is explicitly forced.
    keep_pending_review: bool = True
    dry_run: bool = True


def _photo_stats(db: Session, older_than_days: Optional[int] = None,
                 keep_pending_review: bool = True):
    """Rows with a stored photo, optionally narrowed to the purge candidates."""
    filters = ["selfie_path IS NOT NULL"]
    params: dict = {}
    if older_than_days is not None:
        filters.append("server_time < now() - (:days || ' days')::interval")
        params["days"] = str(older_than_days)
    if keep_pending_review:
        filters.append("COALESCE(face_verdict, '') <> 'PENDING_REVIEW'")
    rows = db.execute(text(
        f"SELECT id, selfie_path FROM mobile_punch_evidence WHERE {' AND '.join(filters)}"
    ), params).fetchall()

    total = 0
    present = []
    for r in rows:
        try:
            fp = Path(r.selfie_path).resolve()
            if fp.is_relative_to(SELFIE_ROOT.resolve()) and fp.is_file():
                total += fp.stat().st_size
                present.append((r.id, fp))
        except (OSError, ValueError):
            continue
    return rows, present, total


class BulkExceptionAction(BaseModel):
    """Apply one action to a set of selected punch records."""
    ids: list[int] = Field(..., min_length=1, max_length=1000)
    note: Optional[str] = None


class BulkReview(BulkExceptionAction):
    verdict: str

    @field_validator("verdict")
    @classmethod
    def _v(cls, v):
        if v not in ("MATCH", "MISMATCH"):
            raise ValueError("verdict must be MATCH or MISMATCH")
        return v


class ResolveRequest(BaseModel):
    """Close an exception. Optionally in bulk."""
    ids: list[int] = Field(..., min_length=1, max_length=1000)
    resolution: str = Field(default="REVIEWED")
    note: Optional[str] = None

    @field_validator("resolution")
    @classmethod
    def _v(cls, v):
        allowed = {"REVIEWED", "GENUINE", "FALSE_POSITIVE", "ACTIONED", "IGNORED"}
        if v not in allowed:
            raise ValueError(f"resolution must be one of {sorted(allowed)}")
        return v


@router.post("/exceptions/resolve")
def resolve_exceptions(
    body: ResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Mark exceptions as dealt with so they leave the working queue.

    This records a decision ABOUT the exception; it does not touch the punch,
    its risk score or its decision — those are the evidence. FALSE_POSITIVE is
    the one worth using deliberately: a run of them at one warehouse is the
    signal that its fence radius is too tight.
    """
    rows = db.execute(text("""
        UPDATE mobile_punch_evidence
           SET resolved_at = now(), resolved_by = :by,
               resolution = :res, resolution_note = :note
         WHERE id = ANY(:ids) AND resolved_at IS NULL
        RETURNING id
    """), {"ids": body.ids, "res": body.resolution, "note": body.note,
           "by": getattr(current_user, "username", None)}).fetchall()
    _audit(db, current_user, "EXCEPTION_RESOLVE", "mobile_punch_evidence", None,
           new={"resolution": body.resolution, "count": len(rows)})
    db.commit()
    skipped = len(body.ids) - len(rows)
    return {"success": True, "resolved": len(rows), "skipped": skipped,
            "message": f"{len(rows)} exception(s) resolved."
                       + (f" {skipped} were already resolved." if skipped else "")}


@router.post("/exceptions/reopen")
def reopen_exceptions(
    body: ResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return resolved exceptions to the working queue."""
    rows = db.execute(text("""
        UPDATE mobile_punch_evidence
           SET resolved_at = NULL, resolved_by = NULL,
               resolution = NULL, resolution_note = NULL
         WHERE id = ANY(:ids) AND resolved_at IS NOT NULL
        RETURNING id
    """), {"ids": body.ids}).fetchall()
    _audit(db, current_user, "EXCEPTION_REOPEN", "mobile_punch_evidence", None,
           new={"count": len(rows)})
    db.commit()
    return {"success": True, "reopened": len(rows),
            "message": f"{len(rows)} exception(s) reopened."}


@router.post("/exceptions/bulk-review")
def bulk_review(
    body: BulkReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Record the same identity verdict against several punches at once.

    As with a single review this is a finding, not an eraser: the punches stay
    exactly as they are. Only rows still awaiting a decision are touched, so a
    careless bulk action cannot silently overwrite a verdict somebody already
    considered.
    """
    # Reviewer and note live inside raw, the same place a single review records
    # them — there are no dedicated columns for them on this table.
    review_blob = json.dumps({"review": {
        "by": getattr(current_user, "username", None) or str(getattr(current_user, "id", "unknown")),
        "at": datetime.now(timezone.utc).isoformat(),
        "note": body.note,
        "bulk": True,
    }})
    rows = db.execute(text("""
        UPDATE mobile_punch_evidence
           SET face_verdict = :verdict,
               raw = COALESCE(raw, '{}'::jsonb) || CAST(:review AS jsonb)
         WHERE id = ANY(:ids)
           AND face_verdict = 'PENDING_REVIEW'
        RETURNING id
    """), {"ids": body.ids, "verdict": body.verdict, "review": review_blob}).fetchall()

    _audit(db, current_user, "PUNCH_BULK_REVIEW", "mobile_punch_evidence", None,
           new={"verdict": body.verdict, "count": len(rows)})
    db.commit()
    skipped = len(body.ids) - len(rows)
    return {
        "success": True, "reviewed": len(rows), "skipped": skipped,
        "message": f"{len(rows)} punch(es) marked {body.verdict}."
                   + (f" {skipped} already had a verdict." if skipped else ""),
    }


@router.post("/exceptions/bulk-delete-photos")
def bulk_delete_photos(
    body: BulkExceptionAction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Remove the photos from the selected punches, keeping the punch records."""
    rows = db.execute(text(
        "SELECT id, selfie_path FROM mobile_punch_evidence "
        "WHERE id = ANY(:ids) AND selfie_path IS NOT NULL"
    ), {"ids": body.ids}).fetchall()

    deleted = freed = 0
    for r in rows:
        try:
            fp = Path(r.selfie_path).resolve()
            if fp.is_relative_to(SELFIE_ROOT.resolve()) and fp.is_file():
                freed += fp.stat().st_size
                fp.unlink()
                deleted += 1
        except (OSError, ValueError):
            logger.warning("Could not delete punch photo for evidence %s", r.id)

    if rows:
        db.execute(text(
            "UPDATE mobile_punch_evidence SET selfie_path = NULL WHERE id = ANY(:ids)"
        ), {"ids": [r.id for r in rows]})
    _audit(db, current_user, "PHOTO_BULK_DELETE", "mobile_punch_evidence", None,
           new={"count": deleted})
    db.commit()
    return {
        "success": True, "deleted": deleted,
        "freed_megabytes": round(freed / 1048576, 2),
        "message": f"{deleted} photo(s) deleted. The punch records are unchanged.",
    }


@router.post("/exceptions/bulk-delete")
def bulk_delete_exceptions(
    body: BulkExceptionAction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Delete the selected exception records.

    This removes the geofence evidence — where the punch was made, how it
    scored, what was flagged — and its photo. The ATTENDANCE punch in
    iclock_transaction is deliberately left alone: clearing a review queue must
    never quietly alter somebody's hours.

    Intended for clearing test data. On a live estate the evidence is what an
    attendance dispute is settled with, so it is audited in full.
    """
    rows = db.execute(text(
        "SELECT id, emp_code, selfie_path FROM mobile_punch_evidence WHERE id = ANY(:ids)"
    ), {"ids": body.ids}).fetchall()

    for r in rows:
        if not r.selfie_path:
            continue
        try:
            fp = Path(r.selfie_path).resolve()
            if fp.is_relative_to(SELFIE_ROOT.resolve()) and fp.is_file():
                fp.unlink()
        except (OSError, ValueError):
            pass

    db.execute(text("DELETE FROM mobile_punch_evidence WHERE id = ANY(:ids)"),
               {"ids": [r.id for r in rows]})
    _audit(db, current_user, "PUNCH_EVIDENCE_DELETE", "mobile_punch_evidence", None,
           old={"ids": [r.id for r in rows], "emp_codes": sorted({r.emp_code for r in rows})},
           new={"count": len(rows), "note": body.note})
    db.commit()
    logger.warning("%s deleted %s punch evidence record(s)",
                   getattr(current_user, "username", "?"), len(rows))
    return {
        "success": True, "deleted": len(rows),
        "message": f"{len(rows)} exception record(s) deleted. "
                   "Attendance punches were not changed.",
    }


@router.get("/photos/usage")
def photo_storage_usage(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """How much disk the punch photos are using, and how old they are."""
    all_rows, present, total = _photo_stats(db, None, keep_pending_review=False)
    oldest = db.execute(text(
        "SELECT MIN(server_time) AS oldest, MAX(server_time) AS newest "
        "FROM mobile_punch_evidence WHERE selfie_path IS NOT NULL"
    )).fetchone()
    pending = db.execute(text(
        "SELECT COUNT(*) FROM mobile_punch_evidence "
        "WHERE selfie_path IS NOT NULL AND face_verdict = 'PENDING_REVIEW'"
    )).scalar()

    return {
        "success": True,
        "photos_recorded": len(all_rows),
        "files_on_disk": len(present),
        "bytes": total,
        "megabytes": round(total / 1048576, 2),
        "pending_review": pending,
        "oldest": oldest.oldest.isoformat() if oldest and oldest.oldest else None,
        "newest": oldest.newest.isoformat() if oldest and oldest.newest else None,
    }


@router.post("/photos/purge")
def purge_photos(
    body: PhotoPurge,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Delete punch photos older than a cut-off.

    The evidence ROW is kept and only its selfie_path cleared — the punch, its
    risk score and its decision remain auditable; it is the image that goes.
    Deleting the row instead would erase the attendance trail along with the
    storage, which is the opposite of what a retention policy is for.

    Defaults to a dry run so the count can be seen before anything is removed.
    """
    rows, present, total = _photo_stats(db, body.older_than_days, body.keep_pending_review)

    if body.dry_run:
        return {
            "success": True, "dry_run": True,
            "would_delete": len(present),
            "would_free_megabytes": round(total / 1048576, 2),
            "older_than_days": body.older_than_days,
            "message": f"{len(present)} photo(s) would be deleted, freeing "
                       f"{round(total / 1048576, 2)} MB.",
        }

    deleted = 0
    freed = 0
    for evid, fp in present:
        try:
            size = fp.stat().st_size
            fp.unlink()
            freed += size
            deleted += 1
        except OSError:
            logger.warning("Could not delete punch photo %s", fp)
    if rows:
        db.execute(text(
            "UPDATE mobile_punch_evidence SET selfie_path = NULL WHERE id = ANY(:ids)"
        ), {"ids": [r.id for r in rows]})

    _audit(db, current_user, "PHOTO_PURGE", "mobile_punch_evidence", None,
           new={"deleted": deleted, "older_than_days": body.older_than_days,
                "megabytes": round(freed / 1048576, 2)})
    db.commit()
    logger.info("Purged %s punch photo(s), freed %.1f MB", deleted, freed / 1048576)

    return {
        "success": True, "dry_run": False,
        "deleted": deleted,
        "freed_megabytes": round(freed / 1048576, 2),
        "message": f"{deleted} photo(s) deleted, {round(freed / 1048576, 2)} MB freed.",
    }


@router.delete("/exceptions/{evidence_id}/photo")
def delete_punch_photo(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete one punch photo, keeping the punch record itself."""
    row = db.execute(text(
        "SELECT selfie_path FROM mobile_punch_evidence WHERE id = :id"
    ), {"id": evidence_id}).fetchone()
    if not row or not row.selfie_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No photo for this punch")

    try:
        fp = Path(row.selfie_path).resolve()
        if fp.is_relative_to(SELFIE_ROOT.resolve()) and fp.is_file():
            fp.unlink()
    except (OSError, ValueError):
        logger.warning("Could not delete punch photo for evidence %s", evidence_id)

    db.execute(text(
        "UPDATE mobile_punch_evidence SET selfie_path = NULL WHERE id = :id"
    ), {"id": evidence_id})
    _audit(db, current_user, "PHOTO_DELETE", "mobile_punch_evidence", evidence_id)
    db.commit()
    return {"success": True, "message": "Photo deleted. The punch record is unchanged."}


@router.post("/exceptions/{evidence_id}/review")
def review_punch(
    evidence_id: int,
    decision: ReviewDecision,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Record a supervisor's verdict on a punch photo.

    The verdict is evidence, not an eraser: marking a photo MISMATCH records
    that the wrong person clocked in but leaves the transaction in place. The
    punch is corrected through the existing manual-adjustment workflow, which
    already carries its own approval trail.
    """
    row = db.execute(text("""
        UPDATE mobile_punch_evidence
        SET face_verdict = :verdict,
            raw = COALESCE(raw, '{}'::jsonb) || CAST(:review AS jsonb)
        WHERE id = :id
        RETURNING id, emp_code, transaction_id
    """), {
        "id": evidence_id,
        "verdict": decision.verdict,
        "review": json.dumps({"review": {
            "by": getattr(current_user, "username", None) or str(getattr(current_user, "id", "unknown")),
            "at": datetime.now(timezone.utc).isoformat(),
            "note": decision.note,
        }}),
    }).fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Punch not found")

    _audit(db, current_user, "PUNCH_PHOTO_REVIEW", "mobile_punch_evidence", evidence_id,
           new={"verdict": decision.verdict, "emp_code": row.emp_code})
    db.commit()
    return {
        "success": True,
        "id": row.id,
        "emp_code": row.emp_code,
        "transaction_id": row.transaction_id,
        "verdict": decision.verdict,
    }


# ── Staff assignment ────────────────────────────────────────────────────────
# An employee can only clock in at a warehouse they are assigned to. Without an
# assignment every punch is refused with NO_ASSIGNMENT, so this is the first
# thing that has to be set up after the fences themselves.

class StaffAssignment(BaseModel):
    personnel_ids: list[int] = Field(default_factory=list)
    emp_codes: list[str] = Field(default_factory=list)
    is_primary: bool = True

    @field_validator("emp_codes")
    @classmethod
    def _at_least_one(cls, v, info):
        if not v and not info.data.get("personnel_ids"):
            raise ValueError("Provide at least one personnel_id or emp_code")
        return v


@router.get("/sites/{zone_id}/staff")
def list_site_staff(
    zone_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Employees currently assigned to this warehouse."""
    rows = db.execute(text("""
        SELECT p.id, p.emp_code, p.first_name, p.last_name,
               zpa.is_primary_zone, zpa.assigned_at,
               d.name AS department
        FROM zone_personnel_assignments zpa
        JOIN personnel p       ON p.id = zpa.personnel_id
        LEFT JOIN departments d ON d.id = p.department_id
        WHERE zpa.zone_id = :zid
          AND zpa.status = 'ACTIVE'
          AND zpa.unassigned_at IS NULL
        ORDER BY p.first_name, p.last_name
    """), {"zid": zone_id}).fetchall()

    return {
        "success": True,
        "count": len(rows),
        "staff": [{
            "personnel_id": r.id,
            "emp_code": r.emp_code,
            "name": " ".join(filter(None, [r.first_name, r.last_name])) or r.emp_code,
            "department": r.department,
            "is_primary": r.is_primary_zone,
            "assigned_at": r.assigned_at.isoformat() if r.assigned_at else None,
        } for r in rows],
    }


@router.post("/sites/{zone_id}/staff")
def assign_staff(
    zone_id: int,
    body: StaffAssignment,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Assign employees to a warehouse.

    Re-assigning somebody already on the site is a no-op rather than an error —
    an operator re-running a bulk assignment should not have to care which of
    the names were already there.
    """
    zone = db.execute(text(
        "SELECT id, name FROM zones WHERE id = :zid AND is_active IS TRUE"
    ), {"zid": zone_id}).fetchone()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    resolved, missing = [], []
    if body.personnel_ids:
        rows = db.execute(text(
            "SELECT id FROM personnel WHERE id = ANY(:ids) AND is_active IS TRUE"
        ), {"ids": body.personnel_ids}).fetchall()
        found = {r.id for r in rows}
        resolved += list(found)
        missing += [str(i) for i in body.personnel_ids if i not in found]
    if body.emp_codes:
        rows = db.execute(text(
            "SELECT id, emp_code FROM personnel WHERE emp_code = ANY(:codes) AND is_active IS TRUE"
        ), {"codes": body.emp_codes}).fetchall()
        found = {r.emp_code for r in rows}
        resolved += [r.id for r in rows]
        missing += [c for c in body.emp_codes if c not in found]

    assigned, already = [], []
    for pid in set(resolved):
        existing = db.execute(text("""
            SELECT id FROM zone_personnel_assignments
            WHERE zone_id = :zid AND personnel_id = :pid
              AND status = 'ACTIVE' AND unassigned_at IS NULL
        """), {"zid": zone_id, "pid": pid}).fetchone()
        if existing:
            already.append(pid)
            continue
        db.execute(text("""
            INSERT INTO zone_personnel_assignments
                (zone_id, personnel_id, status, is_primary_zone, assigned_at, created_at)
            VALUES (:zid, :pid, 'ACTIVE', :primary, now(), now())
        """), {"zid": zone_id, "pid": pid, "primary": body.is_primary})
        assigned.append(pid)

    if assigned:
        _audit(db, current_user, "STAFF_ASSIGN", "zone_personnel_assignments", zone_id,
               new={"warehouse": zone.name, "personnel_ids": assigned})
    db.commit()
    return {
        "success": True,
        "warehouse": zone.name,
        "assigned": len(assigned),
        "already_assigned": len(already),
        "not_found": missing,
    }


@router.delete("/sites/{zone_id}/staff/{personnel_id}")
def unassign_staff(
    zone_id: int,
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Remove an employee from a warehouse.

    The row is closed with unassigned_at rather than deleted, so that a punch
    refused last month can still be explained by the assignment that was in
    force at the time.
    """
    row = db.execute(text("""
        UPDATE zone_personnel_assignments
        SET unassigned_at = now(), status = 'INACTIVE', updated_at = now()
        WHERE zone_id = :zid AND personnel_id = :pid
          AND status = 'ACTIVE' AND unassigned_at IS NULL
        RETURNING id
    """), {"zid": zone_id, "pid": personnel_id}).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That employee is not currently assigned to this warehouse",
        )
    _audit(db, current_user, "STAFF_UNASSIGN", "zone_personnel_assignments", zone_id,
           old={"personnel_id": personnel_id, "zone_id": zone_id})
    db.commit()
    return {"success": True, "unassigned": personnel_id}


@router.get("/staff/unassigned")
def unassigned_staff(
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Active employees with no warehouse.

    These are the people who will be turned away at the gate, so surfacing them
    is what stops a rollout failing quietly on its first morning.
    """
    params: dict[str, Any] = {"limit": limit}
    where = ""
    if search:
        where = ("AND (p.emp_code ILIKE :q OR p.first_name ILIKE :q "
                 "OR p.last_name ILIKE :q)")
        params["q"] = f"%{search}%"

    rows = db.execute(text(f"""
        SELECT p.id, p.emp_code, p.first_name, p.last_name, d.name AS department
        FROM personnel p
        LEFT JOIN departments d ON d.id = p.department_id
        WHERE p.is_active IS TRUE
          {where}
          AND NOT EXISTS (
              SELECT 1 FROM zone_personnel_assignments zpa
              WHERE zpa.personnel_id = p.id
                AND zpa.status = 'ACTIVE' AND zpa.unassigned_at IS NULL
          )
        ORDER BY p.first_name, p.last_name
        LIMIT :limit
    """), params).fetchall()

    return {
        "success": True,
        "count": len(rows),
        "staff": [{
            "personnel_id": r.id,
            "emp_code": r.emp_code,
            "name": " ".join(filter(None, [r.first_name, r.last_name])) or r.emp_code,
            "department": r.department,
        } for r in rows],
    }


@router.post("/staff/bulk-assign")
async def bulk_assign_staff(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Assign many employees from a CSV of `emp_code,site_code`.

    At Continental's scale nobody is going to click through several thousand
    assignments. Rows are validated individually and reported per line, so one
    bad employee number does not cost the operator the whole file.
    """
    raw = await file.read()
    try:
        body = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be UTF-8 encoded CSV")

    reader = csv.DictReader(io.StringIO(body))
    if not reader.fieldnames or "emp_code" not in reader.fieldnames or "site_code" not in reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="CSV needs 'emp_code' and 'site_code' columns")

    assigned, already, errors = 0, 0, []
    for line_no, row in enumerate(reader, start=2):
        emp_code = (row.get("emp_code") or "").strip()
        site_code = (row.get("site_code") or "").strip()
        if not emp_code or not site_code:
            errors.append({"line": line_no, "error": "Missing emp_code or site_code"})
            continue

        found = db.execute(text("""
            SELECT p.id AS pid, z.id AS zid
            FROM personnel p
            CROSS JOIN zones z
            WHERE p.emp_code = :emp AND p.is_active IS TRUE
              AND z.code = :site AND z.is_active IS TRUE
        """), {"emp": emp_code, "site": site_code}).fetchone()
        if not found:
            errors.append({"line": line_no, "emp_code": emp_code, "site_code": site_code,
                           "error": "No active employee and warehouse with those codes"})
            continue

        exists = db.execute(text("""
            SELECT 1 FROM zone_personnel_assignments
            WHERE zone_id = :zid AND personnel_id = :pid
              AND status = 'ACTIVE' AND unassigned_at IS NULL
        """), {"zid": found.zid, "pid": found.pid}).fetchone()
        if exists:
            already += 1
            continue

        db.execute(text("""
            INSERT INTO zone_personnel_assignments
                (zone_id, personnel_id, status, is_primary_zone, assigned_at, created_at)
            VALUES (:zid, :pid, 'ACTIVE', TRUE, now(), now())
        """), {"zid": found.zid, "pid": found.pid})
        assigned += 1

    _audit(db, current_user, "STAFF_BULK_ASSIGN", "zone_personnel_assignments",
           new={"assigned": assigned, "already_assigned": already, "failed": len(errors)})
    db.commit()
    return {
        "success": True,
        "assigned": assigned,
        "already_assigned": already,
        "failed": len(errors),
        "errors": errors[:100],
    }


# ── Clock-in rules ──────────────────────────────────────────────────────────
# The global anti-spoofing policy. Per-warehouse settings (radius, accuracy,
# photo) live on the site itself; these are the rules that apply everywhere.

class ClockInRules(BaseModel):
    impossible_travel_kmh: float = Field(ge=100, le=5000)
    approach_max_ground_speed_kmh: float = Field(ge=30, le=1000)
    reject_risk_threshold: int = Field(ge=10, le=200)
    min_expected_drift_m: float = Field(ge=0, le=20)
    min_drift_samples: int = Field(ge=2, le=20)
    altitude_tolerance_m: float = Field(ge=20, le=2000)
    clock_skew_flag_seconds: float = Field(ge=30, le=86400)
    risk_rooted_device: int = Field(ge=0, le=100)
    risk_static_gps: int = Field(ge=0, le=100)
    risk_implausible_altitude: int = Field(ge=0, le=100)
    risk_zero_altitude: int = Field(ge=0, le=100)
    risk_implausible_accuracy: int = Field(ge=0, le=100)
    risk_clock_skew: int = Field(ge=0, le=100)
    risk_accuracy_buffer: int = Field(ge=0, le=100)
    block_rooted_devices: bool = False

    # Mock location. Blocking is the correct default; turning it off is for
    # testing on an emulator, whose position always comes from a mock provider.
    block_mock_location: bool = True
    risk_mock_location: int = Field(default=50, ge=0, le=100)

    # Browser clients cannot run device attestation, so they are governed
    # separately: permitted or not, and carrying their own standing risk.
    allow_pwa_punches: bool = True
    risk_pwa_client: int = Field(default=0, ge=0, le=100)

    # Automated face matching against the enrolled reference.
    face_matching_enabled: bool = True
    face_match_threshold: float = Field(default=0.40, ge=0.05, le=0.95)
    block_on_face_mismatch: bool = False
    late_reason_after_minutes: int = Field(default=15, ge=0, le=480)


@router.get("/policy")
def get_clock_in_rules(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Current global clock-in rules."""
    row = db.execute(text("SELECT * FROM geofence_policy WHERE id = 1")).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Clock-in rules have not been initialised")
    data = {k: v for k, v in row._mapping.items() if k != "id"}
    if data.get("updated_at"):
        data["updated_at"] = data["updated_at"].isoformat()
    return {"success": True, "rules": data}


@router.put("/policy")
def update_clock_in_rules(
    rules: ClockInRules,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update the global clock-in rules.

    Takes effect within the policy cache's lifetime; the cache is invalidated
    here so a supervisor who has just loosened a threshold to get a stranded
    shift through the gate sees it apply immediately.
    """
    fields = rules.model_dump()
    before = db.execute(text("SELECT * FROM geofence_policy WHERE id = 1")).fetchone()
    assignments = ", ".join(f"{k} = :{k}" for k in fields)
    params = {**fields,
              "by": getattr(current_user, "username", None) or str(getattr(current_user, "id", "unknown"))}
    db.execute(text(f"""
        UPDATE geofence_policy
        SET {assignments}, updated_at = now(), updated_by = :by
        WHERE id = 1
    """), params)
    _audit(db, current_user, "RULES_UPDATE", "geofence_policy", 1,
           old={k: v for k, v in (dict(before._mapping) if before else {}).items()
                if k in fields},
           new=fields)
    db.commit()

    from ..services.geofence_service import invalidate_policy_cache
    invalidate_policy_cache()

    return {"success": True, "rules": fields}


# ── Live occupancy ──────────────────────────────────────────────────────────

@router.get("/occupancy")
def live_occupancy(
    zone_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Who is currently clocked in, per warehouse.

    Derived from the punches themselves rather than a running counter. The old
    occupancy column was incremented by the reader ingest and is now never
    written, so anything reading it shows zero forever; computing from the last
    punch per employee cannot drift out of step with the attendance record.

    An employee is "on site" if their most recent punch today was a clock-in.
    Scoped to today so somebody who forgot to clock out on Friday is not still
    counted as present on Monday.
    """
    params: dict[str, Any] = {"tz": settings.TIMEZONE}
    where = ""
    if zone_id is not None:
        where = "AND z.id = :zid"
        params["zid"] = zone_id

    rows = db.execute(text(f"""
        WITH last_punch AS (
            SELECT DISTINCT ON (t.emp_code)
                   t.emp_code, t.punch_state, t.punch_time, t.terminal_sn
            FROM iclock_transaction t
            WHERE t.punch_time >= (date_trunc('day', now() AT TIME ZONE :tz) AT TIME ZONE :tz)
            ORDER BY t.emp_code, t.punch_time DESC
        )
        SELECT z.id, z.name, z.code,
               COUNT(lp.emp_code) FILTER (WHERE lp.punch_state = 0) AS on_site,
               (SELECT COUNT(*) FROM zone_personnel_assignments zpa
                 WHERE zpa.zone_id = z.id AND zpa.status = 'ACTIVE'
                   AND zpa.unassigned_at IS NULL) AS assigned
        FROM zones z
        LEFT JOIN last_punch lp ON lp.terminal_sn = z.mobile_terminal_sn
        WHERE z.is_active IS TRUE AND z.geofence_enabled IS TRUE {where}
        GROUP BY z.id, z.name, z.code
        ORDER BY z.name
    """), params).fetchall()

    sites = [{
        "zone_id": r.id,
        "name": r.name,
        "code": r.code,
        "on_site": r.on_site,
        "assigned": r.assigned,
        "attendance_rate": round(r.on_site / r.assigned, 3) if r.assigned else None,
    } for r in rows]

    return {
        "success": True,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "total_on_site": sum(s["on_site"] for s in sites),
        "total_assigned": sum(s["assigned"] for s in sites),
        "sites": sites,
    }


@router.get("/occupancy/{zone_id}/staff")
def who_is_on_site(
    zone_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """The named individuals currently clocked in at one warehouse."""
    rows = db.execute(text("""
        WITH last_punch AS (
            SELECT DISTINCT ON (t.emp_code)
                   t.emp_code, t.punch_state, t.punch_time
            FROM iclock_transaction t
            JOIN zones z ON z.mobile_terminal_sn = t.terminal_sn
            WHERE z.id = :zid AND t.punch_time >= (date_trunc('day', now() AT TIME ZONE :tz) AT TIME ZONE :tz)
            ORDER BY t.emp_code, t.punch_time DESC
        )
        SELECT lp.emp_code, lp.punch_time, p.first_name, p.last_name
        FROM last_punch lp
        LEFT JOIN personnel p ON p.emp_code = lp.emp_code
        WHERE lp.punch_state = 0
        ORDER BY lp.punch_time DESC
    """), {"zid": zone_id, "tz": settings.TIMEZONE}).fetchall()

    return {
        "success": True,
        "count": len(rows),
        "staff": [{
            "emp_code": r.emp_code,
            "name": " ".join(filter(None, [r.first_name, r.last_name])) or r.emp_code,
            "clocked_in_at": r.punch_time.isoformat() if r.punch_time else None,
        } for r in rows],
    }


# ── Face enrolment ──────────────────────────────────────────────────────────
# A reference face per employee, so the punch selfie can be compared
# automatically instead of queued for a supervisor.

class FaceEnrolment(BaseModel):
    photo_base64: str


@router.get("/face/status")
def face_status(_=Depends(get_current_user)):
    """Whether automated matching is running, and how many staff are enrolled."""
    from ..services import face_service
    return {
        "success": True,
        "available": face_service.is_available(),
        "reason": face_service.unavailable_reason(),
        "model": face_service.MODEL_NAME,
    }


@router.get("/face/enrolment")
def list_face_enrolment(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Who has a reference face on file, and who does not."""
    rows = db.execute(text("""
        SELECT p.id, p.emp_code, p.first_name, p.last_name,
               fe.enrolled_at, fe.model_name, fe.enrolled_source
        FROM personnel p
        LEFT JOIN personnel_face_enrollment fe ON fe.personnel_id = p.id
        WHERE p.is_active IS TRUE
        ORDER BY (fe.id IS NULL) DESC, p.first_name
    """)).fetchall()
    return {
        "success": True,
        "enrolled": sum(1 for r in rows if r.enrolled_at),
        "total": len(rows),
        "staff": [{
            "personnel_id": r.id,
            "emp_code": r.emp_code,
            "name": " ".join(filter(None, [r.first_name, r.last_name])) or r.emp_code,
            "enrolled": bool(r.enrolled_at),
            "enrolled_at": r.enrolled_at.isoformat() if r.enrolled_at else None,
            "model": r.model_name,
            # ADMIN vs SELF: a self-registered face has not been vouched for by
            # anyone, so the console flags it for confirmation.
            "source": r.enrolled_source,
        } for r in rows],
    }


@router.post("/face/enrolment/{personnel_id}")
def enrol_face(
    personnel_id: int,
    body: FaceEnrolment,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Store an employee's reference face.

    The embedding is what is kept for matching — a 512-float vector that cannot
    be turned back into a photograph. The source image is retained separately on
    the private volume so a supervisor can compare by eye if a match is
    disputed, and is never served except through the authenticated review path.
    """
    from ..services import face_service

    if not face_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Face matching is not installed on this server "
                   f"({face_service.unavailable_reason()}). "
                   f"Install requirements-face.txt to enable it.",
        )

    person = db.execute(text(
        "SELECT id, emp_code FROM personnel WHERE id = :pid AND is_active IS TRUE"
    ), {"pid": personnel_id}).fetchone()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    vec = face_service.embed(body.photo_base64)
    if vec is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face could be found in that photo. Use a clear, "
                   "front-facing picture with the face filling most of the frame.",
        )

    path = _store_reference_photo(person.emp_code, body.photo_base64)
    db.execute(text("""
        INSERT INTO personnel_face_enrollment
            (personnel_id, embedding, model_name, dimensions,
             reference_photo_path, enrolled_at, enrolled_by, enrolled_source, updated_at)
        VALUES (:pid, :emb, :model, :dims, :path, now(), :by, 'ADMIN', now())
        ON CONFLICT (personnel_id) DO UPDATE SET
            embedding = EXCLUDED.embedding,
            model_name = EXCLUDED.model_name,
            dimensions = EXCLUDED.dimensions,
            reference_photo_path = EXCLUDED.reference_photo_path,
            enrolled_by = EXCLUDED.enrolled_by,
            enrolled_source = 'ADMIN',
            updated_at = now()
    """), {
        "pid": personnel_id,
        "emb": face_service.to_bytes(vec),
        "model": face_service.MODEL_NAME,
        "dims": int(vec.shape[0]),
        "path": path,
        "by": getattr(current_user, "username", None),
    })
    _audit(db, current_user, "FACE_ENROL", "personnel_face_enrollment", personnel_id,
           new={"emp_code": person.emp_code, "model": face_service.MODEL_NAME})
    db.commit()
    return {"success": True, "personnel_id": personnel_id, "emp_code": person.emp_code}


@router.delete("/face/enrolment/{personnel_id}")
def remove_face_enrolment(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an employee's reference face; their punches revert to manual review."""
    row = db.execute(text(
        "DELETE FROM personnel_face_enrollment WHERE personnel_id = :pid RETURNING id"
    ), {"pid": personnel_id}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled")
    _audit(db, current_user, "FACE_ENROL_REMOVE", "personnel_face_enrollment", personnel_id)
    db.commit()
    return {"success": True, "personnel_id": personnel_id}


def _store_reference_photo(emp_code: str, encoded: str) -> str:
    """Keep the enrolment photo beside the punch selfies, off any public path."""
    import base64 as _b64
    import secrets as _secrets

    root = Path("/app/private/face_reference") / emp_code
    root.mkdir(parents=True, exist_ok=True)
    payload = encoded.split(",", 1)[-1] if encoded.startswith("data:") else encoded
    path = root / f"{_secrets.token_hex(8)}.jpg"
    path.write_bytes(_b64.b64decode(payload))
    return str(path)
