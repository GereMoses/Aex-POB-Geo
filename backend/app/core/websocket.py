"""
WebSocket Connection Manager
Basic WebSocket connection management for real-time features
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from .config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, room: str = "default"):
        """Connect a WebSocket client"""
        await websocket.accept()
        
        if room not in self.active_connections:
            self.active_connections[room] = []
        
        self.active_connections[room].append(websocket)
        self.user_connections[websocket] = user_id
        
        logger.info(f"User {user_id} connected to room {room}")
        
        # Notify others in the room
        await self.broadcast_to_room(room, {
            "type": "user_connected",
            "user_id": user_id,
            "message": f"User {user_id} joined the room"
        }, exclude_websocket=websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client.

        Synchronous on purpose: it is called from cleanup paths inside async
        broadcast loops where awaiting is unsafe (and where the previous async
        version was never awaited — so dead sockets were never removed and the
        connection dicts leaked). The "user left" notice is fire-and-forget via
        a background task so cleanup itself never blocks or mutates-during-iterate.
        """
        user_id = self.user_connections.get(websocket, "unknown")
        left_rooms = []

        # Iterate over a snapshot of items; mutate the underlying lists safely.
        for room, connections in list(self.active_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                left_rooms.append(room)
                logger.info(f"User {user_id} disconnected from room {room}")

        # Remove from user connections
        if websocket in self.user_connections:
            del self.user_connections[websocket]

        # Fire-and-forget leave notices (only if an event loop is running).
        for room in left_rooms:
            self._schedule_broadcast(room, {
                "type": "user_disconnected",
                "user_id": user_id,
                "message": f"User {user_id} left the room",
            })

    def _schedule_broadcast(self, room: str, message: dict) -> None:
        """Schedule a room broadcast without blocking the caller."""
        try:
            asyncio.get_running_loop().create_task(self.broadcast_to_room(room, message))
        except RuntimeError:
            pass  # no running loop (e.g. called from sync context/tests) — skip notice

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_room(self, room: str, message: dict, exclude_websocket: Optional[WebSocket] = None):
        """Broadcast a message to all clients in a room"""
        if room not in self.active_connections:
            return

        disconnected = []
        # Iterate a copy so disconnect()-driven mutation can't corrupt iteration.
        for connection in list(self.active_connections[room]):
            if connection == exclude_websocket:
                continue

            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to room {room}: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections (now a real, synchronous removal)
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        for room in self.active_connections:
            await self.broadcast_to_room(room, message)
    
    def get_room_connections(self, room: str) -> List[WebSocket]:
        """Get all connections in a specific room"""
        return self.active_connections.get(room, [])
    
    def get_connection_count(self, room: str = None) -> int:
        """Get number of connections in a room or total"""
        if room:
            return len(self.active_connections.get(room, []))
        return len(self.user_connections)
    
    def get_user_rooms(self, user_id: str) -> List[str]:
        """Get all rooms a user is connected to"""
        rooms = []
        for room, connections in self.active_connections.items():
            for connection in connections:
                if self.user_connections.get(connection) == user_id:
                    rooms.append(room)
                    break
        return rooms

# Global connection manager instance
manager = ConnectionManager()

# ── Zone live-count broadcast ─────────────────────────────────────────────────

_zone_connections: list = []  # List[WebSocket]


async def zone_ws_connect(websocket) -> None:
    await websocket.accept()
    _zone_connections.append(websocket)


def zone_ws_disconnect(websocket) -> None:
    if websocket in _zone_connections:
        _zone_connections.remove(websocket)


async def broadcast_zone_update(zone_id: int, count: int, zone_name: str = "") -> None:
    """Push a single zone occupancy update to every connected POB dashboard."""
    if not _zone_connections:
        return
    import json
    payload = json.dumps({"type": "zone_update", "zone_id": zone_id,
                          "count": count, "zone_name": zone_name})
    dead = []
    for ws in list(_zone_connections):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        zone_ws_disconnect(ws)


# Main event loop, captured at startup, so zone broadcasts can be fired from any
# context — request handlers, background asyncio tasks, or threadpool worker threads.
_main_loop = None


def set_main_loop(loop) -> None:
    global _main_loop
    _main_loop = loop


# Redis pub/sub backplane — the API runs multiple uvicorn workers, each with its own
# in-process WS connection list. A punch handled by one worker must reach a dashboard
# connected to a different worker, so updates are published to Redis and every worker
# relays them to its own local WS clients.
_ZONE_CHANNEL = "apex:zone_updates"
_pub_redis = None


def _publisher():
    global _pub_redis
    if _pub_redis is None:
        import redis as _redis
        _pub_redis = _redis.from_url(settings.REDIS_URL)
    return _pub_redis


def _local_zone_broadcast(zone_id: int, count: int, zone_name: str = "") -> None:
    """Broadcast to THIS worker's local WS clients, from any context."""
    coro = broadcast_zone_update(zone_id, count, zone_name)
    try:
        asyncio.get_running_loop().create_task(coro)
        return
    except RuntimeError:
        pass  # not on an event loop (threadpool worker) — use the captured main loop
    if _main_loop is not None and _main_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(coro, _main_loop)
            return
        except Exception:
            pass
    coro.close()  # no loop available — avoid 'coroutine was never awaited'


def schedule_zone_broadcast(zone_id: int, count: int, zone_name: str = "") -> None:
    """
    Fire a live zone-occupancy update from ANY context. Publishes to Redis so EVERY
    worker relays it to its local dashboards; falls back to a local-only broadcast if
    Redis is unavailable. Called by the central occupancy recalc so every path
    (ADMS push, direct poll, live-capture, reset) pushes in real time without refresh.
    """
    try:
        _publisher().publish(_ZONE_CHANNEL, json.dumps(
            {"zone_id": zone_id, "count": count, "zone_name": zone_name}))
        return
    except Exception as e:
        logger.warning("zone broadcast publish failed (%s) — local fallback", e)
    _local_zone_broadcast(zone_id, count, zone_name)


async def zone_pubsub_listener() -> None:
    """Per-worker background task: relay Redis zone updates to this worker's WS clients."""
    import redis.asyncio as aioredis
    while True:
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            ps = r.pubsub()
            await ps.subscribe(_ZONE_CHANNEL)
            logger.info("Zone pub/sub listener subscribed to %s", _ZONE_CHANNEL)
            async for m in ps.listen():
                if m.get("type") != "message":
                    continue
                try:
                    d = json.loads(m["data"])
                    await broadcast_zone_update(int(d["zone_id"]), int(d["count"]), d.get("zone_name", ""))
                except Exception:
                    pass
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("zone pub/sub listener error: %s — retry in 5s", e)
            await asyncio.sleep(5)
