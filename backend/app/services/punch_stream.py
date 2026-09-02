"""
Live punch fan-out for the attendance dashboard.

Previously this registry lived inside the ZKTeco live-capture loop, because
punches only ever arrived from physical readers. Mobile punches are now the
only source, so the subscriber set moved here and the mobile endpoint
publishes to it directly — keeping the supervisor's live view working without
any device code behind it.

Subscribers are per-worker. With several uvicorn workers each holds its own
set, which is fine for a dashboard: every worker serves the SSE connections it
accepted. Cross-worker fan-out would need Redis pub/sub, which the notification
stream already does if this ever needs to be strictly global.
"""

import asyncio
import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

_subscribers: set[asyncio.Queue] = set()
_lock = threading.Lock()


def add_subscriber(q: asyncio.Queue) -> None:
    with _lock:
        _subscribers.add(q)


def remove_subscriber(q: asyncio.Queue) -> None:
    with _lock:
        _subscribers.discard(q)


def publish_punch(event: dict[str, Any]) -> None:
    """
    Push a punch to every open dashboard.

    Never raises: a punch is an attendance record first and a dashboard update
    second, so a slow or dead subscriber must not fail the request that is
    trying to record it. Full queues are dropped rather than awaited.
    """
    with _lock:
        targets = list(_subscribers)
    for q in targets:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            logger.debug("punch stream subscriber is full — dropping event")
        except Exception:
            with _lock:
                _subscribers.discard(q)
