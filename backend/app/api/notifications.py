"""
Notifications API — backed by sys_notifications table.

GET  /api/v1/notifications/               — list + auto-generate from real events
PUT  /api/v1/notifications/mark-all-read/ — mark all as read
PUT  /api/v1/notifications/{id}/read/     — mark one as read
DELETE /api/v1/notifications/{id}         — delete one

Generators run on every GET, each in a savepoint — one failure never
blocks the others. dedup_key prevents the same alert appearing twice.
"""

import asyncio
import json
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Dict, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db, SessionLocal
from ..core.dependencies import get_current_user, get_current_user_sse

router = APIRouter(tags=["notifications"])
logger = logging.getLogger(__name__)

# ── SSE broadcaster — Redis Pub/Sub for cross-worker delivery ─────────────────
#
# Architecture:
#   broadcast_notification(payload) → publishes to Redis channel pob:sse_broadcast
#   _redis_subscriber_task() (started at app startup) → subscribes and routes to
#   local asyncio queues for each connected client in this worker.
#
# _sse_clients: Dict[user_id → Set[Queue]] — enables user-scoped delivery.
# payload["_to"] = user_id   → delivered only to that user's queues
# payload["_to"] = None/absent → delivered to every connected client

_sse_clients: Dict[int, Set[asyncio.Queue]] = {}
_sse_lock = asyncio.Lock()

_SSE_CHANNEL = "pob:sse_broadcast"


async def broadcast_notification(payload: dict) -> None:
    """
    Publish a notification to the Redis Pub/Sub channel so all workers deliver it.
    Falls back to local delivery when Redis is unavailable.
    """
    try:
        import redis.asyncio as aioredis
        from ..core.config import settings
        r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.publish(_SSE_CHANNEL, json.dumps(payload))
        await r.aclose()
        return
    except Exception as exc:
        logger.debug("Redis publish failed (%s) — falling back to local delivery", exc)

    # Local fallback (single-worker or Redis down)
    await _deliver_local(payload)


async def _deliver_local(payload: dict) -> None:
    """Route a payload to local SSE queues, respecting user scope."""
    target_user = payload.get("_to")
    async with _sse_lock:
        if target_user is not None:
            queues = list(_sse_clients.get(int(target_user), set()))
        else:
            queues = [q for qs in _sse_clients.values() for q in qs]

        dead_users: Dict[int, Set[asyncio.Queue]] = {}
        for q in queues:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                for uid, qs in _sse_clients.items():
                    if q in qs:
                        dead_users.setdefault(uid, set()).add(q)

        for uid, dead_qs in dead_users.items():
            if uid in _sse_clients:
                _sse_clients[uid].difference_update(dead_qs)
                if not _sse_clients[uid]:
                    del _sse_clients[uid]


async def start_redis_subscriber() -> None:
    """
    Background task: subscribe to the Redis Pub/Sub channel and route messages
    to local clients. Restarts automatically on disconnection.
    Intended to be called once from main.py startup for the leader worker.
    """
    import redis.asyncio as aioredis
    from ..core.config import settings

    while True:
        try:
            r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(_SSE_CHANNEL)
            logger.info("SSE Redis subscriber connected to channel %s", _SSE_CHANNEL)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        await _deliver_local(payload)
                    except Exception as exc:
                        logger.debug("SSE message parse error: %s", exc)
        except asyncio.CancelledError:
            logger.info("SSE Redis subscriber stopped")
            return
        except Exception as exc:
            logger.warning("SSE Redis subscriber disconnected (%s) — reconnecting in 5s", exc)
            await asyncio.sleep(5)


def notify_sync(payload: dict) -> None:
    """Thread-safe wrapper for broadcasting from sync code / Celery tasks."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_notification(payload), loop)
    except Exception:
        pass


# ── notification generators ───────────────────────────────────────────────────

def _upsert(db: Session, dedup_key: str, notification_type: str,
            title: str, message: str, priority: str = "medium",
            link: str = None, expires_hours: int = 48) -> None:
    """Insert a notification only if its dedup_key doesn't already exist."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    db.execute(text("""
        INSERT INTO sys_notifications (dedup_key, notification_type, title, message, priority, link, expires_at)
        VALUES (:dk, :nt, :title, :msg, :pri, :link, :exp)
        ON CONFLICT (dedup_key) DO NOTHING
    """), {"dk": dedup_key, "nt": notification_type, "title": title,
           "msg": message, "pri": priority, "link": link, "exp": expires_at})


def _run_check(db: Session, fn):
    """Run a single generator check in an isolated savepoint so failures don't abort the transaction."""
    try:
        sp = db.begin_nested()
        fn(db)
        sp.commit()
    except Exception as e:
        sp.rollback()
        logger.debug(f"Notification check skipped: {e}")


def _check_subscription(db: Session) -> None:
    today_str = date.today().isoformat()
    sub = db.execute(text(
        "SELECT expiry_date FROM sys_subscription WHERE is_active=TRUE ORDER BY id DESC LIMIT 1"
    )).fetchone()
    if not sub:
        return
    expiry = sub[0]
    now = datetime.now(timezone.utc)
    if not hasattr(expiry, 'hour'):
        expiry = datetime(expiry.year, expiry.month, expiry.day, tzinfo=timezone.utc)
    elif expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    days = int((expiry - now).total_seconds() / 86400)
    if days < 0:
        _upsert(db, f"sub-expired-{sub[0]}", "error",
                "Subscription Expired",
                f"Your licence expired on {sub[0]}. Contact your vendor to renew.",
                "critical", "/subscription", expires_hours=8760)
    elif days <= 7:
        _upsert(db, f"sub-critical-{today_str}", "error",
                f"Subscription Expires in {days} Day{'s' if days != 1 else ''}",
                f"Your licence expires on {sub[0]}. Renew now to avoid system lockout.",
                "critical", "/subscription", expires_hours=24)
    elif days <= 14:
        _upsert(db, f"sub-warning-14-{today_str}", "warning",
                "Subscription Expiring Soon",
                f"Your licence expires on {sub[0]} ({days} days remaining).",
                "high", "/subscription", expires_hours=24)
    elif days <= 30:
        _upsert(db, f"sub-notice-30-{today_str}", "warning",
                "Subscription Renewal Reminder",
                f"Your licence expires on {sub[0]} ({days} days remaining).",
                "medium", "/subscription", expires_hours=48)


def _check_offline_devices(db: Session) -> None:
    today_str = date.today().isoformat()
    offline = db.execute(text("""
        SELECT COALESCE(NULLIF(alias, ''), sn) AS name, sn FROM iclock_terminal
        WHERE last_activity IS NOT NULL
          AND last_activity < NOW() - make_interval(secs =>
                GREATEST(COALESCE(heartbeat_interval, 30) * 5, 300)::float)
        LIMIT 10
    """)).fetchall()
    if not offline:
        return
    names = ", ".join(r[0] for r in offline)
    count = len(offline)
    _upsert(db, f"devices-offline-{today_str}",
            "warning",
            f"{count} Device{'s' if count > 1 else ''} Offline",
            f"The following reader{'s are' if count > 1 else ' is'} not responding: {names}.",
            "high", "/device", expires_hours=4)


def _check_recent_punches(db: Session) -> None:
    recent = db.execute(text("""
        SELECT COUNT(*) AS c FROM iclock_transaction
        WHERE upload_time > NOW() - INTERVAL '15 minutes'
    """)).fetchone()
    if not recent or recent[0] == 0:
        return
    bucket = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')[:-1] + '0'
    _upsert(db, f"punches-{bucket}", "info",
            f"{recent[0]} New Attendance Record{'s' if recent[0] > 1 else ''}",
            f"{recent[0]} punch record{'s' if recent[0] > 1 else ''} received in the last 15 minutes.",
            "low", "/attendance", expires_hours=1)


def _check_pob_summary(db: Session) -> None:
    today_str = date.today().isoformat()
    pob = db.execute(text("""
        SELECT COUNT(*) AS c FROM personnel
        WHERE is_onboard = TRUE AND is_active = TRUE
    """)).fetchone()
    if not pob or pob[0] == 0:
        return
    _upsert(db, f"pob-summary-{today_str}", "info",
            "Daily POB Summary",
            f"{pob[0]} personnel currently onboard.",
            "low", "/pob-status", expires_hours=24)


def _check_mtd_certifications(db: Session) -> None:
    today_str = date.today().isoformat()
    # Expired certs
    expired = db.execute(text("""
        SELECT COUNT(*) AS c FROM mtd_certification
        WHERE expiry_date IS NOT NULL AND expiry_date < CURRENT_DATE
    """)).fetchone()
    if expired and expired[0] > 0:
        _upsert(db, f"mtd-expired-{today_str}", "error",
                f"{expired[0]} Certification{'s' if expired[0] > 1 else ''} Expired",
                f"{expired[0]} MTD certification{'s have' if expired[0] > 1 else ' has'} passed their expiry date and require immediate renewal.",
                "critical", "/mtd", expires_hours=24)
    # Expiring within 30 days
    expiring = db.execute(text("""
        SELECT COUNT(*) AS c FROM mtd_certification
        WHERE expiry_date IS NOT NULL
          AND expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 30
    """)).fetchone()
    if expiring and expiring[0] > 0:
        _upsert(db, f"mtd-expiring-30d-{today_str}", "warning",
                f"{expiring[0]} Certification{'s' if expiring[0] > 1 else ''} Expiring Soon",
                f"{expiring[0]} MTD certification{'s expire' if expiring[0] > 1 else ' expires'} within the next 30 days.",
                "high", "/mtd", expires_hours=24)


def _check_medical_records(db: Session) -> None:
    today_str = date.today().isoformat()
    overdue = db.execute(text("""
        SELECT COUNT(*) AS c FROM mtd_medical_record
        WHERE next_due IS NOT NULL AND next_due < CURRENT_DATE
    """)).fetchone()
    if overdue and overdue[0] > 0:
        _upsert(db, f"medical-overdue-{today_str}", "error",
                f"{overdue[0]} Medical Record{'s' if overdue[0] > 1 else ''} Overdue",
                f"{overdue[0]} personnel medical examination{'s are' if overdue[0] > 1 else ' is'} overdue.",
                "high", "/mtd", expires_hours=24)
    due_soon = db.execute(text("""
        SELECT COUNT(*) AS c FROM mtd_medical_record
        WHERE next_due IS NOT NULL
          AND next_due BETWEEN CURRENT_DATE AND CURRENT_DATE + 30
    """)).fetchone()
    if due_soon and due_soon[0] > 0:
        _upsert(db, f"medical-due-soon-{today_str}", "warning",
                f"{due_soon[0]} Medical Examination{'s' if due_soon[0] > 1 else ''} Due Soon",
                f"{due_soon[0]} personnel medical examination{'s are' if due_soon[0] > 1 else ' is'} due within 30 days.",
                "medium", "/mtd", expires_hours=24)


def _check_employment_contracts(db: Session) -> None:
    today_str = date.today().isoformat()
    expiring = db.execute(text("""
        SELECT COUNT(*) AS c FROM employment_contracts
        WHERE end_date IS NOT NULL
          AND end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 30
          AND LOWER(status) IN ('active', 'approved', '')
    """)).fetchone()
    if expiring and expiring[0] > 0:
        _upsert(db, f"contracts-expiring-{today_str}", "warning",
                f"{expiring[0]} Employment Contract{'s' if expiring[0] > 1 else ''} Expiring",
                f"{expiring[0]} employment contract{'s expire' if expiring[0] > 1 else ' expires'} within the next 30 days.",
                "high", "/personnel", expires_hours=24)


def _check_pending_leave(db: Session) -> None:
    today_str = date.today().isoformat()
    pending = db.execute(text("""
        SELECT COUNT(*) AS c FROM att_leave
        WHERE approval_status = 'pending'
    """)).fetchone()
    if pending and pending[0] > 0:
        _upsert(db, f"leave-pending-{today_str}", "info",
                f"{pending[0]} Leave Request{'s' if pending[0] > 1 else ''} Awaiting Approval",
                f"{pending[0]} leave request{'s require' if pending[0] > 1 else ' requires'} your approval.",
                "medium", "/attendance", expires_hours=24)


def _check_access_denied(db: Session) -> None:
    """Notify on repeated access-denied events in the last hour (possible forced entry)."""
    today_str = date.today().isoformat()
    denied = db.execute(text("""
        SELECT COUNT(*) AS c FROM iclock_transaction
        WHERE punch_time > NOW() - INTERVAL '1 hour'
          AND (status = 4 OR status = 5)
    """)).fetchone()
    if denied and denied[0] >= 5:
        bucket = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H')
        _upsert(db, f"access-denied-{bucket}", "warning",
                f"Access Denied Alert — {denied[0]} Events",
                f"{denied[0]} access-denied events recorded in the last hour. Possible unauthorised access attempt.",
                "high", "/access-control", expires_hours=2)


def _check_pob_zone_discrepancy(db: Session) -> None:
    """Alert when is_onboard=True but current_zone_id=NULL for >4 hours.
    This catches the transport-departure data gap where a passenger was confirmed
    OUTBOUND but their biometric zone was never cleared (no gangway reader, or
    reader has no zone_id configured). Without this check, the POB count is
    inflated and the next muster expected list will include departed personnel.
    """
    bucket = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H')
    stale = db.execute(text("""
        SELECT COUNT(*) AS c FROM personnel
        WHERE is_onboard = TRUE
          AND is_active = TRUE
          AND current_zone_id IS NULL
          AND updated_at < NOW() - INTERVAL '4 hours'
    """)).fetchone()
    if stale and stale[0] > 0:
        _upsert(db, f"pob-zone-discrepancy-{bucket}", "warning",
                f"POB Discrepancy — {stale[0]} Personnel Onboard With No Zone",
                (
                    f"{stale[0]} personnel are marked onboard (is_onboard=TRUE) but have "
                    f"no zone location on record for over 4 hours. They may have departed "
                    f"without a biometric exit scan, causing an inflated POB count. "
                    f"Review transport manifests and access control logs."
                ),
                "high", "/pob-status", expires_hours=4)


def _generate_notifications(db: Session) -> None:
    """Run all generators, each in an isolated savepoint."""
    _run_check(db, _check_subscription)
    _run_check(db, _check_offline_devices)
    _run_check(db, _check_recent_punches)
    _run_check(db, _check_pob_summary)
    _run_check(db, _check_pob_zone_discrepancy)
    _run_check(db, _check_mtd_certifications)
    _run_check(db, _check_medical_records)
    _run_check(db, _check_employment_contracts)
    _run_check(db, _check_pending_leave)
    _run_check(db, _check_access_denied)
    # Purge expired
    try:
        db.execute(text(
            "DELETE FROM sys_notifications WHERE expires_at IS NOT NULL AND expires_at < NOW()"
        ))
        db.commit()
    except Exception as e:
        logger.debug(f"Notification purge failed: {e}")
        db.rollback()


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/stats")
async def notification_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Summary counts — used by the stats strip in the UI."""
    try:
        row = db.execute(text("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE NOT is_read) AS unread,
                COUNT(*) FILTER (WHERE NOT is_read AND priority IN ('critical','high')) AS critical,
                COUNT(*) FILTER (WHERE created_at::date = CURRENT_DATE) AS today
            FROM sys_notifications
            WHERE (user_id IS NULL OR user_id = :uid)
              AND (expires_at IS NULL OR expires_at > NOW())
        """), {"uid": current_user.id}).fetchone()
        return {"success": True, "data": {
            "total": row[0], "unread": row[1], "critical": row[2], "today": row[3]
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_notifications(
    notification_type: Optional[str] = Query(None),
    priority:          Optional[str] = Query(None),
    is_read:           Optional[bool] = Query(None),
    search:            Optional[str]  = Query(None),
    limit:             int            = Query(100, ge=1, le=500),
    offset:            int            = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return notifications for the current user with optional filtering."""
    try:
        _generate_notifications(db)
    except Exception as e:
        logger.warning(f"Notification generation error: {e}")

    try:
        where = [
            "(user_id IS NULL OR user_id = :uid)",
            "(expires_at IS NULL OR expires_at > NOW())",
        ]
        params: dict = {"uid": current_user.id, "limit": limit, "offset": offset}

        if notification_type:
            where.append("notification_type = :ntype")
            params["ntype"] = notification_type
        if priority:
            where.append("priority = :priority")
            params["priority"] = priority
        if is_read is not None:
            where.append("is_read = :is_read")
            params["is_read"] = is_read
        if search:
            where.append("(title ILIKE :search OR message ILIKE :search)")
            params["search"] = f"%{search}%"

        where_sql = " AND ".join(where)

        rows = db.execute(text(f"""
            SELECT id, user_id, notification_type, title, message, priority,
                   is_read, read_at, link, created_at
            FROM sys_notifications
            WHERE {where_sql}
            -- priority is TEXT, so `priority DESC` sorted it alphabetically:
            -- medium > low > high > critical. That put CRITICAL alerts at the
            -- BOTTOM of the bell and ranked 'low' above 'high' — during an
            -- emergency the one notification that mattered was last. Rank it
            -- explicitly instead.
            ORDER BY is_read ASC,
                     CASE lower(priority)
                         WHEN 'critical' THEN 0
                         WHEN 'high'     THEN 1
                         WHEN 'medium'   THEN 2
                         WHEN 'low'      THEN 3
                         ELSE 4
                     END,
                     created_at DESC
            LIMIT :limit OFFSET :offset
        """), params).fetchall()

        total = db.execute(text(f"""
            SELECT COUNT(*) FROM sys_notifications WHERE {where_sql}
        """), {k: v for k, v in params.items() if k not in ("limit", "offset")}).fetchone()[0]

        notifications = [
            {
                "id": r.id,
                "user_id": r.user_id,
                "notification_type": r.notification_type,
                "title": r.title,
                "message": r.message,
                "priority": r.priority,
                "is_read": r.is_read,
                "read_at": r.read_at.isoformat() if r.read_at else None,
                "link": r.link,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
        return {
            "success": True,
            "data": notifications,
            "meta": {"total": total, "limit": limit, "offset": offset},
        }
    except Exception as e:
        logger.error(f"list_notifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mark-all-read")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark all unread notifications as read for the current user."""
    try:
        db.execute(text("""
            UPDATE sys_notifications
            SET is_read = TRUE, read_at = NOW()
            WHERE is_read = FALSE
              AND (user_id IS NULL OR user_id = :uid)
        """), {"uid": current_user.id})
        db.commit()
        return {"success": True, "message": "All notifications marked as read"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}/read")
async def mark_one_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a single notification as read."""
    try:
        db.execute(text("""
            UPDATE sys_notifications
            SET is_read = TRUE, read_at = NOW()
            WHERE id = :id AND (user_id IS NULL OR user_id = :uid)
        """), {"id": notification_id, "uid": current_user.id})
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a notification."""
    try:
        db.execute(text("""
            DELETE FROM sys_notifications
            WHERE id = :id AND (user_id IS NULL OR user_id = :uid)
        """), {"id": notification_id, "uid": current_user.id})
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ── SSE streaming endpoint ────────────────────────────────────────────────────

@router.get("/stream")
async def notification_stream(
    request: Request,
    current_user=Depends(get_current_user_sse),
):
    """
    Server-Sent Events stream — push real-time notifications to the browser.
    Connects immediately and streams events as they are broadcast.

    Clients reconnect automatically via EventSource (browser) or custom hook.
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    user_id = current_user.id

    async with _sse_lock:
        _sse_clients.setdefault(user_id, set()).add(queue)

    async def event_generator():
        yield f"data: {json.dumps({'type': 'connected', 'ts': datetime.now(timezone.utc).isoformat()})}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30)
                    # Strip internal routing key before sending to client
                    clean = {k: v for k, v in payload.items() if not k.startswith("_")}
                    yield f"data: {json.dumps(clean)}\n\n"
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
        finally:
            async with _sse_lock:
                if user_id in _sse_clients:
                    _sse_clients[user_id].discard(queue)
                    if not _sse_clients[user_id]:
                        del _sse_clients[user_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/broadcast")
async def broadcast_manual(
    payload: dict,
    current_user=Depends(get_current_user),
):
    """Admin: manually broadcast a notification to all connected clients."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Admin only")
    payload["ts"] = datetime.now(timezone.utc).isoformat()
    payload["type"] = payload.get("type", "manual")
    await broadcast_notification(payload)
    total_clients = sum(len(qs) for qs in _sse_clients.values())
    return {"broadcast": True, "clients": total_clients}
