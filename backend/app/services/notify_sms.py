"""
Shared, env-configured SMS sender.

One place every alert (emergency, mustering, …) sends SMS through, so a single
set of gateway env vars turns SMS on everywhere. Provider is chosen by
SMS_PROVIDER (termii | twilio | africastalking | generic); if unset it is
auto-detected from whatever creds are present.

  Termii (Nigeria — recommended, default when SMS_PROVIDER=termii):
    SMS_PROVIDER=termii
    SMS_API_KEY               Termii API key (required)
    SMS_SENDER_ID             approved sender ID (default "N-Alert")
    SMS_CHANNEL               generic | dnd | whatsapp (default "dnd" — the
                              transactional route; "generic" is blocked for
                              the 100M+ numbers on Nigeria's NCC DND list)
    SMS_DEFAULT_COUNTRY_CODE  digits prepended to local 0-numbers (default "234")
    TERMII_BASE_URL           default https://api.ng.termii.com

  Twilio:
    TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / SMS_FROM_NUMBER (or TWILIO_FROM_NUMBER)

  Generic HTTP gateway (in-house / proxy):
    SMS_API_URL               POST endpoint; body {"api_key","to","message"[, "from"]}
    SMS_API_KEY / SMS_SENDER_ID

Never raises — returns {"sent": N, "failed": [...], "error"?: str} so a gateway
outage can never break the flow that triggered it. The HTTP calls block, so
async callers must run these via asyncio.to_thread().
"""

from __future__ import annotations

import logging
import os
import re
from typing import Dict, Iterable, List, Union

logger = logging.getLogger(__name__)

TERMII_DEFAULT_BASE = "https://api.ng.termii.com"


def _provider() -> str:
    """Which SMS backend is usable, or '' when SMS is off."""
    explicit = os.getenv("SMS_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    if os.getenv("SMS_API_URL"):
        return "generic"
    if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and (
        os.getenv("SMS_FROM_NUMBER") or os.getenv("TWILIO_FROM_NUMBER")
    ):
        return "twilio"
    return ""


def sms_configured() -> bool:
    """True if the selected SMS provider has the creds it needs to send."""
    provider = _provider()
    if provider == "termii":
        return bool(os.getenv("SMS_API_KEY"))
    if provider == "africastalking":
        return bool(os.getenv("AT_USERNAME") and os.getenv("SMS_API_KEY"))
    if provider == "twilio":
        return bool(
            os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")
            and (os.getenv("SMS_FROM_NUMBER") or os.getenv("TWILIO_FROM_NUMBER"))
        )
    if provider == "generic":
        return bool(os.getenv("SMS_API_URL"))
    return False


def _clean(to: Union[str, Iterable[str]]) -> List[str]:
    recipients: List[str] = [to] if isinstance(to, str) else [r for r in to if r]
    return [r.strip() for r in recipients if r and r.strip()]


def normalize_msisdn(number: str, default_cc: str | None = None) -> str:
    """Best-effort E.164-without-plus for gateways that want bare international MSISDNs.

    Strips spaces/dashes/parens and a leading '+'. A local number starting with a
    single '0' has it replaced by the default country code (234 for Nigeria) so
    '08012345678' → '2348012345678'. Numbers that already look international are
    left as-is. Never guesses when it can't tell.
    """
    cc = (default_cc or os.getenv("SMS_DEFAULT_COUNTRY_CODE", "234")).strip()
    digits = re.sub(r"[\s\-()]", "", number.strip())
    digits = digits.lstrip("+")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and cc:
        digits = cc + digits[1:]
    return digits


def send_sms(to: Union[str, Iterable[str]], message: str) -> Dict[str, object]:
    """Send one SMS to one or many numbers via the env-configured provider.

    Returns {"sent": N, "failed": [num, ...], "error"?: str}. Fails soft: an
    unconfigured or unreachable gateway yields sent=0 with a clear error, never
    an exception.
    """
    recipients = _clean(to)
    if not recipients:
        return {"sent": 0, "failed": [], "error": "no recipients with a phone number"}

    provider = _provider()
    if not sms_configured():
        return {
            "sent": 0,
            "failed": recipients,
            "error": "SMS gateway not configured — set SMS_PROVIDER + its credentials "
                     "(e.g. SMS_PROVIDER=termii, SMS_API_KEY=...)",
        }

    if provider == "termii":
        # Default to the DND route, NOT "generic".
        #
        # Nigeria's NCC Do-Not-Disturb list carries over 100 million numbers, and
        # the generic/promotional route is BLOCKED for every one of them. Only the
        # transactional route ("dnd" at Termii — the same one OTPs use) reaches a
        # DND-registered handset. With the old default a muster alert would have
        # been silently dropped for a large share of the workforce: the send
        # reports success, the phone never rings. Override with SMS_CHANNEL if a
        # deployment is outside Nigeria.
        return _send_termii(recipients, message, os.getenv("SMS_CHANNEL", "dnd"))
    if provider == "twilio":
        return _send_twilio(recipients, message)
    if provider == "africastalking":
        return _send_africastalking(recipients, message)
    return _send_generic(recipients, message)


def _finish(sent: int, failed: List[str], tag: str) -> Dict[str, object]:
    logger.info("notify_sms(%s): sent %d, failed %d", tag, sent, len(failed))
    out: Dict[str, object] = {"sent": sent, "failed": failed}
    if sent == 0 and failed:
        out["error"] = f"all sends failed via {tag} — check credentials/sender ID and gateway"
    return out


def _send_termii(recipients: List[str], message: str, channel: str) -> Dict[str, object]:
    import requests

    base = os.getenv("TERMII_BASE_URL", TERMII_DEFAULT_BASE).rstrip("/")
    url = f"{base}/api/sms/send"
    api_key = os.getenv("SMS_API_KEY", "")
    sender = os.getenv("SMS_SENDER_ID") or "N-Alert"

    sent, failed = 0, []
    for number in recipients:
        try:
            payload = {
                "to": normalize_msisdn(number),
                "from": sender,
                "sms": message,
                "type": "plain",
                "channel": channel,  # generic | dnd | whatsapp
                "api_key": api_key,
            }
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json() if resp.content else {}
            if data.get("message_id"):
                sent += 1
            else:
                failed.append(number)
                logger.warning("Termii SMS to %s returned no message_id: %s", number, data)
        except Exception as exc:  # noqa: BLE001 — one bad number must not fail the rest
            failed.append(number)
            logger.warning("Termii SMS to %s failed: %s", number, exc)
    return _finish(sent, failed, "termii")


def _send_generic(recipients: List[str], message: str) -> Dict[str, object]:
    """POST to any HTTP SMS gateway, including the free self-hosted ones.

    The original shape was fixed — api_key in the BODY, fields named to/message —
    which matches almost no real gateway. The self-hosted options people actually
    use for Nigeria all differ:

        httpSMS    header x-api-key,  body {"content", "from", "to"}
        textbee    header x-api-key,  body {"recipients": [...], "message"}
        SMSGate    Basic auth,        body {"phoneNumbers": [...], "message"}

    So the field names, the auth header and whether recipients are sent as an
    array are all configurable. Defaults reproduce the old behaviour exactly.

        SMS_API_URL          POST endpoint
        SMS_API_KEY          credential
        SMS_API_KEY_HEADER   send the key as this HEADER instead of in the body
                             (e.g. "x-api-key"); unset = body field "api_key"
        SMS_API_HEADERS      extra headers as JSON, e.g. {"Authorization":"Basic .."}
        SMS_FIELD_TO         recipient field name        (default "to")
        SMS_FIELD_MESSAGE    message field name          (default "message")
        SMS_FIELD_FROM       sender field name           (default "from")
        SMS_BATCH_RECIPIENTS "true" = send all numbers in ONE request as a list
    """
    import json as _json
    import requests

    url = os.getenv("SMS_API_URL", "")
    api_key = os.getenv("SMS_API_KEY", "")
    sender_id = os.getenv("SMS_SENDER_ID", "")
    key_header = os.getenv("SMS_API_KEY_HEADER", "").strip()
    f_to = os.getenv("SMS_FIELD_TO", "to")
    f_msg = os.getenv("SMS_FIELD_MESSAGE", "message")
    f_from = os.getenv("SMS_FIELD_FROM", "from")
    batch = os.getenv("SMS_BATCH_RECIPIENTS", "").lower() in ("1", "true", "yes")

    headers: Dict[str, str] = {}
    try:
        headers.update(_json.loads(os.getenv("SMS_API_HEADERS", "") or "{}"))
    except Exception:
        logger.warning("SMS_API_HEADERS is not valid JSON — ignoring it")
    if key_header and api_key:
        headers[key_header] = api_key

    def _body(target) -> Dict[str, object]:
        body: Dict[str, object] = {f_to: target, f_msg: message}
        # Only put the key in the body when it is NOT being sent as a header.
        if api_key and not key_header:
            body["api_key"] = api_key
        if sender_id:
            body[f_from] = sender_id
        return body

    sent, failed = 0, []
    if batch:
        try:
            resp = requests.post(url, json=_body(recipients), headers=headers, timeout=10)
            resp.raise_for_status()
            sent = len(recipients)
        except Exception as exc:  # noqa: BLE001
            failed = list(recipients)
            logger.warning("SMS batch of %d failed: %s", len(recipients), exc)
        return _finish(sent, failed, "generic")

    for number in recipients:
        try:
            resp = requests.post(url, json=_body(number), headers=headers, timeout=10)
            resp.raise_for_status()
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed.append(number)
            logger.warning("SMS to %s failed: %s", number, exc)
    return _finish(sent, failed, "generic")


def _send_twilio(recipients: List[str], message: str) -> Dict[str, object]:
    from_number = os.getenv("SMS_FROM_NUMBER") or os.getenv("TWILIO_FROM_NUMBER")
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
            client.messages.create(body=message, from_=from_number, to=number)
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed.append(number)
            logger.warning("Twilio SMS to %s failed: %s", number, exc)
    return _finish(sent, failed, "twilio")


def _send_africastalking(recipients: List[str], message: str) -> Dict[str, object]:
    import requests

    username = os.getenv("AT_USERNAME", "")
    api_key = os.getenv("SMS_API_KEY", "")
    sender_id = os.getenv("SMS_SENDER_ID", "")
    url = os.getenv("SMS_API_URL") or "https://api.africastalking.com/version1/messaging"

    # Africa's Talking takes all recipients in one comma-separated call.
    to = ",".join(normalize_msisdn(n) for n in recipients)
    try:
        data = {"username": username, "to": to, "message": message}
        if sender_id:
            data["from"] = sender_id
        resp = requests.post(
            url,
            data=data,
            headers={"apiKey": api_key, "Accept": "application/json",
                     "Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        recips = body.get("SMSMessageData", {}).get("Recipients", [])
        sent = sum(1 for r in recips if str(r.get("status", "")).lower().startswith("success"))
        failed = [r.get("number") for r in recips if not str(r.get("status", "")).lower().startswith("success")]
        return _finish(sent, [f for f in failed if f], "africastalking")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Africa's Talking SMS failed: %s", exc)
        return {"sent": 0, "failed": recipients, "error": str(exc)}
