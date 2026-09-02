"""
Geofence validation for mobile clock-in / clock-out.

Every mobile punch is validated here, server-side, before it is allowed to
become an attendance record. The mobile app performs the same distance check
locally so it can grey out the button, but that check is advisory only — a
patched app can always claim it passed. This module is the enforcement point.

Geometry is computed in Python rather than PostGIS: at a few hundred sites the
per-punch cost is negligible and it keeps the stock postgres:15-alpine image.
If the estate ever reaches five figures, move `_candidate_zones` to a PostGIS
`ST_DWithin` query and leave the rest of this module untouched.
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6_371_008.8

# --- Policy defaults -------------------------------------------------------
# Per-site overrides live on the zones row; these apply when a site is silent.

# A punch reporting worse accuracy than its site allows is not trustworthy
# enough to enforce a fence against, in either direction.
DEFAULT_GPS_ACCURACY_MAX_M = 100.0

# The fence is widened by the reported GPS accuracy so a legitimate employee
# standing at the gate with a poor fix is not turned away. The widening is
# capped: without a cap, a spoofer would simply report accuracy=5000 and
# inflate the fence to cover the whole city.
DEFAULT_ACCURACY_BUFFER_CAP_M = 50.0

# Sustained speed between consecutive punches above which the pair is
# physically implausible. Generous enough to cover a domestic flight, because
# two punches can legitimately be days and a continent apart.
IMPOSSIBLE_TRAVEL_KMH = 900.0

# The approach trail is different: it covers the minutes before a single punch,
# during which the employee is travelling to the warehouse on the ground. The
# flight-tolerant threshold above would wave through an obvious spoof — jumping
# 9km in two minutes is only 267 km/h — so ground movement gets its own, far
# tighter limit. Still generous enough for a car on an expressway.
APPROACH_MAX_GROUND_SPEED_KMH = 200.0

# Device clock drift beyond this is recorded as evidence. It never affects the
# stored punch time, which is always server time.
CLOCK_SKEW_FLAG_SECONDS = 300.0

# A real GNSS fix jitters between consecutive samples even on a stationary
# handset. A spoofed one is pinned to an exact coordinate and does not move at
# all. Below this spread across the sample window the fix looks synthetic.
MIN_EXPECTED_DRIFT_M = 0.5

# Samples needed before the drift signal means anything. Two identical readings
# happen legitimately when the OS returns a cached fix twice.
MIN_DRIFT_SAMPLES = 3

# Below this site elevation, a reported altitude of exactly zero is
# unremarkable and the sentinel check is skipped.
ZERO_ALTITUDE_MIN_SITE_ELEVATION_M = 20.0

# Altitude tolerance against the site's recorded elevation. GNSS altitude is
# far less accurate than horizontal position — routinely +/-30m, worse under
# cover — so this is deliberately loose and only catches gross mismatches.
ALTITUDE_TOLERANCE_M = 150.0

# No single soft signal blocks a punch. Enough of them together does: this is
# the composite threshold at which an accepted-but-suspicious punch becomes a
# rejection.
REJECT_RISK_THRESHOLD = 80


# --- Policy loading -------------------------------------------------------
# The constants above are defaults and fallbacks. The live values come from the
# geofence_policy row so an administrator can tune them without a redeploy —
# the right thresholds only emerge from real GPS behaviour at the client's own
# warehouses, and nobody wants a code change to widen a drift tolerance.

_POLICY_TTL_SECONDS = 30.0
_policy_cache: dict[str, Any] = {"at": 0.0, "value": None}


@dataclass
class Policy:
    impossible_travel_kmh: float = IMPOSSIBLE_TRAVEL_KMH
    approach_max_ground_speed_kmh: float = APPROACH_MAX_GROUND_SPEED_KMH
    reject_risk_threshold: int = REJECT_RISK_THRESHOLD
    min_expected_drift_m: float = MIN_EXPECTED_DRIFT_M
    min_drift_samples: int = MIN_DRIFT_SAMPLES
    altitude_tolerance_m: float = ALTITUDE_TOLERANCE_M
    clock_skew_flag_seconds: float = CLOCK_SKEW_FLAG_SECONDS
    risk_rooted_device: int = 40
    risk_static_gps: int = 50
    risk_implausible_altitude: int = 40
    risk_zero_altitude: int = 30
    risk_implausible_accuracy: int = 30
    risk_clock_skew: int = 20
    risk_accuracy_buffer: int = 10
    block_rooted_devices: bool = False
    block_mock_location: bool = True
    risk_mock_location: int = 50
    face_match_threshold: float = 0.40
    face_matching_enabled: bool = True
    block_on_face_mismatch: bool = False
    allow_self_enrolment: bool = True
    duplicate_punch_seconds: int = 120
    enforce_punch_order: bool = True
    allow_pwa_punches: bool = True
    risk_pwa_client: int = 0
    late_reason_after_minutes: int = 15


def load_policy(db: Session, force: bool = False) -> Policy:
    """
    Current clock-in rules, cached briefly.

    Cached because every punch reads them and they change perhaps monthly. A
    missing or unreadable row falls back to the module defaults rather than
    failing the punch: an administrative table being absent must never stop a
    warehouse clocking in.
    """
    now = time.monotonic()
    if not force and _policy_cache["value"] is not None and now - _policy_cache["at"] < _POLICY_TTL_SECONDS:
        return _policy_cache["value"]
    try:
        row = db.execute(text("SELECT * FROM geofence_policy WHERE id = 1")).fetchone()
        policy = Policy(**{
            f: row._mapping[f] for f in Policy.__dataclass_fields__
            if f in row._mapping and row._mapping[f] is not None
        }) if row else Policy()
    except Exception:
        logger.warning("geofence_policy unreadable — falling back to built-in defaults")
        policy = Policy()
    _policy_cache.update({"at": now, "value": policy})
    return policy


def invalidate_policy_cache() -> None:
    """Called after an administrator saves new rules, so they take effect at once."""
    _policy_cache.update({"at": 0.0, "value": None})


class Decision:
    ACCEPTED = "ACCEPTED"
    ACCEPTED_FLAGGED = "ACCEPTED_FLAGGED"
    REJECTED = "REJECTED"


class ClientType:
    """
    How much the server can trust what the client tells it.

    NATIVE runs the integrity modules — Play Integrity, App Attest,
    mock-location and root checks. PWA runs in a browser, where none of those
    APIs exist: it can report a position and a photo and nothing more. Treating
    the two alike would make the browser the obvious way to defeat the whole
    control, so the difference is recorded and scored.
    """
    NATIVE = "NATIVE"
    PWA = "PWA"


class Reason:
    OUTSIDE_FENCE = "OUTSIDE_FENCE"
    LOW_GPS_ACCURACY = "LOW_GPS_ACCURACY"
    MOCK_LOCATION = "MOCK_LOCATION"
    ROOTED_DEVICE = "ROOTED_DEVICE"
    EMULATOR = "EMULATOR"
    ATTESTATION_FAILED = "ATTESTATION_FAILED"
    NO_ASSIGNMENT = "NO_ASSIGNMENT"
    NO_FENCE_CONFIGURED = "NO_FENCE_CONFIGURED"
    IMPOSSIBLE_TRAVEL = "IMPOSSIBLE_TRAVEL"
    CLOCK_SKEW = "CLOCK_SKEW"
    STATIC_GPS = "STATIC_GPS"
    IMPLAUSIBLE_ALTITUDE = "IMPLAUSIBLE_ALTITUDE"
    APPROACH_TELEPORT = "APPROACH_TELEPORT"
    COMPOSITE_RISK = "COMPOSITE_RISK"
    MISSING_SELFIE = "MISSING_SELFIE"
    PWA_NOT_PERMITTED = "PWA_NOT_PERMITTED"
    FACE_MISMATCH = "FACE_MISMATCH"


# Messages shown to the employee. Deliberately vague about *how far* outside
# the fence they are — telling them "you are 340m away" is a free calibration
# tool for anyone probing the boundary.
EMPLOYEE_MESSAGE = {
    Reason.OUTSIDE_FENCE: "You are not at your assigned warehouse location.",
    Reason.LOW_GPS_ACCURACY: (
        "Your location signal is too weak to confirm where you are. "
        "Step outside or into the yard and try again."
    ),
    Reason.MOCK_LOCATION: "Mock location is enabled on this device. Turn it off to clock in.",
    Reason.ROOTED_DEVICE: "This device cannot be used to clock in. Contact your supervisor.",
    Reason.EMULATOR: "This device cannot be used to clock in. Contact your supervisor.",
    Reason.ATTESTATION_FAILED: "This device cannot be used to clock in. Contact your supervisor.",
    Reason.NO_ASSIGNMENT: "You are not assigned to any warehouse. Contact your supervisor.",
    Reason.NO_FENCE_CONFIGURED: "Your warehouse is not yet set up for mobile clock-in.",
    Reason.IMPOSSIBLE_TRAVEL: "We could not verify this clock-in. Contact your supervisor.",
    Reason.STATIC_GPS: "We could not verify your location. Contact your supervisor.",
    Reason.IMPLAUSIBLE_ALTITUDE: "We could not verify your location. Contact your supervisor.",
    Reason.APPROACH_TELEPORT: "We could not verify your location. Contact your supervisor.",
    Reason.COMPOSITE_RISK: "We could not verify this clock-in. Contact your supervisor.",
    Reason.MISSING_SELFIE: "A photo is required to clock in at this warehouse.",
    Reason.PWA_NOT_PERMITTED: (
        "Please clock in using the Apex Clock app rather than the browser."
    ),
    Reason.FACE_MISMATCH: (
        "The photo does not match your record. Contact your supervisor."
    ),
}


@dataclass
class LocationSample:
    """One fix from the short burst the app captures around a punch."""
    latitude: float
    longitude: float
    accuracy_m: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class DeviceContext:
    """What the mobile app reports about itself and its surroundings."""
    latitude: float
    longitude: float
    gps_accuracy_m: Optional[float] = None
    altitude_m: Optional[float] = None
    device_time: Optional[datetime] = None

    # A burst of fixes taken over a few seconds while the punch screen is open.
    # Used for the drift check: a stationary handset still jitters, a spoofed
    # one does not.
    samples: list[LocationSample] = field(default_factory=list)

    # The trail of fixes leading up to the punch, oldest first. Used to confirm
    # the employee actually travelled to the site rather than materialising at it.
    approach_path: list[LocationSample] = field(default_factory=list)

    selfie_provided: bool = False
    device_id: Optional[str] = None
    platform: Optional[str] = None
    app_version: Optional[str] = None
    is_mock_location: Optional[bool] = None
    is_rooted: Optional[bool] = None
    is_emulator: Optional[bool] = None
    attestation_verdict: Optional[str] = None

    # Which client sent this, and what arrived with it. A browser cannot run
    # the integrity checks above, so the server has to know the difference.
    client_type: str = "NATIVE"
    client_ip: Optional[str] = None
    late_reason: Optional[str] = None


@dataclass
class GeofenceResult:
    decision: str
    reason: Optional[str] = None
    message: str = ""
    zone_id: Optional[int] = None
    zone_name: Optional[str] = None
    terminal_sn: Optional[str] = None
    distance_m: Optional[float] = None
    effective_radius_m: Optional[float] = None
    travel_speed_kmh: Optional[float] = None
    clock_skew_seconds: Optional[float] = None
    gps_drift_m: Optional[float] = None
    sample_count: Optional[int] = None
    altitude_delta_m: Optional[float] = None
    approach_max_speed_kmh: Optional[float] = None
    approach_teleport: Optional[bool] = None
    face_verdict: Optional[str] = None
    face_score: Optional[float] = None
    risk_score: int = 0
    flags: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.decision != Decision.REJECTED


# --- Geometry --------------------------------------------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _to_local_xy(lat: float, lon: float, ref_lat: float, ref_lon: float) -> tuple[float, float]:
    """
    Equirectangular projection to metres about a reference point. Warehouse
    footprints span a few hundred metres, where the distortion is far below
    GPS noise.
    """
    x = math.radians(lon - ref_lon) * math.cos(math.radians(ref_lat)) * EARTH_RADIUS_M
    y = math.radians(lat - ref_lat) * EARTH_RADIUS_M
    return x, y


def _point_in_ring(x: float, y: float, ring: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon."""
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            x_cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_cross:
                inside = not inside
    return inside


def _distance_to_ring(x: float, y: float, ring: list[tuple[float, float]]) -> float:
    """Shortest distance from a point to a closed polygon's edges."""
    best = float("inf")
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            best = min(best, math.hypot(x - x1, y - y1))
            continue
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / seg_len_sq))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return best


def distance_to_fence_m(lat: float, lon: float, zone: Any) -> Optional[float]:
    """
    Distance from a point to the edge of a zone's fence: 0 when inside,
    positive metres when outside. Returns None if the zone has no usable fence.

    A polygon, when present, takes precedence over the circular radius.
    """
    polygon = _parse_polygon(getattr(zone, "geofence_polygon", None))
    if polygon:
        ref_lat, ref_lon = polygon[0]
        ring = [_to_local_xy(plat, plon, ref_lat, ref_lon) for plat, plon in polygon]
        px, py = _to_local_xy(lat, lon, ref_lat, ref_lon)
        if _point_in_ring(px, py, ring):
            return 0.0
        return _distance_to_ring(px, py, ring)

    if zone.geofence_lat is None or zone.geofence_lng is None:
        return None
    centre_distance = haversine_m(lat, lon, float(zone.geofence_lat), float(zone.geofence_lng))
    return max(0.0, centre_distance - float(zone.geofence_radius_m or 0))


def _parse_polygon(raw: Any) -> Optional[list[tuple[float, float]]]:
    """Normalise a stored polygon to [(lat, lng), ...]; None if unusable."""
    if not raw:
        return None
    points = raw.get("points") if isinstance(raw, dict) else raw
    if not isinstance(points, list) or len(points) < 3:
        return None
    try:
        return [(float(p[0]), float(p[1])) for p in points]
    except (TypeError, ValueError, IndexError):
        return None



# --- Spoofing detectors ----------------------------------------------------
# None of these is conclusive alone. Each contributes to a risk score, and it
# is the combination that blocks a punch — a single soft signal must never
# strand a legitimate employee at the gate.

def analyse_drift(samples: list[LocationSample], min_samples: int = MIN_DRIFT_SAMPLES) -> Optional[float]:
    """
    Spread, in metres, across a burst of fixes.

    A handset lying still on a table still wanders a few metres between
    readings — GNSS noise guarantees it. A location injected by a mock provider
    is byte-identical every time. Returns None when there are too few samples
    for the signal to mean anything.
    """
    if len(samples) < min_samples:
        return None
    lat0, lon0 = samples[0].latitude, samples[0].longitude
    return max(haversine_m(lat0, lon0, s.latitude, s.longitude) for s in samples)


def analyse_altitude(reported: Optional[float], site_elevation: Optional[float]) -> Optional[float]:
    """
    Difference between reported altitude and the site's known elevation.

    Cheap to check and awkward to fake: most spoofing apps let you drop a pin
    on a map but have no elevation model behind it, so they report zero or
    leave the field empty. Returns None when either value is unavailable, which
    is the common case until sites have elevations recorded.
    """
    if reported is None or site_elevation is None:
        return None
    return abs(reported - float(site_elevation))


def analyse_approach(path: list[LocationSample],
                     max_ground_speed_kmh: float = APPROACH_MAX_GROUND_SPEED_KMH,
                     ) -> tuple[Optional[float], bool]:
    """
    Fastest leg along the approach trail, and whether any leg is a teleport.

    Distinct from the punch-to-punch travel check: this looks *within* the
    minutes before a single punch. Someone walking to the gate leaves a
    contiguous track; someone flipping on a fake-GPS app jumps from their
    sofa to the warehouse in one step.
    """
    timed = [p for p in path if p.timestamp is not None]
    if len(timed) < 2:
        return None, False
    timed.sort(key=lambda p: p.timestamp)

    fastest = 0.0
    for previous, current in zip(timed, timed[1:]):
        elapsed_h = (current.timestamp - previous.timestamp).total_seconds() / 3600.0
        if elapsed_h <= 0:
            continue
        km = haversine_m(previous.latitude, previous.longitude,
                         current.latitude, current.longitude) / 1000.0
        fastest = max(fastest, km / elapsed_h)

    return fastest, fastest > max_ground_speed_kmh


# --- Validation ------------------------------------------------------------

def _candidate_zones(db: Session, emp_code: str) -> list[Any]:
    """
    Fence-enabled zones the employee is currently assigned to.

    An employee working across several warehouses is validated against all of
    them; the nearest match wins. Assignments that have been ended or have not
    started are excluded.
    """
    return db.execute(text("""
        SELECT z.id, z.name, z.code, z.mobile_terminal_sn,
               z.geofence_lat, z.geofence_lng, z.geofence_radius_m,
               z.geofence_polygon, z.gps_accuracy_max_m,
               z.accuracy_buffer_cap_m, z.require_selfie, z.elevation_m
        FROM zones z
        JOIN zone_personnel_assignments zpa ON zpa.zone_id = z.id
        JOIN personnel p                    ON p.id = zpa.personnel_id
        WHERE p.emp_code = :emp_code
          AND z.is_active IS TRUE
          AND z.geofence_enabled IS TRUE
          AND zpa.status = 'ACTIVE'
          AND zpa.unassigned_at IS NULL
    """), {"emp_code": emp_code}).fetchall()


def _last_punch_location(db: Session, emp_code: str) -> Optional[tuple[float, float, datetime]]:
    """Most recent accepted mobile punch position, for the travel-speed check."""
    row = db.execute(text("""
        SELECT device_lat, device_lng, server_time
        FROM mobile_punch_evidence
        WHERE emp_code = :emp_code
          AND decision IN ('ACCEPTED', 'ACCEPTED_FLAGGED')
          AND device_lat IS NOT NULL
        ORDER BY server_time DESC
        LIMIT 1
    """), {"emp_code": emp_code}).fetchone()
    if not row or row.device_lat is None:
        return None
    return float(row.device_lat), float(row.device_lng), row.server_time


def validate_punch(
    db: Session,
    emp_code: str,
    device: DeviceContext,
    server_time: Optional[datetime] = None,
) -> GeofenceResult:
    """
    Decide whether a mobile punch may become an attendance record.

    Rejection is reserved for signals that are unambiguous — a spoofed location,
    a tampered device, or a position plainly outside every assigned fence.
    Softer signals raise the risk score and surface the punch to a supervisor
    rather than blocking a legitimate employee at the gate.
    """
    now = server_time or datetime.now(timezone.utc)
    policy = load_policy(db)
    flags: list[str] = []
    risk = 0

    # 0. Resolve the site first, for context only.
    #
    #    The integrity stops below do not depend on it, but the evidence row
    #    does: a spoofed punch recorded against no warehouse disappears the
    #    moment a supervisor filters their own site, which would hide exactly
    #    the punches most worth seeing. Resolving here means every rejection
    #    names the warehouse the employee claimed to be at.
    zones = _candidate_zones(db, emp_code)
    scored = []
    for z in zones:
        d = distance_to_fence_m(device.latitude, device.longitude, z)
        if d is not None:
            scored.append((d, z))
    distance, zone = min(scored, key=lambda pair: pair[0]) if scored else (None, None)

    # 1. Client trust, then device integrity.
    #
    #    A browser client cannot run any of the checks below, so its punches are
    #    accepted only while the policy permits it and always carry a standing
    #    risk score. During a pilot that score is zero; once the native app is
    #    distributed, raising it (or switching the flag off) closes the browser
    #    as a spoofing route without another deployment.
    if device.client_type == ClientType.PWA:
        if not policy.allow_pwa_punches:
            return _reject(Reason.PWA_NOT_PERMITTED, risk=100,
                           flags=["pwa_not_permitted"], zone=zone, distance=distance)
        if policy.risk_pwa_client:
            flags.append("browser_client")
            risk += policy.risk_pwa_client

    #    These are hard stops: there is no benign reason for a mock-location
    #    provider to be feeding the app.
    if device.is_mock_location:
        flags.append("mock_location")
        # A hard refusal by default — nothing benign feeds a mock provider.
        # It can be relaxed for testing, because an emulator reports its
        # position this way and would otherwise never produce a punch that
        # succeeds. Relaxed, the punch still carries the risk score.
        if policy.block_mock_location:
            return _reject(Reason.MOCK_LOCATION, risk=100, flags=flags,
                           zone=zone, distance=distance)
        risk += policy.risk_mock_location
    if device.is_emulator:
        return _reject(Reason.EMULATOR, risk=100, flags=["emulator"],
                       zone=zone, distance=distance)
    if device.attestation_verdict and device.attestation_verdict.upper() in {"FAIL", "FAILED", "UNRECOGNISED"}:
        return _reject(Reason.ATTESTATION_FAILED, risk=100, flags=["attestation_failed"],
                       zone=zone, distance=distance)

    # A rooted phone is suspicious but not proof of fraud — plenty of people
    # root their own handset for unrelated reasons. Flag, do not block.
    if device.is_rooted:
        flags.append("rooted_device")
        if policy.block_rooted_devices:
            return _reject(Reason.ROOTED_DEVICE, risk=100, flags=flags,
                           zone=zone, distance=distance)
        risk += policy.risk_rooted_device

    # 2. Clock skew is evidence only. The punch is stamped with server time
    #    regardless, so a manipulated device clock cannot shift a shift boundary.
    clock_skew = None
    if device.device_time is not None:
        dt = device.device_time
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        clock_skew = abs((now - dt).total_seconds())
        if clock_skew > policy.clock_skew_flag_seconds:
            flags.append("clock_skew")
            risk += policy.risk_clock_skew

    # 3. Confirm the site resolved to something usable.
    if not zones:
        return _reject(Reason.NO_ASSIGNMENT, risk=risk, flags=flags, clock_skew=clock_skew)
    if zone is None:
        return _reject(Reason.NO_FENCE_CONFIGURED, risk=risk, flags=flags, clock_skew=clock_skew)

    # 4. Accuracy gate, using the nearest site's policy. Checked after site
    #    resolution so the message can name the right warehouse, and before the
    #    fence test because an untrustworthy fix cannot settle either way.
    accuracy_max = float(zone.gps_accuracy_max_m or DEFAULT_GPS_ACCURACY_MAX_M)
    accuracy = device.gps_accuracy_m
    if accuracy is not None and accuracy > accuracy_max:
        return _reject(
            Reason.LOW_GPS_ACCURACY, risk=risk, flags=flags + ["low_accuracy"],
            zone=zone, distance=distance, clock_skew=clock_skew,
        )

    # An unnaturally perfect fix is itself a spoofing tell: real handsets do not
    # report sub-metre accuracy on open-sky GNSS, let alone under a steel roof.
    if accuracy is not None and accuracy <= 1.0:
        flags.append("implausible_accuracy")
        risk += policy.risk_implausible_accuracy

    # 5. The fence test. The allowance is the reported accuracy, capped.
    buffer_cap = float(zone.accuracy_buffer_cap_m or DEFAULT_ACCURACY_BUFFER_CAP_M)
    allowance = min(accuracy or 0.0, buffer_cap)
    effective_radius = float(zone.geofence_radius_m or 0) + allowance

    if distance > allowance:
        return _reject(
            Reason.OUTSIDE_FENCE, risk=risk, flags=flags, zone=zone,
            distance=distance, effective_radius=effective_radius, clock_skew=clock_skew,
        )

    # An employee admitted only by the accuracy allowance is worth recording as
    # a borderline case — a cluster of these means the fence needs recalibrating.
    if distance > 0:
        flags.append("within_accuracy_buffer")
        risk += policy.risk_accuracy_buffer

    # 5a. Selfie gate. Geofencing establishes that a phone was on site; it says
    #     nothing about who was holding it. Where a site requires a photo, a
    #     punch without one is refused outright rather than risk-scored.
    face_verdict = None
    if zone.require_selfie:
        if not device.selfie_provided:
            return _reject(
                Reason.MISSING_SELFIE, risk=risk, flags=flags, zone=zone,
                distance=distance, effective_radius=effective_radius,
                clock_skew=clock_skew,
            )
        face_verdict = "PENDING_REVIEW"

    # 5b. Spoofing detectors. Each contributes to the risk score; the composite
    #     threshold below decides. A teleport inside the approach trail is the
    #     one exception — there is no innocent reading of it.
    drift = analyse_drift(device.samples, policy.min_drift_samples)
    if drift is not None and drift < policy.min_expected_drift_m:
        flags.append("static_gps")
        risk += policy.risk_static_gps

    altitude_delta = analyse_altitude(device.altitude_m, zone.elevation_m)
    if altitude_delta is not None and altitude_delta > policy.altitude_tolerance_m:
        flags.append("implausible_altitude")
        risk += policy.risk_implausible_altitude
    elif (
        device.altitude_m == 0.0
        and zone.elevation_m is not None
        and float(zone.elevation_m) >= ZERO_ALTITUDE_MIN_SITE_ELEVATION_M
    ):
        # Exactly zero is a sentinel, not a measurement — a real GNSS fix
        # essentially never lands on 0.000. It is the default a spoofing app
        # emits when it has no elevation model behind the pin. Scored below the
        # gross-mismatch signal because some handsets also use 0 to mean
        # "unavailable"; the mobile client must send null in that case.
        flags.append("zero_altitude")
        risk += policy.risk_zero_altitude

    approach_speed, teleported = analyse_approach(
        device.approach_path, policy.approach_max_ground_speed_kmh)
    if teleported:
        return _reject(
            Reason.APPROACH_TELEPORT, risk=100, flags=flags + ["approach_teleport"],
            zone=zone, distance=distance, effective_radius=effective_radius,
            clock_skew=clock_skew, drift=drift, sample_count=len(device.samples),
            altitude_delta=altitude_delta, approach_speed=approach_speed,
            approach_teleport=True,
        )

    # 6. Physics. Compared against the previous accepted punch.
    speed_kmh = None
    previous = _last_punch_location(db, emp_code)
    if previous:
        prev_lat, prev_lng, prev_time = previous
        elapsed_h = (now - prev_time).total_seconds() / 3600.0
        if elapsed_h > 0:
            moved_km = haversine_m(prev_lat, prev_lng, device.latitude, device.longitude) / 1000.0
            speed_kmh = moved_km / elapsed_h
            if speed_kmh > policy.impossible_travel_kmh:
                return _reject(
                    Reason.IMPOSSIBLE_TRAVEL, risk=100, flags=flags + ["impossible_travel"],
                    zone=zone, distance=distance, effective_radius=effective_radius,
                    speed=speed_kmh, clock_skew=clock_skew,
                )

    # Composite judgement. Individually these signals all have innocent
    # explanations; stacked up they do not. Blocking on the total rather than
    # on any one of them is what keeps false positives off the gate.
    shared = dict(
        zone_id=zone.id,
        zone_name=zone.name,
        terminal_sn=zone.mobile_terminal_sn,
        distance_m=distance,
        effective_radius_m=effective_radius,
        travel_speed_kmh=speed_kmh,
        clock_skew_seconds=clock_skew,
        gps_drift_m=drift,
        sample_count=len(device.samples) or None,
        altitude_delta_m=altitude_delta,
        approach_max_speed_kmh=approach_speed,
        approach_teleport=teleported,
        risk_score=risk,
        flags=flags,
    )

    if risk >= policy.reject_risk_threshold:
        return GeofenceResult(
            decision=Decision.REJECTED,
            reason=Reason.COMPOSITE_RISK,
            message=EMPLOYEE_MESSAGE[Reason.COMPOSITE_RISK],
            **shared,
        )

    return GeofenceResult(
        decision=Decision.ACCEPTED_FLAGGED if risk >= 40 else Decision.ACCEPTED,
        message="Confirmed at " + zone.name,
        face_verdict=face_verdict,
        **shared,
    )


def _reject(
    reason: str, risk: int, flags: list[str],
    zone: Any = None, distance: Optional[float] = None,
    effective_radius: Optional[float] = None, speed: Optional[float] = None,
    clock_skew: Optional[float] = None, drift: Optional[float] = None,
    sample_count: Optional[int] = None, altitude_delta: Optional[float] = None,
    approach_speed: Optional[float] = None, approach_teleport: Optional[bool] = None,
) -> GeofenceResult:
    return GeofenceResult(
        decision=Decision.REJECTED,
        reason=reason,
        message=EMPLOYEE_MESSAGE.get(reason, "Clock-in could not be confirmed."),
        zone_id=zone.id if zone is not None else None,
        zone_name=zone.name if zone is not None else None,
        terminal_sn=zone.mobile_terminal_sn if zone is not None else None,
        distance_m=distance,
        effective_radius_m=effective_radius,
        travel_speed_kmh=speed,
        clock_skew_seconds=clock_skew,
        gps_drift_m=drift,
        sample_count=sample_count,
        altitude_delta_m=altitude_delta,
        approach_max_speed_kmh=approach_speed,
        approach_teleport=approach_teleport,
        risk_score=max(risk, 50),
        flags=flags,
    )


def record_evidence(
    db: Session,
    emp_code: str,
    punch_state: int,
    device: DeviceContext,
    result: GeofenceResult,
    transaction_id: Optional[int],
    server_time: datetime,
    selfie_path: Optional[str] = None,
) -> None:
    """
    Persist the full evidence trail for a punch — accepted or rejected alike.

    Rejected attempts matter as much as accepted ones: a run of blocked
    clock-ins from a residential address is exactly the signal HR asked for.
    """
    db.execute(text("""
        INSERT INTO mobile_punch_evidence (
            transaction_id, emp_code, zone_id, punch_state,
            decision, reason, risk_score,
            device_lat, device_lng, gps_accuracy_m, distance_m, effective_radius_m,
            device_time, server_time, clock_skew_seconds,
            device_id, platform, app_version,
            is_mock_location, is_rooted, is_emulator, attestation_verdict,
            travel_speed_kmh, altitude_m, altitude_delta_m,
            gps_drift_m, sample_count,
            approach_max_speed_kmh, approach_teleport,
            selfie_path, face_verdict, face_score, client_type, client_ip, late_reason, raw
        ) VALUES (
            :transaction_id, :emp_code, :zone_id, :punch_state,
            :decision, :reason, :risk_score,
            :device_lat, :device_lng, :gps_accuracy_m, :distance_m, :effective_radius_m,
            :device_time, :server_time, :clock_skew_seconds,
            :device_id, :platform, :app_version,
            :is_mock_location, :is_rooted, :is_emulator, :attestation_verdict,
            :travel_speed_kmh, :altitude_m, :altitude_delta_m,
            :gps_drift_m, :sample_count,
            :approach_max_speed_kmh, :approach_teleport,
            :selfie_path, :face_verdict, :face_score, :client_type, :client_ip, :late_reason,
            CAST(:raw AS jsonb)
        )
    """), {
        "transaction_id": transaction_id,
        "emp_code": emp_code,
        "zone_id": result.zone_id,
        "punch_state": punch_state,
        "decision": result.decision,
        "reason": result.reason,
        "risk_score": result.risk_score,
        "device_lat": device.latitude,
        "device_lng": device.longitude,
        "gps_accuracy_m": device.gps_accuracy_m,
        "distance_m": result.distance_m,
        "effective_radius_m": result.effective_radius_m,
        "device_time": device.device_time,
        "server_time": server_time,
        "clock_skew_seconds": result.clock_skew_seconds,
        "device_id": device.device_id,
        "platform": device.platform,
        "app_version": device.app_version,
        "is_mock_location": device.is_mock_location,
        "is_rooted": device.is_rooted,
        "is_emulator": device.is_emulator,
        "attestation_verdict": device.attestation_verdict,
        "travel_speed_kmh": result.travel_speed_kmh,
        "altitude_m": device.altitude_m,
        "altitude_delta_m": result.altitude_delta_m,
        "gps_drift_m": result.gps_drift_m,
        "sample_count": result.sample_count,
        "approach_max_speed_kmh": result.approach_max_speed_kmh,
        "approach_teleport": result.approach_teleport,
        "selfie_path": selfie_path,
        "face_verdict": result.face_verdict,
        "face_score": result.face_score,
        "client_type": device.client_type,
        "client_ip": device.client_ip,
        "late_reason": device.late_reason,
        "raw": json.dumps({"flags": result.flags}),
    })
