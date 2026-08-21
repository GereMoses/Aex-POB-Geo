"""
BioTime WebSocket Service

This module provides real-time WebSocket connections for BioTime integration,
including live device status streaming, attendance monitoring, and biometric verification updates.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.personnel import Personnel, AttendanceLog
from ..models.biotime_enhancements import BioTimeDevice, BioTimeBiometricTemplate
from ..services.biotime_client import biotime_client


class BioTimeWebSocketManager:
    """WebSocket connection manager for BioTime real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "device_status": [],
            "attendance_live": [],
            "biometric_updates": [],
            "system_health": [],
            "emergency_alerts": []
        }
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, connection_type: str, metadata: Dict[str, Any] = None):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        if connection_type not in self.active_connections:
            raise ValueError(f"Invalid connection type: {connection_type}")
        
        self.active_connections[connection_type].append(websocket)
        self.connection_metadata[websocket] = {
            "connection_type": connection_type,
            "connected_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        print(f"WebSocket connected: {connection_type}, total connections: {len(self.active_connections[connection_type])}")
    
    def disconnect(self, websocket: WebSocket, connection_type: str):
        """Remove WebSocket connection"""
        if connection_type in self.active_connections and websocket in self.active_connections[connection_type]:
            self.active_connections[connection_type].remove(websocket)
        
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        print(f"WebSocket disconnected: {connection_type}, remaining connections: {len(self.active_connections.get(connection_type, []))}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: Dict[str, Any], connection_type: str):
        """Broadcast message to all connections of specific type"""
        if connection_type not in self.active_connections:
            return
        
        disconnected_connections = []
        for connection in self.active_connections[connection_type]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected_connections.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection, connection_type)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all active connections"""
        for connection_type in self.active_connections:
            await self.broadcast(message, connection_type)


# Global WebSocket Manager
websocket_manager = BioTimeWebSocketManager()


class BioTimeEventStreamer:
    """Real-time event streaming for BioTime data"""
    
    def __init__(self):
        self.streaming_active = False
        self.stream_tasks: List[asyncio.Task] = []
    
    async def start_streaming(self):
        """Start all streaming tasks"""
        if self.streaming_active:
            return
        
        self.streaming_active = True
        
        # Start streaming tasks
        self.stream_tasks = [
            asyncio.create_task(self.stream_device_events()),
            asyncio.create_task(self.stream_attendance_events()),
            asyncio.create_task(self.stream_biometric_events()),
            asyncio.create_task(self.stream_system_health()),
            asyncio.create_task(self.stream_emergency_alerts())
        ]
        
        print("BioTime event streaming started")
    
    async def stop_streaming(self):
        """Stop all streaming tasks"""
        self.streaming_active = False
        
        for task in self.stream_tasks:
            task.cancel()
        
        self.stream_tasks.clear()
        print("BioTime event streaming stopped")
    
    async def stream_device_events(self):
        """Stream real-time device status events"""
        while self.streaming_active:
            try:
                # Get device status from BioTime
                device_status = await self._get_device_status()
                
                if device_status:
                    event_data = {
                        "event_type": "device_status",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": device_status,
                        "source": "biotime_websocket"
                    }
                    
                    await websocket_manager.broadcast(event_data, "device_status")
                
                await asyncio.sleep(30)  # Stream every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in device status streaming: {e}")
                await asyncio.sleep(5)
    
    async def stream_attendance_events(self):
        """Stream real-time attendance events"""
        while self.streaming_active:
            try:
                # Get recent attendance events
                attendance_events = await self._get_attendance_events()
                
                if attendance_events:
                    event_data = {
                        "event_type": "attendance_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": attendance_events,
                        "source": "biotime_websocket"
                    }
                    
                    await websocket_manager.broadcast(event_data, "attendance_live")
                
                await asyncio.sleep(10)  # Stream every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in attendance streaming: {e}")
                await asyncio.sleep(5)
    
    async def stream_biometric_events(self):
        """Stream real-time biometric verification events"""
        while self.streaming_active:
            try:
                # Get recent biometric verification events
                biometric_events = await self._get_biometric_events()
                
                if biometric_events:
                    event_data = {
                        "event_type": "biometric_verification",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": biometric_events,
                        "source": "biotime_websocket"
                    }
                    
                    await websocket_manager.broadcast(event_data, "biometric_updates")
                
                await asyncio.sleep(15)  # Stream every 15 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in biometric streaming: {e}")
                await asyncio.sleep(5)
    
    async def stream_system_health(self):
        """Stream system health monitoring"""
        while self.streaming_active:
            try:
                # Get system health metrics
                health_data = await self._get_system_health()
                
                event_data = {
                    "event_type": "system_health",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": health_data,
                    "source": "biotime_websocket"
                }
                
                await websocket_manager.broadcast(event_data, "system_health")
                
                await asyncio.sleep(60)  # Stream every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in health streaming: {e}")
                await asyncio.sleep(5)
    
    async def stream_emergency_alerts(self):
        """Stream emergency alerts"""
        while self.streaming_active:
            try:
                # Get emergency alerts
                emergency_data = await self._get_emergency_alerts()
                
                if emergency_data:
                    event_data = {
                        "event_type": "emergency_alert",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": emergency_data,
                        "source": "biotime_websocket"
                    }
                    
                    await websocket_manager.broadcast(event_data, "emergency_alerts")
                
                await asyncio.sleep(5)  # Stream every 5 seconds for emergencies
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in emergency streaming: {e}")
                await asyncio.sleep(1)
    
    async def _get_device_status(self) -> Optional[Dict[str, Any]]:
        """Get current device status from BioTime"""
        try:
            # Simulate device status data
            return {
                "total_devices": 15,
                "online_devices": 13,
                "offline_devices": 2,
                "devices": [
                    {
                        "device_id": "MB560_001",
                        "device_name": "Main Entrance",
                        "status": "online",
                        "cpu_usage": 45.2,
                        "memory_usage": 67.8,
                        "last_heartbeat": datetime.utcnow().isoformat(),
                        "active_sessions": 3
                    },
                    {
                        "device_id": "MB360_001",
                        "device_name": "Side Entrance",
                        "status": "offline",
                        "last_heartbeat": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                        "error_message": "Connection timeout"
                    }
                ]
            }
        except Exception as e:
            print(f"Error getting device status: {e}")
            return None
    
    async def _get_attendance_events(self) -> Optional[List[Dict[str, Any]]]:
        """Get recent attendance events"""
        try:
            # Simulate attendance events
            return [
                {
                    "event_id": f"attendance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "personnel_id": 123,
                    "personnel_name": "John Doe",
                    "device_id": "MB560_001",
                    "event_type": "check_in",
                    "verification_method": "fingerprint",
                    "verification_score": 0.92,
                    "timestamp": datetime.utcnow().isoformat(),
                    "location": "Main Entrance"
                }
            ]
        except Exception as e:
            print(f"Error getting attendance events: {e}")
            return None
    
    async def _get_biometric_events(self) -> Optional[List[Dict[str, Any]]]:
        """Get recent biometric verification events"""
        try:
            # Simulate biometric events
            return [
                {
                    "event_id": f"biometric_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "personnel_id": 456,
                    "personnel_name": "Jane Smith",
                    "device_id": "MB360_001",
                    "verification_type": "multimodal",
                    "biometric_methods": ["fingerprint", "face"],
                    "confidence_score": 0.95,
                    "processing_time_ms": 250,
                    "timestamp": datetime.utcnow().isoformat(),
                    "template_quality": 0.88
                }
            ]
        except Exception as e:
            print(f"Error getting biometric events: {e}")
            return None
    
    async def _get_system_health(self) -> Optional[Dict[str, Any]]:
        """Get system health metrics"""
        try:
            # Simulate system health data
            return {
                "overall_status": "healthy",
                "biotime_connection": {
                    "status": "connected",
                    "response_time_ms": 150,
                    "last_successful_sync": datetime.utcnow().isoformat()
                },
                "database_connection": {
                    "status": "connected",
                    "connection_pool_size": 10,
                    "active_connections": 3
                },
                "performance_metrics": {
                    "cpu_usage": 35.5,
                    "memory_usage": 68.2,
                    "disk_usage": 45.8,
                    "network_io": 1024
                },
                "active_websockets": {
                    "device_status": len(websocket_manager.active_connections.get("device_status", [])),
                    "attendance_live": len(websocket_manager.active_connections.get("attendance_live", [])),
                    "biometric_updates": len(websocket_manager.active_connections.get("biometric_updates", [])),
                    "system_health": len(websocket_manager.active_connections.get("system_health", [])),
                    "emergency_alerts": len(websocket_manager.active_connections.get("emergency_alerts", []))
                }
            }
        except Exception as e:
            print(f"Error getting system health: {e}")
            return None
    
    async def _get_emergency_alerts(self) -> Optional[List[Dict[str, Any]]]:
        """Get emergency alerts"""
        try:
            # Simulate emergency alerts (empty for normal operation)
            return []
        except Exception as e:
            print(f"Error getting emergency alerts: {e}")
            return None


# Global Event Streamer
event_streamer = BioTimeEventStreamer()


async def handle_websocket_connection(websocket: WebSocket, connection_type: str, metadata: Dict[str, Any] = None):
    """Handle WebSocket connection lifecycle"""
    try:
        await websocket_manager.connect(websocket, connection_type, metadata)
        
        # Send initial connection confirmation
        confirmation_message = {
            "type": "connection_established",
            "connection_type": connection_type,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Connected to BioTime {connection_type} stream"
        }
        await websocket_manager.send_personal_message(confirmation_message, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client message (ping/pong or subscription updates)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages
                await handle_client_message(websocket, message)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error handling WebSocket message: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        websocket_manager.disconnect(websocket, connection_type)


async def handle_client_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle incoming WebSocket messages from clients"""
    message_type = message.get("type", "")
    
    if message_type == "ping":
        # Respond to ping with pong
        pong_message = {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.send_personal_message(pong_message, websocket)
    
    elif message_type == "subscribe":
        # Handle subscription to specific data streams
        subscription_data = message.get("data", {})
        
        # Send subscription confirmation
        confirmation_message = {
            "type": "subscription_confirmed",
            "subscription": subscription_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.send_personal_message(confirmation_message, websocket)
    
    elif message_type == "request_data":
        # Handle immediate data request
        request_type = message.get("request_type", "")
        
        if request_type == "device_status":
            device_status = await event_streamer._get_device_status()
            response_message = {
                "type": "data_response",
                "request_type": request_type,
                "data": device_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket_manager.send_personal_message(response_message, websocket)
        
        elif request_type == "recent_attendance":
            attendance_events = await event_streamer._get_attendance_events()
            response_message = {
                "type": "data_response",
                "request_type": request_type,
                "data": attendance_events,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket_manager.send_personal_message(response_message, websocket)
    
    else:
        # Handle unknown message types
        error_message = {
            "type": "error",
            "error": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.send_personal_message(error_message, websocket)


# Utility functions for external use
async def start_biotime_websocket_service():
    """Start the BioTime WebSocket service"""
    await event_streamer.start_streaming()
    print("BioTime WebSocket service started")


async def stop_biotime_websocket_service():
    """Stop the BioTime WebSocket service"""
    await event_streamer.stop_streaming()
    print("BioTime WebSocket service stopped")


async def broadcast_device_alert(alert_data: Dict[str, Any]):
    """Broadcast device alert to all connected clients"""
    message = {
        "event_type": "device_alert",
        "timestamp": datetime.utcnow().isoformat(),
        "data": alert_data,
        "source": "biotime_system"
    }
    await websocket_manager.broadcast(message, "device_status")


async def broadcast_attendance_alert(alert_data: Dict[str, Any]):
    """Broadcast attendance alert to all connected clients"""
    message = {
        "event_type": "attendance_alert",
        "timestamp": datetime.utcnow().isoformat(),
        "data": alert_data,
        "source": "biotime_system"
    }
    await websocket_manager.broadcast(message, "attendance_live")


async def broadcast_emergency_alert(alert_data: Dict[str, Any]):
    """Broadcast emergency alert to all connected clients"""
    message = {
        "event_type": "emergency_alert",
        "timestamp": datetime.utcnow().isoformat(),
        "data": alert_data,
        "source": "biotime_system"
    }
    await websocket_manager.broadcast(message, "emergency_alerts")
