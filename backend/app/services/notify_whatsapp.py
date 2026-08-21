"""
Shared, env-configured WhatsApp sender.

Provider is chosen by WHATSAPP_PROVIDER (termii | twilio | generic); if unset it
falls back to SMS_PROVIDER (so a single Termii account powers both), then to
auto-detection.

  Termii (Nigeria — recommended):
    WHATSAPP_PROVIDER=termii   (or just SMS_PROVIDER=termii)
    SMS_API_KEY                Termii API key (shared with SMS)
    WHATSAPP_SENDER_ID         approved WhatsApp sender (falls back to SMS_SENDER_ID)
    TERMII_BASE_URL            default https://api.ng.termii.com
    Delivered via Termii's send endpoint with channel="whatsapp". The recipient
    number must be WhatsApp-enabled; template pre-approval may be required by Meta.

  Twilio WhatsApp:
    TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / WHATSAPP_FROM (e.g. whatsapp:+14155238886)

  Generic HTTP gateway:
    WHATSAPP_API_URL           POST endpoint; body {"api_key","to","message"}
    WHATSAPP_API_KEY

Never raises — returns {"sent": N, "failed": [...], "error"?: str}. The HTTP
calls block, so async callers must run these via asyncio.to_thread().
"""

from __future__ import annotations

import logging
import os
import time as _time
from typing import Dict, Iterable, List, Union

from .notify_sms import normalize_msisdn, TERMII_DEFAULT_BASE

logger = logging.getLogger(__name__)


def _provider() -> str:
    """Which WhatsApp backend is usable, or '' when WhatsApp is off."""
    explicit = os.getenv("WHATSAPP_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    # A Termii account does both — inherit the SMS provider when it's Termii.
    if os.getenv("SMS_PROVIDER", "").strip().lower() == "termii":
        return "termii"
    if os.getenv("WHATSAPP_API_URL"):
        return "generic"
    if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("WHATSAPP_FROM"):
        return "twilio"
    return ""


def whatsapp_configured() -> bool:
    """True if the selected WhatsApp provider has the creds it needs to send."""
    provider = _provider()
    if provider == "termii":
        return bool(os.getenv("SMS_API_KEY"))
    if provider == "twilio":
        return bool(
            os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")
            and os.getenv("WHATSAPP_FROM")
        )
    if provider == "generic":
        return bool(os.getenv("WHATSAPP_API_URL"))
    return False


def _clean(to: Union[str, Iterable[str]]) -> List[str]:
    recipients: List[str] = [to] if isinstance(to, str) else [r for r in to if r]
    return [r.strip() for r in recipients if r and r.strip()]


def send_whatsapp(to: Union[str, Iterable[str]], message: str) -> Dict[str, object]:
    """Send one WhatsApp message to one or many numbers via env-configured provider.

    Returns {"sent": N, "failed": [num, ...], "error"?: str}. Fails soft.
    """
    recipients = _clean(to)
    if not recipients:
        return {"sent": 0, "failed": [], "error": "no recipients with a phone number"}

    provider = _provider()
    if not whatsapp_configured():
        return {
            "sent": 0,
            "failed": recipients,
            "error": "WhatsApp not configured — set WHATSAPP_PROVIDER (or SMS_PROVIDER=termii) "
                     "and its credentials",
        }

    if provider == "termii":
        return _send_termii(recipients, message)
    if provider == "twilio":
        return _send_twilio(recipients, message)
    return _send_generic(recipients, message)


def _finish(sent: int, failed: List[str], tag: str) -> Dict[str, object]:
    logger.info("notify_whatsapp(%s): sent %d, failed %d", tag, sent, len(failed))
    out: Dict[str, object] = {"sent": sent, "failed": failed}
    if sent == 0 and failed:
        out["error"] = f"all sends failed via {tag} — check credentials/sender and gateway"
    return out


def _send_termii(recipients: List[str], message: str) -> Dict[str, object]:
    import requests

    base = os.getenv("TERMII_BASE_URL", TERMII_DEFAULT_BASE).rstrip("/")
    url = f"{base}/api/sms/send"
    api_key = os.getenv("SMS_API_KEY", "")
    sender = os.getenv("WHATSAPP_SENDER_ID") or os.getenv("SMS_SENDER_ID") or "N-Alert"

    sent, failed = 0, []
    for number in recipients:
        try:
            payload = {
                "to": normalize_msisdn(number),
                "from": sender,
                "sms": message,
                "type": "plain",
                "channel": "whatsapp",
                "api_key": api_key,
            }
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json() if resp.content else {}
            if data.get("message_id"):
                sent += 1
            else:
                failed.append(number)
                logger.warning("Termii WhatsApp to %s returned no message_id: %s", number, data)
        except Exception as exc:  # noqa: BLE001
            failed.append(number)
            logger.warning("Termii WhatsApp to %s failed: %s", number, exc)
    return _finish(sent, failed, "termii")


def _send_generic(recipients: List[str], message: str) -> Dict[str, object]:
    """POST to any HTTP WhatsApp gateway, self-hosted included.

    The body shape was fixed (api_key in the body, fields to/message), which no
    self-hosted gateway actually uses — Evolution API wants a Bearer/apikey
    header and {"number", "text"}, WAHA wants {"chatId", "text", "session"}. So
    the field names and auth header are configurable, defaults unchanged:

        WHATSAPP_API_URL          POST endpoint
        WHATSAPP_API_KEY          credential
        WHATSAPP_API_KEY_HEADER   send the key as this HEADER (e.g. "apikey")
        WHATSAPP_API_HEADERS      extra headers as JSON
        WHATSAPP_FIELD_TO         recipient field   (default "to")
        WHATSAPP_FIELD_MESSAGE    message field     (default "message")
        WHATSAPP_EXTRA_BODY       constant body fields as JSON (e.g. session name)

    NOTE: a self-hosted gateway drives an UNOFFICIAL WhatsApp client. It violates
    Meta's terms and such numbers are commonly banned within weeks. Do not make
    it the only route for an emergency alert — keep email or SMS alongside it.
    """
    import json as _json
    import requests

    url = os.getenv("WHATSAPP_API_URL", "")
    api_key = os.getenv("WHATSAPP_API_KEY", "")
    key_header = os.getenv("WHATSAPP_API_KEY_HEADER", "").strip()
    f_to = os.getenv("WHATSAPP_FIELD_TO", "to")
    f_msg = os.getenv("WHATSAPP_FIELD_MESSAGE", "message")

    headers: Dict[str, str] = {}
    try:
        headers.update(_json.loads(os.getenv("WHATSAPP_API_HEADERS", "") or "{}"))
    except Exception:
        logger.warning("WHATSAPP_API_HEADERS is not valid JSON — ignoring it")
    if key_header and api_key:
        headers[key_header] = api_key

    extra: Dict[str, object] = {}
    try:
        extra.update(_json.loads(os.getenv("WHATSAPP_EXTRA_BODY", "") or "{}"))
    except Exception:
        logger.warning("WHATSAPP_EXTRA_BODY is not valid JSON — ignoring it")

    # A self-hosted gateway runs on a phone and WILL sometimes be slow or
    # offline. Notifications dispatch synchronously while a muster is being
    # activated, so an unbounded per-recipient loop could leave the operator
    # watching a spinner for minutes during an emergency. Bound the single
    # request AND the whole run; anything not attempted is reported failed
    # rather than silently dropped.
    req_timeout = float(os.getenv("WHATSAPP_TIMEOUT", "8"))
    budget = float(os.getenv("WHATSAPP_TOTAL_TIMEOUT", "30"))
    started = _time.monotonic()

    sent, failed = 0, []
    for number in recipients:
        if _time.monotonic() - started > budget:
            failed.append(number)
            logger.warning("WHATSAPP time budget of %.0fs exhausted — %s not attempted", budget, number)
            continue
        try:
            body: Dict[str, object] = {f_to: number, f_msg: message}
            if api_key and not key_header:
                body["api_key"] = api_key
            body.update(extra)
            resp = requests.post(url, json=body, headers=headers, timeout=req_timeout)
            resp.raise_for_status()
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed.append(number)
            logger.warning("WhatsApp to %s failed: %s", number, exc)
    return _finish(sent, failed, "generic")


def _send_twilio(recipients: List[str], message: str) -> Dict[str, object]:
    from_addr = os.getenv("WHATSAPP_FROM")  # e.g. "whatsapp:+14155238886"
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    try:
        from twilio.rest import Client
    except ImportError:
        return {"sent": 0, "failed": recipients, "error": "twilio library not installed"}

    client = Client(sid, token)
    sent, failed = 0, []
    for number in recipients:
        try:
            to_addr = number if number.startswith("whatsapp:") else f"whatsapp:{number}"
            client.messages.create(body=message, from_=from_addr, to=to_addr)
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed.append(number)
            logger.warning("Twilio WhatsApp to %s failed: %s", number, exc)
    return _finish(sent, failed, "twilio")
