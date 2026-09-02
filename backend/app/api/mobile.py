"""
Mobile API Endpoints
API endpoints for mobile application access
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import base64
import binascii
import logging
import secrets
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..core.dependencies import get_current_user
from sqlalchemy import text
from ..services.punch_stream import publish_punch
from ..services.geofence_service import (
    DeviceContext,
    LocationSample,
    validate_punch,
    record_evidence,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["mobile"])

class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    timestamp: datetime

class LocationSampleIn(BaseModel):
    """One fix from the burst the app captures while the punch screen is open."""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: Optional[datetime] = None

class DeviceIntegrity(BaseModel):
    """
    Self-reported device integrity signals.

    Reported by the app, so treated as untrusted input: a positive signal is
    actionable (nothing benign sets a mock-location flag), but their absence
    proves nothing. `attestation_verdict` is the exception — it originates from
    Play Integrity / App Attest and is the only field here a patched app
    cannot simply omit its way past, which is why sites that require hard
    assurance should enforce its presence.
    """
    device_id: Optional[str] = None
    platform: Optional[str] = None
    app_version: Optional[str] = None
    is_mock_location: Optional[bool] = None
    is_rooted: Optional[bool] = None
    is_emulator: Optional[bool] = None
    attestation_verdict: Optional[str] = None

class PunchRequest(BaseModel):
    location: LocationData
    device: Optional[DeviceIntegrity] = None

    # A short burst of fixes taken over a few seconds before the punch. Feeds
    # the drift check — a real handset jitters, a spoofed one does not. Three
    # or more are needed before the signal counts for anything.
    samples: list[LocationSampleIn] = Field(default_factory=list)

    # Fixes from the minutes leading up to the punch, so the server can confirm
    # the employee travelled to the site rather than appearing at it.
    approach_path: list[LocationSampleIn] = Field(default_factory=list)

    # Base64 JPEG captured at the moment of punch. Required at sites configured
    # with require_selfie; ignored elsewhere.
    selfie_base64: Optional[str] = None

    # Which client this came from. Defaults to NATIVE so an older build keeps
    # working; the PWA sends "PWA" explicitly and is scored accordingly.
    client_type: str = "NATIVE"

    # Offered by the employee when they clock in late.
    late_reason: Optional[str] = None

class SelfEnrolRequest(BaseModel):
    """One-off reference photo submitted by the employee themselves."""
    photo_base64: str


class EmergencyAlert(BaseModel):
    alert_type: str
    location: LocationData
    message: Optional[str] = None
    severity: Optional[str] = "medium"

# Punch selfies are biometric data and must never be reachable except through
# the reviewing endpoint, which checks permissions. They deliberately do NOT
# live under /app/uploads or /app/media: nginx serves both of those straight
# from disk with no authentication (see nginx/conf.d/pob.conf), so anything
# placed there is world-readable to anyone who can guess a path.
SELFIE_ROOT = Path("/app/private/punch_selfies")

# A punch selfie is a small front-camera JPEG. Anything materially larger is
# either a misconfigured client or an attempt to fill the volume.
MAX_SELFIE_BYTES = 2 * 1024 * 1024

# Anything smaller than this is not a photograph of a person — an empty canvas
# encodes to a few hundred bytes.
MIN_SELFIE_BYTES = 1024

def _client_ip(request: Optional[Request]) -> Optional[str]:
    """
    The address the punch arrived from.

    Recorded as evidence, not used as a control: on mobile data this is the
    carrier's address, not the warehouse's, so it cannot prove location. It is
    still worth keeping — a punch arriving from a hosting provider or a VPN
    exit node is worth a supervisor's attention, because spoofing tools are
    routinely paired with one.
    """
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return request.client.host[:64] if request.client else None


def _resolve_emp_code(current_user, db: Session) -> str:
    """
    Map the authenticated account to the employee record it clocks in against.

    get_current_user yields a SimpleUser, not a dict, and it carries no
    emp_code — so the link has to be resolved here. personnel.user_id is the
    real relationship; the username fallback matches the convention already
    used in self_service.py for installations where accounts were provisioned
    with the employee code as the username.
    """
    direct = getattr(current_user, "emp_code", None)
    if direct:
        return direct

    user_id = getattr(current_user, "id", None)
    if user_id is not None:
        row = db.execute(text(
            "SELECT emp_code FROM personnel WHERE user_id = :uid AND is_active IS TRUE"
        ), {"uid": user_id}).fetchone()
        if row and row.emp_code:
            return row.emp_code

    username = getattr(current_user, "username", None)
    if username:
        # Case-insensitive on purpose: POST /settings/users lowercases every
        # username it stores, while emp_code is uppercase (CL001). An exact
        # match meant no staff account created through the admin UI could ever
        # clock in — it resolved to nothing and returned 403.
        row = db.execute(text(
            "SELECT emp_code FROM personnel "
            "WHERE UPPER(emp_code) = UPPER(:u) AND is_active IS TRUE"
        ), {"u": username}).fetchone()
        if row:
            return row.emp_code

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This account is not linked to an employee record, so it cannot clock in.",
    )

def _verify_face(db: Session, emp_code: str, selfie_b64: str, result) -> None:
    """
    Compare the punch selfie against the employee's enrolled face.

    Mutates the result in place so the verdict and score land on the evidence
    row alongside everything else about the punch. Anything other than a clean
    decision leaves the punch for a supervisor: an unavailable model, an
    unenrolled employee or a photo with no detectable face are all reasons to
    ask a human, never to accuse one.
    """
    from ..services import face_service
    from ..services.geofence_service import load_policy

    policy = load_policy(db)
    if not policy.face_matching_enabled:
        return

    row = db.execute(text("""
        SELECT fe.embedding
        FROM personnel_face_enrollment fe
        JOIN personnel p ON p.id = fe.personnel_id
        WHERE p.emp_code = :emp
    """), {"emp": emp_code}).fetchone()

    try:
        cmp = face_service.verify(
            selfie_b64, row.embedding if row else None, policy.face_match_threshold)
    except Exception:
        logger.exception("Face verification failed for %s — leaving for review", emp_code)
        return

    result.face_score = cmp.score
    if cmp.verdict == face_service.FaceResult.MATCH:
        result.face_verdict = "MATCH"
    elif cmp.verdict == face_service.FaceResult.MISMATCH:
        result.face_verdict = "MISMATCH"
        # Refusing on a mismatch is opt-in. Until an estate has good enrolment
        # photos, a mismatch is more often a poor reference than an impostor,
        # and stranding somebody at the gate on that is the worse error.
        if policy.block_on_face_mismatch:
            result.decision = "REJECTED"
            result.reason = "FACE_MISMATCH"
            result.message = ("The photo does not match your record. "
                              "Contact your supervisor.")
    else:
        result.face_verdict = "PENDING_REVIEW"


def _store_selfie(emp_code: str, encoded: str, server_time: datetime) -> str:
    """
    Decode and persist a punch selfie, returning its stored path.

    The image is written before the transaction is committed but is never the
    reason a punch fails: a storage error raises, the punch rolls back, and the
    employee is asked to try again rather than being silently clocked in
    without the photo the site requires.
    """
    payload = encoded.split(",", 1)[-1] if encoded.startswith("data:") else encoded
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selfie image is not valid base64",
        )
    # A truncated or blank capture must not be stored. It would sit on the
    # punch as an unreadable file, leaving a review that can never resolve and
    # a face check that always reports "no face".
    if len(raw) < MIN_SELFIE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The photo did not come through. Please take it again.",
        )
    if len(raw) > MAX_SELFIE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Selfie image is too large",
        )

    directory = SELFIE_ROOT / emp_code / server_time.strftime("%Y-%m-%d")
    directory.mkdir(parents=True, exist_ok=True)
    # A random suffix on top of the timestamp: should the directory ever be
    # exposed by a misconfigured deployment, filenames still cannot be
    # enumerated by walking timestamps.
    path = directory / f"{server_time.strftime('%H%M%S')}-{secrets.token_hex(8)}.jpg"
    path.write_bytes(raw)
    return str(path)

def _check_punch_sequence(db: Session, emp_code: str, punch_state: int,
                          server_time: datetime) -> Optional[dict]:
    """
    Guard against a repeated punch and an out-of-order one.

    Returns a detail dict to refuse with, or None to proceed.

    Both rules are policy-driven. Duplicate suppression catches the double-tap
    and the retry after a slow response — without it three clock-ins 1.3s apart
    were all recorded. Order enforcement stops a clock-out with no clock-in,
    which paired to (None, out_time) and computed as zero minutes worked, so an
    employee whose clock-in was refused for GPS accuracy silently lost the day.
    """
    from ..services.geofence_service import load_policy

    policy = load_policy(db)
    last = db.execute(text("""
        SELECT punch_state, punch_time
        FROM iclock_transaction
        WHERE UPPER(emp_code) = UPPER(:emp)
        ORDER BY punch_time DESC
        LIMIT 1
    """), {"emp": emp_code}).fetchone()
    if not last:
        # First punch ever. Only a clock-out is nonsensical here.
        if punch_state != 0 and policy.enforce_punch_order:
            return {"success": False, "reason": "NOT_CLOCKED_IN",
                    "message": "You have not clocked in yet."}
        return None

    window = policy.duplicate_punch_seconds or 0
    if window > 0 and last.punch_state == punch_state:
        gap = (server_time - last.punch_time).total_seconds()
        if 0 <= gap < window:
            action = "clocked in" if punch_state == 0 else "clocked out"
            return {"success": False, "reason": "DUPLICATE_PUNCH",
                    "message": f"You already {action} a moment ago."}

    if policy.enforce_punch_order and last.punch_state == punch_state:
        if punch_state == 0:
            return {"success": False, "reason": "ALREADY_CLOCKED_IN",
                    "message": "You are already clocked in. Clock out first."}
        return {"success": False, "reason": "NOT_CLOCKED_IN",
                "message": "You are not clocked in."}
    return None


def _record_punch(
    punch_state: int,
    payload: PunchRequest,
    current_user,
    db: Session,
    request: Optional[Request] = None,
):
    """
    Validate a mobile punch against the employee's warehouse geofence and, if
    it passes, write it to iclock_transaction.

    Punches are written to iclock_transaction — not checkinout — because that
    is the table the attendance engine reads (shift_management.py treats
    checkinout only as a fallback). Each warehouse owns a virtual terminal, so
    a phone punch is indistinguishable downstream from a physical reader's and
    every existing timesheet, overtime and payroll path works unchanged.

    The stored punch_time is server time. Device time is kept in the evidence
    row for tamper detection but never drives attendance, so a manipulated
    handset clock cannot move a shift boundary.
    """
    emp_code = _resolve_emp_code(current_user, db)

    server_time = datetime.now(timezone.utc)
    integrity = payload.device or DeviceIntegrity()

    def to_samples(items):
        return [LocationSample(
            latitude=i.latitude, longitude=i.longitude,
            accuracy_m=i.accuracy, timestamp=i.timestamp,
        ) for i in items]

    device = DeviceContext(
        latitude=payload.location.latitude,
        longitude=payload.location.longitude,
        gps_accuracy_m=payload.location.accuracy,
        altitude_m=payload.location.altitude,
        device_time=payload.location.timestamp,
        samples=to_samples(payload.samples),
        approach_path=to_samples(payload.approach_path),
        selfie_provided=bool(payload.selfie_base64),
        device_id=integrity.device_id,
        platform=integrity.platform,
        app_version=integrity.app_version,
        is_mock_location=integrity.is_mock_location,
        is_rooted=integrity.is_rooted,
        is_emulator=integrity.is_emulator,
        attestation_verdict=integrity.attestation_verdict,
        client_type=(payload.client_type or "NATIVE").upper(),
        client_ip=_client_ip(request),
        late_reason=(payload.late_reason or None),
    )

    try:
        # Reject a repeat of the same punch, and a punch that does not follow
        # from the employee's last one, BEFORE validating location — neither is
        # a geofence question and both should cost nothing.
        dup = _check_punch_sequence(db, emp_code, punch_state, server_time)
        if dup:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dup)

        result = validate_punch(db, emp_code, device, server_time=server_time)

        # Only accepted punches keep their photo. Storing selfies for rejected
        # attempts would accumulate images of employees who never clocked in —
        # more biometric data retained, for no investigative gain that the
        # evidence row does not already provide.
        selfie_path = None
        if result.allowed and payload.selfie_base64:
            selfie_path = _store_selfie(emp_code, payload.selfie_base64, server_time)
            # May flip the decision to REJECTED. No early return here: the
            # guards below already skip the transaction insert, and the punch
            # still has to reach the evidence trail — a refusal on a face
            # mismatch is the single most important thing to record.
            _verify_face(db, emp_code, payload.selfie_base64, result)

        transaction_id = None
        if result.allowed:
            row = db.execute(text("""
                INSERT INTO iclock_transaction (
                    emp_code, punch_time, punch_state, verify_type,
                    terminal_sn, area_alias, upload_time
                ) VALUES (
                    :emp_code, :punch_time, :punch_state, 200,
                    :terminal_sn, :area_alias, :upload_time
                )
                RETURNING id
            """), {
                'emp_code': emp_code,
                'punch_time': server_time,
                'punch_state': punch_state,
                'terminal_sn': result.terminal_sn,
                'area_alias': (result.zone_name or '')[:50],
                'upload_time': server_time,
            }).fetchone()
            transaction_id = row[0]

        # Rejected attempts are recorded too — a run of blocked clock-ins from
        # a residential address is precisely the signal HR is asking for.
        record_evidence(
            db, emp_code=emp_code, punch_state=punch_state, device=device,
            result=result, transaction_id=transaction_id, server_time=server_time,
            selfie_path=selfie_path,
        )
        db.commit()

        # Feed the supervisor's live view. After commit and never before: a
        # dashboard must not show a punch that a failed transaction rolled back.
        if result.allowed:
            publish_punch({
                "type": "punch",
                "emp_code": emp_code,
                "punch_state": punch_state,
                "punch_time": server_time.isoformat(),
                "terminal_sn": result.terminal_sn,
                "zone_id": result.zone_id,
                "zone_name": result.zone_name,
                "source": "MOBILE",
                "flagged": result.decision == "ACCEPTED_FLAGGED",
            })
    except HTTPException:
        db.rollback()
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record punch: {str(e)}"
        )

    if not result.allowed:
        # 422 rather than 403: the request was authenticated and well-formed,
        # it simply did not satisfy the location rule. Keeps genuine auth
        # failures distinguishable in logs and on the client.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'success': False,
                'reason': result.reason,
                'message': result.message,
            },
        )

    action = 'Clock-in' if punch_state == 0 else 'Clock-out'
    return {
        'success': True,
        'message': f"{action} confirmed at {result.zone_name}",
        'transaction_id': transaction_id,
        'zone': {'id': result.zone_id, 'name': result.zone_name},
        'timestamp': server_time.isoformat(),
        'flagged': result.decision == 'ACCEPTED_FLAGGED',
        'photo_pending_review': result.face_verdict == 'PENDING_REVIEW',
    }

@router.post("/check-in")
async def mobile_check_in(
    payload: PunchRequest,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clock in. Rejected unless the device is inside an assigned geofence."""
    return _record_punch(0, payload, current_user, db, request)

@router.post("/check-out")
async def mobile_check_out(
    payload: PunchRequest,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clock out. Subject to the same geofence enforcement as clock-in."""
    return _record_punch(1, payload, current_user, db, request)

@router.get("/face/status")
def my_face_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Tell the app whether this employee still needs to register their face.

    The app calls this after sign-in so it can prompt for a one-off enrolment
    photo instead of silently sending every punch to the review queue.
    """
    from ..services import face_service
    from ..services.geofence_service import load_policy

    emp_code = _resolve_emp_code(current_user, db)
    policy = load_policy(db)

    row = db.execute(text("""
        SELECT fe.enrolled_at, fe.enrolled_source
        FROM personnel_face_enrollment fe
        JOIN personnel p ON p.id = fe.personnel_id
        WHERE UPPER(p.emp_code) = UPPER(:emp)
    """), {"emp": emp_code}).fetchone()

    available = face_service.is_available()
    return {
        "success": True,
        "emp_code": emp_code,
        "enrolled": row is not None,
        "enrolled_at": row.enrolled_at if row else None,
        "enrolled_source": row.enrolled_source if row else None,
        # The app should only show the enrolment screen when it would actually work.
        "can_self_enrol": bool(
            available and policy.face_matching_enabled
            and policy.allow_self_enrolment and row is None
        ),
        "face_matching_available": available,
    }


@router.post("/face/enrol")
def self_enrol_face(
    body: SelfEnrolRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Register the signed-in employee's own reference face.

    Creates a reference only where none exists. Replacing one is deliberately an
    administrator action: if self-enrolment could overwrite, anyone who obtained
    an account could quietly re-point it at their own face and the match would
    then confirm the impostor rather than catch them.
    """
    from ..services import face_service
    from ..services.geofence_service import load_policy

    emp_code = _resolve_emp_code(current_user, db)
    policy = load_policy(db)

    if not policy.allow_self_enrolment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is turned off. Ask your supervisor to register your photo.",
        )
    if not face_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Face registration is unavailable on this server right now.",
        )

    person = db.execute(text(
        "SELECT id FROM personnel WHERE UPPER(emp_code) = UPPER(:emp) AND is_active IS TRUE"
    ), {"emp": emp_code}).fetchone()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee record not found")

    existing = db.execute(text(
        "SELECT 1 FROM personnel_face_enrollment WHERE personnel_id = :pid"
    ), {"pid": person.id}).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Your photo is already registered. Contact your supervisor to change it.",
        )

    vec = face_service.embed(body.photo_base64)
    if vec is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face was found in that photo. Face the camera in good light "
                   "and make sure your whole face is visible.",
        )

    from .geofence_admin import _store_reference_photo
    path = _store_reference_photo(emp_code, body.photo_base64)

    db.execute(text("""
        INSERT INTO personnel_face_enrollment
            (personnel_id, embedding, model_name, dimensions,
             reference_photo_path, enrolled_at, enrolled_by, enrolled_source, updated_at)
        VALUES (:pid, :emb, :model, :dims, :path, now(), :by, 'SELF', now())
    """), {
        "pid": person.id,
        "emb": face_service.to_bytes(vec),
        "model": face_service.MODEL_NAME,
        "dims": len(vec),
        "path": path,
        "by": getattr(current_user, "username", None),
    })
    db.commit()

    logger.info("Face self-enrolled for %s", emp_code)
    return {"success": True, "message": "Your photo has been registered.",
            "emp_code": emp_code, "enrolled_source": "SELF"}


@router.get("/my-sites")
async def get_my_sites(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Geofences assigned to the caller, so the app can show fence status and
    grey out the clock-in button before a punch is attempted.

    This is a convenience for the employee, not a security boundary — the
    server revalidates every punch regardless of what the app believed.
    """
    emp_code = _resolve_emp_code(current_user, db)

    # The app shows who it believes is signed in, so somebody handed the wrong
    # credentials notices before they clock in as a colleague.
    who = db.execute(text("""
        SELECT p.emp_code, p.first_name, p.last_name, p.full_name, d.name AS department
        FROM personnel p
        LEFT JOIN departments d ON d.id = p.department_id
        WHERE UPPER(p.emp_code) = UPPER(:emp_code)
    """), {"emp_code": emp_code}).fetchone()

    rows = db.execute(text("""
        SELECT z.id, z.name, z.code, z.address,
               z.geofence_lat, z.geofence_lng, z.geofence_radius_m,
               z.geofence_polygon, z.gps_accuracy_max_m, z.require_selfie,
               zpa.is_primary_zone
        FROM zones z
        JOIN zone_personnel_assignments zpa ON zpa.zone_id = z.id
        JOIN personnel p                    ON p.id = zpa.personnel_id
        WHERE p.emp_code = :emp_code
          AND z.is_active IS TRUE
          AND z.geofence_enabled IS TRUE
          AND zpa.status = 'ACTIVE'
          AND zpa.unassigned_at IS NULL
        ORDER BY zpa.is_primary_zone DESC, z.name
    """), {"emp_code": emp_code}).fetchall()

    display_name = None
    if who:
        display_name = (" ".join(filter(None, [who.first_name, who.last_name]))
                        or who.full_name or who.emp_code)

    return {
        'success': True,
        'employee': {
            'emp_code': emp_code,
            'name': display_name or emp_code,
            'department': who.department if who else None,
        },
        'sites': [{
            'id': r.id,
            'name': r.name,
            'code': r.code,
            'address': r.address,
            'latitude': float(r.geofence_lat) if r.geofence_lat is not None else None,
            'longitude': float(r.geofence_lng) if r.geofence_lng is not None else None,
            'radius_m': r.geofence_radius_m,
            'polygon': r.geofence_polygon,
            'gps_accuracy_max_m': r.gps_accuracy_max_m,
            'require_selfie': r.require_selfie,
            'is_primary': r.is_primary_zone,
        } for r in rows],
        'server_time': datetime.now(timezone.utc).isoformat(),
    }

@router.get("/my-qr")
async def get_my_qr_code(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's QR code for mobile access
    """
    try:
        emp_code = _resolve_emp_code(current_user, db)
        
        # Get employee details
        result = db.execute(text("""
            SELECT id, emp_code, first_name, last_name, photo
            FROM personnel_employee
            WHERE emp_code = :emp_code
        """), {'emp_code': emp_code})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Generate QR code data (simplified - in production use proper QR library)
        qr_data = f"POB:{emp_code}:{row[0]}:{datetime.utcnow().timestamp()}"
        
        return {
            'success': True,
            'data': {
                'qr_data': qr_data,
                'emp_code': emp_code,
                'name': f"{row[2]} {row[3]}",
                'photo': row[4]
            }
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate QR code: {str(e)}"
        )

@router.get("/my-location")
async def get_my_location(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's current location/zone
    """
    try:
        emp_code = _resolve_emp_code(current_user, db)
        
        result = db.execute(text("""
            SELECT current_zone_id, is_onboard
            FROM personnel_employee
            WHERE emp_code = :emp_code
        """), {'emp_code': emp_code})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        return {
            'success': True,
            'data': {
                'zone_id': row[0],
                'is_onboard': row[1]
            }
        }
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get location: {str(e)}"
        )

@router.get("/notifications")
async def get_notifications(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get mobile notifications for user
    """
    try:
        emp_code = _resolve_emp_code(current_user, db)
        
        result = db.execute(text("""
            SELECT id, notification_type, message, is_read, created_at
            FROM notifications
            WHERE emp_code = :emp_code
            ORDER BY created_at DESC
            LIMIT :limit
        """), {'emp_code': emp_code, 'limit': limit})
        
        notifications = []
        for row in result:
            notifications.append({
                'id': row[0],
                'type': row[1],
                'message': row[2],
                'is_read': row[3],
                'created_at': row[4].isoformat() if row[4] else None
            })
        
        return {
            'success': True,
            'data': notifications
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
        )

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read
    """
    try:
        emp_code = _resolve_emp_code(current_user, db)
        
        db.execute(text("""
            UPDATE notifications
            SET is_read = TRUE, read_at = :read_at
            WHERE id = :notification_id AND emp_code = :emp_code
        """), {
            'notification_id': notification_id,
            'emp_code': emp_code,
            'read_at': datetime.utcnow()
        })
        
        db.commit()
        
        return {
            'success': True,
            'message': 'Notification marked as read'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

