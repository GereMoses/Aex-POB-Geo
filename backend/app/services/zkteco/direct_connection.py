"""
ZKTeco Direct IP Connection Service

Connects to ZKTeco readers (including Huros H1) via TCP port 4370 using the ZKLib
protocol. Operations are synchronous under the hood but wrapped for async use via
asyncio's thread-pool executor so the event loop is never blocked.
"""

import asyncio
import logging
from datetime import datetime
from functools import partial
from typing import Any, Dict, List, Optional

from zk import ZK, const

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _run_sync(func, *args, **kwargs):
    """Execute *func* in the default executor so it doesn't block the loop."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, partial(func, *args, **kwargs))


def _make_zk(ip: str, port: int = 4370, timeout: int = 10, password: int = 0) -> ZK:
    return ZK(
        ip,
        port=port,
        timeout=timeout,
        password=password,
        force_udp=False,
        ommit_ping=True,   # skip pyzk's pre-connect ICMP check; TCP handshake is the real test
    )


# --------------------------------------------------------------------------- #
# Core service                                                                 #
# --------------------------------------------------------------------------- #

class ZKTecoDirectService:
    """
    Direct TCP connection to a ZKTeco reader.

    Every public method is a coroutine that runs the blocking ZK SDK call in
    a thread so FastAPI's async event loop stays responsive.
    """

    # ------------------------------------------------------------------ #
    # Connection test                                                      #
    # ------------------------------------------------------------------ #

    async def test_connection(
        self, ip: str, port: int = 4370, timeout: int = 5, password: int = 0
    ) -> Dict[str, Any]:
        """Open and immediately close a connection; return basic device info."""

        def _connect():
            zk = _make_zk(ip, port, timeout, password)
            conn = zk.connect()
            try:
                info = {
                    "connected": True,
                    "ip": ip,
                    "port": port,
                    "serial_number": conn.get_serialnumber(),
                    "firmware": conn.get_firmware_version(),
                    "device_name": conn.get_device_name(),
                    "platform": conn.get_platform(),
                    "mac": conn.get_mac(),
                    "fp_count": conn.get_fp_version(),
                    "user_count": None,
                    "log_count": None,
                }
                try:
                    info["user_count"] = conn.get_users_count()
                    info["log_count"] = conn.get_attendance_count()
                except Exception:
                    pass
                return info
            finally:
                conn.disconnect()

        try:
            result = await _run_sync(_connect)
            return {"success": True, **result}
        except Exception as exc:
            logger.warning("ZK connect failed %s:%s — %s", ip, port, exc)
            return {"success": False, "connected": False, "ip": ip, "port": port, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Users                                                                #
    # ------------------------------------------------------------------ #

    async def get_users(
        self, ip: str, port: int = 4370, password: int = 0
    ) -> Dict[str, Any]:
        """Return all user records stored on the device."""

        def _get():
            zk = _make_zk(ip, port)
            conn = zk.connect()
            try:
                users = conn.get_users()
                return [
                    {
                        "uid": u.uid,
                        "user_id": u.user_id,
                        "name": u.name,
                        "privilege": u.privilege,
                        "card": u.card,
                        "group_id": u.group_id,
                    }
                    for u in users
                ]
            finally:
                conn.disconnect()

        try:
            users = await _run_sync(_get)
            return {"success": True, "users": users, "count": len(users)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def set_user(
        self,
        ip: str,
        uid: int,
        name: str,
        privilege: int = const.USER_DEFAULT,
        password: str = "",
        group_id: str = "",
        user_id: str = "",
        card: int = 0,
        port: int = 4370,
        device_password: int = 0,
    ) -> Dict[str, Any]:
        """Create or update a user on the device."""

        def _set():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.set_user(
                    uid=uid,
                    name=name,
                    privilege=privilege,
                    password=password,
                    group_id=group_id,
                    user_id=user_id,
                    card=card,
                )
                return True
            finally:
                conn.disconnect()

        try:
            await _run_sync(_set)
            return {"success": True, "uid": uid, "name": name}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def delete_user(
        self, ip: str, uid: int, port: int = 4370, device_password: int = 0
    ) -> Dict[str, Any]:
        """Delete a user from the device by uid."""

        def _del():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.delete_user(uid=uid)
                return True
            finally:
                conn.disconnect()

        try:
            await _run_sync(_del)
            return {"success": True, "uid": uid}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Attendance / Access logs                                             #
    # ------------------------------------------------------------------ #

    async def get_attendance(
        self,
        ip: str,
        port: int = 4370,
        device_password: int = 0,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Pull all attendance records from device.
        If *since* is provided, only records with timestamp >= since are returned.
        """

        def _get():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                records = conn.get_attendance()
                result = []
                for r in records:
                    if since and r.timestamp < since:
                        continue
                    result.append(
                        {
                            "uid": r.uid,
                            "user_id": r.user_id,
                            "timestamp": r.timestamp.isoformat(),
                            "status": r.status,
                            "punch": r.punch,
                        }
                    )
                return result
            finally:
                conn.disconnect()

        try:
            records = await _run_sync(_get)
            return {"success": True, "records": records, "count": len(records)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def clear_attendance(
        self, ip: str, port: int = 4370, device_password: int = 0
    ) -> Dict[str, Any]:
        """Erase all attendance records stored on the device."""

        def _clear():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.clear_attendance()
                return True
            finally:
                conn.disconnect()

        try:
            await _run_sync(_clear)
            return {"success": True, "message": "Attendance log cleared"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Device control                                                       #
    # ------------------------------------------------------------------ #

    async def get_time(
        self,
        ip: str,
        port: int = 4370,
        device_password: int = 0,
    ) -> Dict[str, Any]:
        """Read the device's current clock without changing it."""
        def _get():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                return conn.get_time()
            finally:
                conn.disconnect()

        try:
            device_time = await _run_sync(_get)
            return {
                "success": True,
                "device_time": str(device_time),
                "server_time": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def sync_time(
        self,
        ip: str,
        port: int = 4370,
        device_password: int = 0,
        target_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Set device clock to *target_time* (defaults to current UTC time)."""
        dt = target_time or datetime.utcnow()

        def _sync():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.set_time(dt)
                return conn.get_time()
            finally:
                conn.disconnect()

        try:
            device_time = await _run_sync(_sync)
            return {
                "success": True,
                "set_to": dt.isoformat(),
                "device_reports": str(device_time),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def restart_device(
        self, ip: str, port: int = 4370, device_password: int = 0
    ) -> Dict[str, Any]:
        """Restart the device remotely."""

        def _restart():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.restart()
                return True
            finally:
                try:
                    conn.disconnect()
                except Exception:
                    pass  # device may not respond after restart command

        try:
            await _run_sync(_restart)
            return {"success": True, "message": f"Restart command sent to {ip}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def open_door(
        self,
        ip: str,
        port: int = 4370,
        device_password: int = 0,
        hold_seconds: int = 5,
    ) -> Dict[str, Any]:
        """
        Send door unlock command to the device.
        *hold_seconds* controls how long the relay stays open.
        Supported on access-control terminals such as the Huros H1.
        """

        def _unlock():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.unlock(time=hold_seconds)
                return True
            finally:
                conn.disconnect()

        try:
            await _run_sync(_unlock)
            return {
                "success": True,
                "message": f"Door opened for {hold_seconds}s on {ip}",
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def disable_device(
        self, ip: str, port: int = 4370, device_password: int = 0
    ) -> Dict[str, Any]:
        """Put device into disabled (lockdown) state — no local biometric auth."""

        def _disable():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.disable_device()
                return True
            finally:
                conn.disconnect()

        try:
            await _run_sync(_disable)
            return {"success": True, "message": f"Device {ip} disabled"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def enable_device(
        self, ip: str, port: int = 4370, device_password: int = 0
    ) -> Dict[str, Any]:
        """Re-enable a previously disabled device."""

        def _enable():
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            try:
                conn.enable_device()
                return True
            finally:
                conn.disconnect()

        try:
            await _run_sync(_enable)
            return {"success": True, "message": f"Device {ip} enabled"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Bulk personnel sync                                                  #
    # ------------------------------------------------------------------ #

    async def sync_personnel_from_db(
        self,
        ip: str,
        port: int = 4370,
        device_password: int = 0,
        personnel_ids: Optional[List[int]] = None,
        db=None,
    ) -> Dict[str, Any]:
        """
        Read personnel records from the local DB and push them to the device.

        Each person is written as a ZK user:
          uid        = personnel.id (int)
          user_id    = personnel.badge_id (string, shown on device)
          name       = personnel.full_name (truncated to 24 chars)
          privilege  = USER_DEFAULT (admin flag only for superusers)
          card       = 0 (card enrollment handled separately)
        """
        if db is None:
            return {"success": False, "error": "DB session required"}

        from ...models.personnel import Personnel

        # Filter on is_active, the boolean "is this person employed" flag.
        #
        # This previously compared `status == "active"` — but status is an enum of
        # ACTIVE / ONSHORE / OFFSHORE / IN_TRANSIT etc., stored UPPERCASE, and it
        # describes WHERE someone is, not whether they are employed. The lowercase
        # literal matched nothing, so a sync pushed zero users to the reader and
        # still reported success ("No active personnel to sync") — the device
        # silently ended up with nobody on it.
        query = db.query(Personnel).filter(Personnel.is_active.is_(True))
        if personnel_ids:
            query = query.filter(Personnel.id.in_(personnel_ids))
        people = query.all()

        if not people:
            return {"success": True, "synced": 0, "message": "No active personnel to sync"}

        errors: List[str] = []
        synced = 0

        def _push_all():
            nonlocal synced
            zk = _make_zk(ip, port, password=device_password)
            conn = zk.connect()
            conn.disable_device()
            try:
                for p in people:
                    try:
                        conn.set_user(
                            uid=p.id,
                            name=(p.full_name or p.badge_id or p.emp_code)[:24],
                            privilege=const.USER_DEFAULT,
                            password="",
                            group_id="",
                            user_id=str(p.badge_id or p.emp_code),
                            card=int(p.card_number) if p.card_number else 0,
                        )
                        synced += 1
                    except Exception as e:
                        errors.append(f"{p.badge_id}: {e}")
            finally:
                conn.enable_device()
                conn.disconnect()

        try:
            await _run_sync(_push_all)
            return {
                "success": True,
                "synced": synced,
                "errors": errors,
                "total": len(people),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "synced": synced}


    # ------------------------------------------------------------------ #
    # Biometric enrollment                                                #
    # ------------------------------------------------------------------ #

    async def get_templates_from_device(
        self, ip: str, port: int = 4370, password: int = 0
    ) -> Dict[str, Any]:
        """Pull ALL fingerprint/face templates currently stored on the device."""
        templates = []
        errors = []

        def _pull():
            zk = _make_zk(ip, port, password=password)
            conn = zk.connect()
            try:
                raw = conn.get_templates()
                for t in raw:
                    templates.append({
                        "uid": t.uid,
                        "fid": t.fid,          # finger slot: 0-9=finger, 12/15=face
                        "valid": t.valid,
                        "mark": getattr(t, "mark", 0),
                        "template": t.template, # raw bytes
                    })
            except Exception as exc:
                errors.append(str(exc))
            finally:
                conn.disconnect()

        try:
            await _run_sync(_pull)
            return {"success": True, "templates": templates, "count": len(templates), "errors": errors}
        except Exception as exc:
            return {"success": False, "error": str(exc), "templates": [], "count": 0}

    async def get_users_from_device(
        self, ip: str, port: int = 4370, password: int = 0
    ) -> Dict[str, Any]:
        """Pull user records from device, returning uid→user_id (PIN/emp_code) mapping."""
        users = []

        def _pull():
            zk = _make_zk(ip, port, password=password)
            conn = zk.connect()
            try:
                for u in conn.get_users():
                    users.append({
                        "uid": u.uid,
                        "user_id": u.user_id,     # emp_code / PIN
                        "name": u.name,
                        "card": u.card,
                        "privilege": u.privilege,
                    })
            finally:
                conn.disconnect()

        try:
            await _run_sync(_pull)
            return {"success": True, "users": users}
        except Exception as exc:
            return {"success": False, "error": str(exc), "users": []}

    async def cancel_enrollment(
        self, ip: str, port: int = 4370, password: int = 0
    ) -> Dict[str, Any]:
        """Cancel any pending capture/enrollment on the device and re-enable it."""
        def _cancel():
            zk = _make_zk(ip, port, timeout=8, password=password)
            conn = zk.connect()
            try:
                try:
                    conn.cancel_capture()
                except Exception:
                    pass  # device may not be in capture mode; proceed to enable
                conn.enable_device()
            finally:
                conn.disconnect()

        try:
            await _run_sync(_cancel)
            return {"success": True, "message": "Enrollment cancelled, device re-enabled"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def enroll_and_capture(
        self, ip: str, port: int = 4370, password: int = 0,
        uid: int = 0, user_id: str = "", finger_id: int = 0, timeout: int = 90
    ) -> Dict[str, Any]:
        """
        Full blocking enrollment: keep the TCP connection open while the employee
        presses their finger 3 times on the device scanner.  Returns the captured
        template on success.  Must NOT be cancelled mid-way — disconnecting while
        the device is in capture mode leaves it stuck.
        """
        import base64
        result: Dict[str, Any] = {}

        def _enroll():
            # timeout on the ZK object controls the initial connect only;
            # pyzk internally sets the socket to 60 s during capture.
            zk = _make_zk(ip, port, timeout=10, password=password)
            conn = zk.connect()
            try:
                conn.enroll_user(uid=uid, temp_id=finger_id, user_id=user_id)
                # After 3 successful presses the template is stored on device.
                # Try to read it back immediately over the same connection.
                try:
                    tpl = conn.get_user_template(uid=uid, finger_id=finger_id)
                    if tpl and tpl.template:
                        result["template_b64"] = base64.b64encode(tpl.template).decode()
                        result["template_size"] = len(tpl.template)
                        result["captured"] = True
                    else:
                        result["captured"] = False
                except Exception:
                    result["captured"] = False
            finally:
                conn.disconnect()

        try:
            await _run_sync(_enroll)
            return {"success": True, **result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


# Singleton
zkteco_direct = ZKTecoDirectService()
