import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing modules that need them
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sample import app as samples_app
from testrunners import router as tests_router
from db.redis import redis_client
from db.elasticsearch import elasticsearch_client
from api.websocket_routes import router as websocket_router
import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress verbose Elasticsearch transport logs
logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
async def status():
    """
    Simple healthcheck.
    """
    return JSONResponse({"status": "ok"})

@app.get("/redis/status")
async def ping_redis():
    """
    Check Redis connection.
    """
    if await redis_client.ping():
        return JSONResponse({"status": "ok"})
    else:
        raise HTTPException(status_code=500, detail="Redis connection failed")

@app.get("/elastic/status")
async def ping_elasticsearch():
    """
    Check Elasticsearch connection.
    """
    try:
        if await elasticsearch_client.ping():
            return JSONResponse({"status": "ok"})
        else:
            raise HTTPException(status_code=500, detail="Elasticsearch connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch error: {str(e)}")

@app.get("/elastic/sample")
async def get_elasticsearch_sample():
    """
    Get one sample entry from Elasticsearch.
    """
    try:
        # Search for any document, return just 1
        results = await elasticsearch_client.search(
            index_name="api_requests",
            query={"match_all": {}},
            size=1
        )
        
        if results:
            return JSONResponse({"data": results[0], "count": len(results)})
        else:
            return JSONResponse({"data": None, "message": "No entries found in Elasticsearch"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch error: {str(e)}")

@app.get("/elastic/activity")
async def get_activity_data(days: int = 7, interval: str = 'hour'):
    """
    Get activity trends for statistics visualization.
    
    Args:
        days: Number of days to fetch (default: 7)
        interval: Aggregation interval - 'hour', 'day', or 'week' (default: 'hour')
    """
    from websocket import get_hourly_activity
    
    try:
        activity_data = await get_hourly_activity(days=days, interval=interval)
        if activity_data:
            return JSONResponse(activity_data)
        else:
            return JSONResponse({"data": [], "message": "No activity data available"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activity data: {str(e)}")

# Include the tests router
app.include_router(tests_router, tags=["tests"])

# Include WebSocket router
app.include_router(websocket_router, tags=["websocket"])

# Background task for periodic stats broadcasts
async def broadcast_stats_periodically():
    """
    Background task that broadcasts stats every 30 seconds.
    """
    from websocket import manager, get_recent_stats
    
    logger.info("[Stats] Starting periodic stats broadcast task")
    
    while True:
        try:
            await asyncio.sleep(30)  # Every 30 seconds
            
            if manager.get_connection_count() > 0:
                logger.info(f"[Stats] Broadcasting stats to {manager.get_connection_count()} clients")
                stats = await get_recent_stats()
                if stats:
                    await manager.broadcast({
                        "type": "stats",
                        "timestamp": datetime.now().isoformat(),
                        "stats": stats
                    })
            
        except Exception as e:
            logger.error(f"[Stats] Error broadcasting stats: {e}")
            await asyncio.sleep(5)


# Function to broadcast new requests (called by middleware)
async def broadcast_new_request(request_data: dict):
    """
    Broadcast a new request to all WebSocket clients.
    Called by middleware after logging to Elasticsearch.
    
    Args:
        request_data: The request data to broadcast
    """
    from websocket import manager
    
    if manager.get_connection_count() > 0:
        await manager.broadcast({
            "type": "new_request",
            "timestamp": datetime.now().isoformat(),
            "data": request_data
        })
        logger.debug(f"[WebSocket] Broadcasted new request to {manager.get_connection_count()} clients")


# Mount the samples app (this should be LAST so it doesn't catch all routes)
app.mount("", samples_app)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # auto-reload in dev
    )