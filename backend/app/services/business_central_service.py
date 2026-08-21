"""
Microsoft Business Central Integration Service
───────────────────────────────────────────────
Pushes daily attendance (as timesheet hours) from iclock_transaction into
Business Central's Time Registration Entries so HR/Finance can process
payroll and project cost allocation.

Authentication: OAuth 2.0 Client Credentials (Azure AD / Microsoft Entra ID)
  Requires an App Registration in the organisation's Azure tenant with the
  Dynamics 365 Business Central API permission granted.

BC API base:
  https://api.businesscentral.dynamics.com/v2.0/{tenant_id}/{environment}/api/v2.0/

Key endpoints used:
  GET  /companies                                   — discover company ID
  GET  /companies({id})/employees?$filter=...       — verify employee exists
  POST /companies({id})/timeRegistrationEntries     — post attendance hours

Payload per employee per day:
  {
    "employeeNumber": "EMP001",
    "date":           "2026-06-06",
    "quantity":       8.72,          // hours worked (total_minutes / 60)
    "status":         "Open"
  }
"""

import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

import asyncio

logger = logging.getLogger(__name__)

# ── Shared httpx client — reused across all calls to avoid per-request TCP overhead ──
_http_client: Optional[httpx.AsyncClient] = None
_http_client_lock = asyncio.Lock()


async def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        async with _http_client_lock:
            if _http_client is None or _http_client.is_closed:
                _http_client = httpx.AsyncClient(timeout=30)
    return _http_client


async def close_http_client() -> None:
    """Close the shared httpx client on app shutdown. Called from main.py lifespan."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


# ── Token cache (in-process; valid for 1 hour) ────────────────────────────────
_token_cache: Dict[str, Any] = {}   # keyed by tenant_id
_token_lock = asyncio.Lock()        # prevent concurrent token refreshes
_TOKEN_GRACE = 60                   # refresh 60s before expiry


def _token_cache_key(cfg: Dict) -> str:
    return f"{cfg['tenant_id']}:{cfg['client_id']}"


def _token_is_valid(cfg: Dict) -> bool:
    key   = _token_cache_key(cfg)
    entry = _token_cache.get(key)
    return bool(entry and entry["expires_at"] - time.time() > _TOKEN_GRACE)


def _get_cached_token(cfg: Dict) -> Optional[str]:
    key = _token_cache_key(cfg)
    entry = _token_cache.get(key)
    return entry["access_token"] if entry else None


async def _fetch_token(cfg: Dict) -> Tuple[Optional[str], Optional[str]]:
    """Obtain OAuth 2.0 access token via client_credentials grant."""
    url = f"https://login.microsoftonline.com/{cfg['tenant_id']}/oauth2/v2.0/token"
    data = {
        "grant_type":    "client_credentials",
        "client_id":     cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "scope":         "https://api.businesscentral.dynamics.com/.default",
    }
    try:
        client = await _get_http_client()
        resp = await client.post(url, data=data, timeout=15)
        if resp.status_code != 200:
            err = resp.json().get("error_description") or resp.text[:200]
            return None, f"Token request failed ({resp.status_code}): {err}"
        body   = resp.json()
        token  = body["access_token"]
        expiry = time.time() + body.get("expires_in", 3600)
        _token_cache[_token_cache_key(cfg)] = {"access_token": token, "expires_at": expiry}
        return token, None
    except httpx.ConnectError:
        return None, "Cannot reach login.microsoftonline.com — check internet/firewall"
    except Exception as e:
        return None, str(e)


async def _get_token(cfg: Dict) -> Tuple[Optional[str], Optional[str]]:
    if _token_is_valid(cfg):
        return _get_cached_token(cfg), None
    # Serialize token refresh to avoid concurrent duplicate requests
    async with _token_lock:
        if _token_is_valid(cfg):  # re-check under lock
            return _get_cached_token(cfg), None
        return await _fetch_token(cfg)


# ── Connector options (real BC surfaces — standard API / custom API / OData V4) ─
# These map 1:1 to documented Business Central URL structures; nothing is invented.
# Defaults are the standard v2.0 API and its real timeRegistrationEntries fields, so
# an unconfigured `options` behaves exactly as before.
#   Standard API:  .../{env}/api/v2.0/companies({id})/timeRegistrationEntries
#   Custom API:    .../{env}/api/{publisher}/{group}/{version}/companies({id})/{entity}
#   OData V4 page: .../{env}/ODataV4/Company('{name}')/{PageName}
_BC_DEFAULT_OPTIONS: Dict[str, Any] = {
    "api_route":     "api/v2.0",                    # standard; custom: "api/{publisher}/{group}/{version}"; OData: "ODataV4"
    "company_path":  "companies({company_id})",     # standard/custom; OData: "Company('{company_name}')"
    "target_entity": "timeRegistrationEntries",     # standard time entity; e.g. "journalLines" (GL) or a custom API entity
    "field_map":     {},                            # rename output keys ("" ⇒ omit); default = real standard fields
    "static_fields": {},                            # constants a target requires, e.g. {"unitOfMeasureCode":"HOUR","jobNumber":"..."}
    "internal_prefix": "_",                          # local-only fields stripped before POST
}


def _merge_bc_options(raw: Optional[Dict]) -> Dict[str, Any]:
    opts = dict(_BC_DEFAULT_OPTIONS)
    if isinstance(raw, dict):
        opts.update({k: v for k, v in raw.items() if v is not None})
    return opts


def _bc_root(cfg: Dict) -> str:
    """`https://api.businesscentral.dynamics.com/v2.0/{tenant}/{env}` — the shared root."""
    env = cfg.get("environment") or "Production"
    return f"https://api.businesscentral.dynamics.com/v2.0/{cfg['tenant_id']}/{env}"


def _bc_base(cfg: Dict) -> str:
    """Data-API base using the configured route (standard v2.0, a custom API, or OData V4)."""
    route = (cfg.get("options") or _BC_DEFAULT_OPTIONS).get("api_route", "api/v2.0")
    return f"{_bc_root(cfg)}/{route}"


def _bc_base_standard(cfg: Dict) -> str:
    """Always the standard v2.0 API — used for company discovery, which is a standard
    entity even when data is posted to a custom/OData endpoint."""
    return f"{_bc_root(cfg)}/api/v2.0"


def _bc_company_path(cfg: Dict) -> str:
    opts = cfg.get("options") or _BC_DEFAULT_OPTIONS
    tmpl = opts.get("company_path", "companies({company_id})")
    return tmpl.format(company_id=cfg.get("company_id") or "", company_name=cfg.get("company_name") or "")


def _map_bc_payload(entry: Dict, opts: Dict) -> Dict:
    """Strip local-only fields, rename to the target's real field names, add any
    required static fields. Renaming a field to "" omits it."""
    prefix = opts.get("internal_prefix", "_")
    fm = opts.get("field_map") or {}
    out: Dict[str, Any] = {}
    for k, v in entry.items():
        if k.startswith(prefix):
            continue
        key = fm.get(k, k)
        if key != "":
            out[key] = v
    out.update(opts.get("static_fields") or {})
    return out


# ── Config helpers ────────────────────────────────────────────────────────────

def _ensure_bc_tables(db: Session) -> None:
    """Create BC integration tables if they don't exist (idempotent)."""
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS bc_integration_config (
                id             SERIAL PRIMARY KEY,
                tenant_id      VARCHAR(200),
                client_id      VARCHAR(200),
                client_secret  VARCHAR(500),
                environment    VARCHAR(50)  DEFAULT 'Production',
                company_id     VARCHAR(100),
                company_name   VARCHAR(200),
                is_enabled     BOOLEAN      DEFAULT FALSE,
                sync_time      VARCHAR(10)  DEFAULT '01:00',
                options        JSONB,
                updated_at     TIMESTAMPTZ  DEFAULT NOW()
            )
        """))
        # Upgrade path for existing installs.
        #
        # CRITICAL: only run ALTER TABLE when the column is actually absent.
        # `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` still takes an ACCESS
        # EXCLUSIVE lock even when the column already exists, and once that lock
        # request queues behind any open transaction, every later reader of the
        # table queues behind it too — which stalls the whole API, not just BC.
        # The information_schema probe below takes only ACCESS SHARE, so on an
        # already-migrated database this costs nothing and locks nothing.
        # (Same failure and same remedy as _ensure_totp_column in api/mfa.py.)
        has_options = db.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'bc_integration_config' AND column_name = 'options'"
        )).fetchone()
        if not has_options:
            db.execute(text("SET LOCAL lock_timeout = '3s'"))
            db.execute(text("ALTER TABLE bc_integration_config ADD COLUMN IF NOT EXISTS options JSONB"))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS bc_sync_log (
                id              SERIAL PRIMARY KEY,
                sync_date       DATE,
                triggered_by    VARCHAR(50),
                status          VARCHAR(20),
                records_built   INTEGER DEFAULT 0,
                records_sent    INTEGER DEFAULT 0,
                records_failed  INTEGER DEFAULT 0,
                message         VARCHAR(500),
                created_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Could not ensure BC tables: {e}")


def get_bc_config(db: Session) -> Optional[Dict[str, Any]]:
    _ensure_bc_tables(db)
    try:
        row = db.execute(text(
            "SELECT tenant_id, client_id, client_secret, environment, "
            "       company_id, company_name, is_enabled, sync_time, options "
            "FROM bc_integration_config LIMIT 1"
        )).fetchone()
        if not row or not row[0] or not row[1] or not row[2]:
            return None
        from ..core.crypto import decrypt_secret
        return {
            "tenant_id":     row[0],
            "client_id":     row[1],
            "client_secret": decrypt_secret(row[2]),  # transparently handles legacy plaintext
            "environment":   row[3] or "Production",
            "company_id":    row[4],
            "company_name":  row[5],
            "is_enabled":    bool(row[6]),
            "sync_time":     row[7] or "01:00",
            "options":       _merge_bc_options(row[8] if len(row) > 8 else None),
        }
    except Exception as e:
        logger.warning(f"bc_integration_config read error: {e}")
        return None


# ── Company discovery ─────────────────────────────────────────────────────────

async def fetch_companies(cfg: Dict) -> Tuple[List[Dict], Optional[str]]:
    """Return list of BC companies available with the given credentials."""
    token, err = await _get_token(cfg)
    if err:
        return [], err
    # Company discovery always uses the standard v2.0 API (a standard entity),
    # even when data is posted to a custom/OData endpoint.
    url = f"{_bc_base_standard(cfg)}/companies"
    try:
        client = await _get_http_client()
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if resp.status_code == 200:
            companies = [
                {"id": c["id"], "name": c["displayName"]}
                for c in resp.json().get("value", [])
            ]
            return companies, None
        return [], f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return [], str(e)


# ── Core sync logic ───────────────────────────────────────────────────────────

def _build_time_entries(db: Session, sync_date: date) -> List[Dict]:
    """
    Build BC time-registration entries for sync_date — one per employee.

    Source of truth is the COMPUTED attendance in att_report (via the shared
    attendance_export.build_daily_attendance), NOT raw iclock_transaction. This fixes
    the same defects as the SeamlessHR exporter: access-control door swipes no longer
    inflate hours, night/cross-midnight shifts land on the correct business day, and
    `quantity` is the shift/break-aware computed work time (not a raw in→out span).

    Each entry carries an idempotency key so a re-run cannot double-post to finance.
    """
    from .attendance_export import build_daily_attendance

    entries = []
    for c in build_daily_attendance(db, sync_date):
        # Authoritative computed work time → hours (include overtime in the total).
        total_minutes = c["work_minutes"] + c["overtime_minutes"]
        if total_minutes <= 0:
            continue
        hours = round(total_minutes / 60, 2)
        entries.append({
            "employeeNumber":  c["emp_code"],
            "date":            str(c["att_date"]),
            "quantity":        hours,
            "status":          "Open",
            # Internal only (underscore-prefixed → stripped before POST). Business Central's
            # OData API has no idempotencyKey property and returns 400 for unknown fields.
            "_idempotency_key": c["idempotency_key"],
            "_clock_in":       c["check_in"].isoformat() if c["check_in"] else None,
            "_clock_out":      c["check_out"].isoformat() if c["check_out"] else None,
        })
    return entries


async def push_attendance(
    db: Session,
    sync_date: Optional[date] = None,
    triggered_by: str = "scheduler",
    force: bool = False,
    allow_today: bool = False,
) -> Dict[str, Any]:
    """
    Build time entries for sync_date (defaults to yesterday) and POST to BC.

    Idempotency: each (employee, date) is posted at most once — already-sent records are
    skipped so a re-run/retry/manual+scheduler overlap cannot double-post to finance.
      • force=True       — re-send even if already sent (admin correction; may duplicate).
      • allow_today=True — permit syncing a not-yet-finalized day (today/future).
    """
    if sync_date is None:
        sync_date = date.today() - timedelta(days=1)

    result = {
        "sync_date":      str(sync_date),
        "triggered_by":   triggered_by,
        "started_at":     datetime.now(timezone.utc).isoformat(),
        "status":         "failed",
        "records_built":  0,
        "records_sent":   0,
        "records_failed": 0,
        "message":        "",
    }

    cfg = get_bc_config(db)
    if not cfg:
        result["message"] = "Business Central not configured — add credentials in Settings → BC Integration"
        _log_sync(db, result)
        return result

    if not cfg["is_enabled"]:
        result["status"]  = "skipped"
        result["message"] = "Integration is disabled"
        _log_sync(db, result)
        return result

    if not cfg.get("company_id"):
        result["message"] = "No BC company selected — open Settings → BC Integration and select a company"
        _log_sync(db, result)
        return result

    # Don't post a not-yet-finalized day (today/future) to finance unless explicitly allowed.
    if not allow_today and not force and sync_date >= date.today():
        result["status"]  = "skipped"
        result["message"] = f"{sync_date} is not finalized yet — payroll syncs after the day closes"
        _log_sync(db, result)
        return result

    entries = _build_time_entries(db, sync_date)
    result["records_built"] = len(entries)

    if not entries:
        result["status"]  = "success"
        result["message"] = f"No attendance records found for {sync_date}"
        _log_sync(db, result)
        return result

    # Idempotency: drop employee-days already sent for this date (unless force re-send).
    if not force:
        from .attendance_export import already_synced_codes
        done = already_synced_codes(db, "bc_synced_records", sync_date)
        if done:
            entries = [e for e in entries if e["employeeNumber"] not in done]
        if not entries:
            result["status"]  = "success"
            result["message"] = f"All records for {sync_date} already synced — nothing new to send"
            _log_sync(db, result)
            return result

    token, err = await _get_token(cfg)
    if err:
        result["message"] = f"Authentication failed: {err}"
        _log_sync(db, result)
        return result

    opts    = cfg.get("options") or _BC_DEFAULT_OPTIONS
    url     = f"{_bc_base(cfg)}/{_bc_company_path(cfg)}/{opts['target_entity']}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    sent = failed = 0
    sent_codes = []
    client = await _get_http_client()
    for entry in entries:
        # Strip local-only fields, rename to the target's real fields, add static fields.
        payload = _map_bc_payload(entry, opts)
        try:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in (200, 201, 204):
                sent += 1
                sent_codes.append(entry["employeeNumber"])
            else:
                logger.warning(
                    "BC rejected entry for %s: HTTP %s — %s",
                    entry.get("employeeNumber"), resp.status_code, resp.text[:200],
                )
                failed += 1
        except httpx.RequestError as e:
            logger.error("BC request error for %s: %s", entry.get("employeeNumber"), e)
            failed += 1

    # Record successfully-sent employee-days so a re-run cannot double-post them.
    if sent_codes:
        from .attendance_export import mark_synced
        mark_synced(db, "bc_synced_records", sync_date, sent_codes)

    result["records_sent"]   = sent
    result["records_failed"] = failed
    result["status"] = "success" if failed == 0 else ("partial" if sent > 0 else "failed")
    result["message"] = (
        f"Sent {sent}/{len(entries)} time entries to Business Central for {sync_date}"
        + (f" ({failed} failed)" if failed else "")
    )
    _log_sync(db, result)
    logger.info(f"Business Central sync [{result['status']}]: {result['message']}")
    return result


async def test_connection(cfg: Dict) -> Dict[str, Any]:
    """Verify Azure AD credentials and BC API access."""
    token, err = await _get_token(cfg)
    if err:
        return {"success": False, "message": err}

    companies, err = await fetch_companies(cfg)
    if err:
        return {"success": False, "message": f"Authenticated but cannot reach BC API: {err}"}

    if not companies:
        return {"success": True, "message": "Connected — no companies found (check API permissions)", "companies": []}

    return {
        "success":   True,
        "message":   f"Connected — {len(companies)} company/companies found",
        "companies": companies,
    }


# ── Sync log ──────────────────────────────────────────────────────────────────

def _log_sync(db: Session, result: Dict):
    try:
        db.execute(text("""
            INSERT INTO bc_sync_log
              (sync_date, triggered_by, status, records_built,
               records_sent, records_failed, message, created_at)
            VALUES
              (:sync_date, :triggered_by, :status, :records_built,
               :records_sent, :records_failed, :message, NOW())
        """), {
            "sync_date":      result["sync_date"],
            "triggered_by":   result["triggered_by"],
            "status":         result["status"],
            "records_built":  result["records_built"],
            "records_sent":   result["records_sent"],
            "records_failed": result["records_failed"],
            "message":        result["message"][:500],
        })
        db.commit()
    except Exception as e:
        logger.warning(f"Could not write bc_sync_log: {e}")
        db.rollback()
