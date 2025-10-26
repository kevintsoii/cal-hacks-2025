"""
WebSocket routes for real-time data streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket import manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/elasticsearch")
async def websocket_elasticsearch(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Elasticsearch updates.
    
    On connection: Sends last 10 logs from Elasticsearch
    Then: Receives real-time updates from middleware via queue
    
    Messages sent to client:
        - connection: Initial connection confirmation
        - initial_data: Last 10 logs on connection
        - new_request: Real-time request from middleware
        - stats: Aggregated statistics (every 30s)
        - alert: Security alerts (when detected)
    """
    from websocket import get_recent_logs
    
    await manager.connect(websocket)
    
    try:
        # Send initial data (last 100 logs)
        logger.info("[WebSocket] Fetching initial logs for new client")
        recent_logs = await get_recent_logs(limit=100)
        
        if recent_logs:
            await websocket.send_json({
                "type": "initial_data",
                "timestamp": datetime.now().isoformat(),
                "count": len(recent_logs),
                "data": recent_logs
            })
            logger.info(f"[WebSocket] Sent {len(recent_logs)} initial logs to client")
        
        # Keep connection alive
        while True:
            # Just receive to keep connection alive (middleware pushes updates)
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        logger.info("[WebSocket] Client disconnected normally")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"[WebSocket] Error: {e}")
        manager.disconnect(websocket)
