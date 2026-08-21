"""
Device WebSocket Implementation for Real-time Monitoring
Handles real-time device status updates and live logs
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import verify_token
from ..models.biotime_models import IClockTerminal, IClockTransaction

# Router
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

# WebSocket connection manager
class DeviceWebSocketManager:
    def __init__(self):
        # Store active connections
        self.device_connections: Dict[str, Set[WebSocket]] = {}  # device_sn -> set of connections
        self.status_connections: Set[WebSocket] = set()  # connections for device status updates
        self.log_connections: Dict[str, Set[WebSocket]] = {}  # device_sn -> set of log connections
        
    async def connect_device_status(self, websocket: WebSocket):
        """Connect to device status broadcast"""
        await websocket.accept()
        self.status_connections.add(websocket)
        logger.info(f"Device status client connected. Total status connections: {len(self.status_connections)}")
        
    async def disconnect_device_status(self, websocket: WebSocket):
        """Disconnect from device status broadcast"""
        self.status_connections.discard(websocket)
        logger.info(f"Device status client disconnected. Total status connections: {len(self.status_connections)}")
        
    async def connect_device_logs(self, websocket: WebSocket, device_sn: str):
        """Connect to specific device logs"""
        await websocket.accept()
        
        if device_sn not in self.log_connections:
            self.log_connections[device_sn] = set()
        
        self.log_connections[device_sn].add(websocket)
        logger.info(f"Device logs client connected for {device_sn}. Connections: {len(self.log_connections[device_sn])}")
        
    async def disconnect_device_logs(self, websocket: WebSocket, device_sn: str):
        """Disconnect from specific device logs"""
        if device_sn in self.log_connections:
            self.log_connections[device_sn].discard(websocket)
            
            # Clean up empty device connections
            if not self.log_connections[device_sn]:
                del self.log_connections[device_sn]
                
        logger.info(f"Device logs client disconnected for {device_sn}")
        
    async def broadcast_device_status(self, device_data: Dict):
        """Broadcast device status update to all status connections"""
        if not self.status_connections:
            return
            
        message = {
            "type": "device_status",
            "data": device_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all connected status clients
        disconnected_clients = set()
        for connection in self.status_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Error broadcasting device status: {e}")
                disconnected_clients.add(connection)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.status_connections.discard(client)
            
    async def send_device_log(self, device_sn: str, log_data: Dict):
        """Send device log to specific device log connections"""
        if device_sn not in self.log_connections:
            return
            
        message = {
            "type": "device_log",
            "device_sn": device_sn,
            "data": log_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all connected log clients for this device
        disconnected_clients = set()
        for connection in self.log_connections[device_sn]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Error sending device log: {e}")
                disconnected_clients.add(connection)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.log_connections[device_sn].discard(client)
            
    async def broadcast_emergency_alert(self, alert_data: Dict):
        """Broadcast emergency alert to all connections"""
        message = {
            "type": "emergency_alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all status connections
        disconnected_clients = set()
        for connection in self.status_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Error broadcasting emergency alert: {e}")
                disconnected_clients.add(connection)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.status_connections.discard(client)
            
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "status_connections": len(self.status_connections),
            "device_log_connections": {
                device_sn: len(connections) 
                for device_sn, connections in self.log_connections.items()
            },
            "total_connections": len(self.status_connections) + sum(
                len(connections) for connections in self.log_connections.values()
            )
        }

# Global WebSocket manager
websocket_manager = DeviceWebSocketManager()

# Helper Functions
async def get_device_real_time_data(db: Session, device_sn: str) -> Dict:
    """Get real-time data for a device"""
    try:
        # Get device info
        device = db.query(IClockTerminal).filter(IClockTerminal.sn == device_sn).first()
        if not device:
            return None
            
        # Get recent transactions
        recent_txns = db.execute(text("""
            SELECT emp_code, punch_time, punch_state, verify_type
            FROM iclock_transaction 
            WHERE terminal_sn = :sn 
            ORDER BY punch_time DESC 
            LIMIT 5
        """), {'sn': device_sn}).fetchall()
        
        # Get pending commands
        pending_cmds = db.execute(text("""
            SELECT COUNT(*) as count, cmd_content
            FROM iclock_devcmd 
            WHERE sn = :sn AND status = 0
            ORDER BY cmd_commit_time DESC
            LIMIT 1
        """), {'sn': device_sn}).fetchone()
        
        # Determine online status
        is_online = False
        if device.last_activity:
            time_diff = datetime.utcnow() - device.last_activity
            is_online = time_diff.total_seconds() <= 300  # 5 minutes
        
        return {
            "sn": device.sn,
            "alias": device.alias,
            "device_name": device.device_name,
            "ip_address": device.ip_address,
            "device_type": device.device_type,
            "zone_id": device.zone_id,
            "status": "online" if is_online else "offline",
            "last_activity": device.last_activity.isoformat() if device.last_activity else None,
            "user_count": device.user_count or 0,
            "fp_count": device.fp_count or 0,
            "face_count": device.face_count or 0,
            "fw_version": device.fw_version,
            "recent_transactions": [
                {
                    "emp_code": txn.emp_code,
                    "punch_time": txn.punch_time.isoformat(),
                    "punch_state": txn.punch_state,
                    "verify_type": txn.verify_type
                }
                for txn in recent_txns
            ],
            "pending_commands": pending_cmds.count if pending_cmds else 0,
            "last_command": pending_cmds.cmd_content if pending_cmds else None
        }
        
    except Exception as e:
        logger.error(f"Error getting device real-time data: {e}")
        return None

async def monitor_device_activity(db: Session):
    """Background task to monitor device activity and broadcast updates"""
    while True:
        try:
            # Get devices with recent activity
            recent_devices = db.execute(text("""
                SELECT sn, last_activity, state, user_count, fp_count, face_count
                FROM iclock_terminal 
                WHERE last_activity >= :since 
                OR state != 0
                ORDER BY last_activity DESC
                LIMIT 50
            """), {
                'since': datetime.utcnow() - timedelta(minutes=10)
            }).fetchall()
            
            for device_row in recent_devices:
                device_data = await get_device_real_time_data(db, device_row.sn)
                if device_data:
                    await websocket_manager.broadcast_device_status(device_data)
                    
                    # Send logs if there are recent transactions
                    if device_data.get("recent_transactions"):
                        for txn in device_data["recent_transactions"]:
                            await websocket_manager.send_device_log(device_row.sn, {
                                "event_type": "punch",
                                "emp_code": txn["emp_code"],
                                "punch_time": txn["punch_time"],
                                "punch_state": txn["punch_state"],
                                "verify_type": txn["verify_type"]
                            })
            
            # Check for emergency device status changes
            emergency_devices = db.execute(text("""
                SELECT ed.terminal_sn, ed.status, ed.last_heartbeat,
                       it.device_name, it.zone_id
                FROM emergency_device ed
                JOIN iclock_terminal it ON ed.terminal_sn = it.sn
                WHERE ed.last_heartbeat >= :since
                ORDER BY ed.last_heartbeat DESC
            """), {
                'since': datetime.utcnow() - timedelta(minutes=5)
            }).fetchall()
            
            for emergency in emergency_devices:
                await websocket_manager.broadcast_emergency_alert({
                    "device_sn": emergency.terminal_sn,
                    "device_name": emergency.device_name,
                    "zone_id": emergency.zone_id,
                    "status": "on" if emergency.status else "off",
                    "last_heartbeat": emergency.last_heartbeat.isoformat()
                })
            
            # Sleep for 30 seconds before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in device monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# WebSocket Endpoints

@router.websocket("/ws/device/status")
async def websocket_device_status(websocket: WebSocket):
    """WebSocket endpoint for real-time device status updates."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=1008)
        return
    await websocket_manager.connect_device_status(websocket)
    
    try:
        # Send initial device list
        # This would typically get from database
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to device status updates",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message (could be ping or subscription requests)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                elif message.get("type") == "get_devices":
                    # Send current device list
                    # This would query database and send device list
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect_device_status(websocket)

@router.websocket("/ws/device/{device_sn}")
async def websocket_device_logs(websocket: WebSocket, device_sn: str):
    """WebSocket endpoint for specific device logs."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=1008)
        return
    await websocket_manager.connect_device_logs(websocket, device_sn)
    
    try:
        # Send initial device data
        # This would get from database
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "device_sn": device_sn,
            "message": f"Connected to {device_sn} logs",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Keep connection alive
        while True:
            try:
                # Receive message (could be ping or commands)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "device_sn": device_sn,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                elif message.get("type") == "get_recent_logs":
                    # Send recent logs for this device
                    # This would query database for recent transactions
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling device WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect_device_logs(websocket, device_sn)

# API Endpoints for WebSocket Management

@router.get("/api/device/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "status": "active",
        "connections": websocket_manager.get_connection_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/api/device/websocket/broadcast/{device_sn}")
async def broadcast_device_update(
    device_sn: str,
    device_data: Dict,
    # current_user: User = Depends(get_current_user)  # Uncomment if auth needed
):
    """Manually broadcast device update (for testing)"""
    try:
        await websocket_manager.broadcast_device_status({
            "sn": device_sn,
            **device_data
        })
        
        return {
            "message": f"Device update broadcasted for {device_sn}",
            "connections": len(websocket_manager.status_connections)
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting device update: {e}")
        return {
            "error": str(e),
            "message": "Failed to broadcast device update"
        }

@router.post("/api/device/websocket/emergency-alert")
async def broadcast_emergency_alert(
    alert_data: Dict,
    # current_user: User = Depends(get_current_user)  # Uncomment if auth needed
):
    """Manually broadcast emergency alert (for testing)"""
    try:
        await websocket_manager.broadcast_emergency_alert(alert_data)
        
        return {
            "message": "Emergency alert broadcasted",
            "connections": len(websocket_manager.status_connections)
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting emergency alert: {e}")
        return {
            "error": str(e),
            "message": "Failed to broadcast emergency alert"
        }

# Background Task Management
background_task = None

async def start_device_monitoring():
    """Start the background device monitoring task"""
    global background_task
    
    if background_task is None:
        # Get database session for background task
        from ..core.database import get_db
        db_gen = get_db()
        db = next(db_gen)
        
        background_task = asyncio.create_task(monitor_device_activity(db))
        logger.info("Device monitoring background task started")

async def stop_device_monitoring():
    """Stop the background device monitoring task"""
    global background_task
    
    if background_task:
        background_task.cancel()
        background_task = None
        logger.info("Device monitoring background task stopped")

# Lifecycle management
async def on_startup():
    """Initialize WebSocket services on startup"""
    await start_device_monitoring()

async def on_shutdown():
    """Clean up WebSocket services on shutdown"""
    await stop_device_monitoring()
