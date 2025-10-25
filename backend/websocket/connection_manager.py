"""
WebSocket manager for real-time Elasticsearch updates.
Handles multiple connections and broadcasts updates to all connected clients.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to all connected clients.
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_count = 0
        
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"[WebSocket] Client connected. Active connections: {len(self.active_connections)}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to Elasticsearch live feed",
            "timestamp": datetime.now().isoformat(),
            "connection_id": self.connection_count
        })
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"[WebSocket] Client disconnected. Active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"[WebSocket] Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.
        Handles disconnections gracefully.
        """
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
                logger.warning("[WebSocket] Client disconnected during broadcast")
            except Exception as e:
                logger.error(f"[WebSocket] Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_elasticsearch_update(self, data: List[Dict[str, Any]], update_type: str = "new_data"):
        """
        Broadcast Elasticsearch updates to all clients.
        
        Args:
            data: List of Elasticsearch documents
            update_type: Type of update (new_data, aggregation, alert, etc.)
        """
        message = {
            "type": update_type,
            "timestamp": datetime.now().isoformat(),
            "count": len(data),
            "data": data
        }
        
        await self.broadcast(message)
        logger.debug(f"[WebSocket] Broadcasted {len(data)} items to {len(self.active_connections)} clients")
    
    async def broadcast_stats(self, stats: Dict[str, Any]):
        """Broadcast statistics/metrics to all clients."""
        message = {
            "type": "stats",
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
        
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast security alerts to all clients."""
        message = {
            "type": "alert",
            "timestamp": datetime.now().isoformat(),
            "alert": alert,
            "severity": alert.get("severity", "medium")
        }
        
        await self.broadcast(message)
        logger.warning(f"[WebSocket] Alert broadcasted: {alert.get('message', 'Unknown alert')}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()