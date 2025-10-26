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
import os
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

@app.get("/mitigations/active")
async def get_active_mitigations():
    """
    Get all current active mitigations from Redis.
    Returns mitigations for both IPs and users.
    """
    try:
        mitigations = []
        
        # Scan for all mitigation keys in Redis
        cursor = 0
        while True:
            cursor, keys = await redis_client.client.scan(cursor, match="mitigation:*", count=100)
            
            for key in keys:
                value = await redis_client.get_value(key)
                if value and value != "none":
                    # Parse the key to extract type and entity
                    parts = key.split(":")
                    if len(parts) == 3:
                        entity_type = parts[1]  # "ip" or "user"
                        entity = parts[2]
                        
                        # Get TTL if available
                        ttl = await redis_client.client.ttl(key)
                        
                        mitigations.append({
                            "entity_type": entity_type,
                            "entity": entity,
                            "mitigation": value,
                            "ttl": ttl if ttl > 0 else None
                        })
            
            if cursor == 0:
                break
        
        return JSONResponse({
            "success": True,
            "count": len(mitigations),
            "mitigations": mitigations
        })
    except Exception as e:
        logger.error(f"Error fetching active mitigations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching active mitigations: {str(e)}")

@app.get("/mitigations/history")
async def get_mitigation_history(limit: int = 100):
    """
    Get past mitigations from ChromaDB.
    
    Args:
        limit: Maximum number of results to return (default: 100)
    """
    import httpx
    
    try:
        # Call ChromaDB service
        async with httpx.AsyncClient() as client:
            chromadb_url = os.getenv("CHROMADB_URL", "http://chromadb:9000")
            response = await client.get(f"{chromadb_url}/all")
            
            if response.status_code == 200:
                data = response.json()
                
                # Sort by timestamp (most recent first) and limit
                items = data.get("items", [])
                items.sort(key=lambda x: x.get("metadata", {}).get("timestamp", ""), reverse=True)
                items = items[:limit]
                
                return JSONResponse({
                    "success": True,
                    "count": len(items),
                    "mitigations": items
                })
            else:
                raise HTTPException(status_code=response.status_code, detail="ChromaDB request failed")
    except Exception as e:
        logger.error(f"Error fetching mitigation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching mitigation history: {str(e)}")

@app.get("/mitigations/search")
async def search_mitigations(query: str, k: int = 10):
    """
    Search past mitigations by semantic similarity.
    
    Args:
        query: Search query text
        k: Number of results to return (default: 10)
    """
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            chromadb_url = os.getenv("CHROMADB_URL", "http://chromadb:9000")
            response = await client.post(
                f"{chromadb_url}/query",
                json={"query_text": query, "k": k}
            )
            
            if response.status_code == 200:
                return JSONResponse(response.json())
            else:
                raise HTTPException(status_code=response.status_code, detail="ChromaDB search failed")
    except Exception as e:
        logger.error(f"Error searching mitigations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching mitigations: {str(e)}")

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