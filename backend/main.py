import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sample import app as samples_app
from testrunners import router as tests_router
from db.redis import redis_client
from db.elasticsearch import elasticsearch_client

# Load environment variables from .env file
load_dotenv()


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

# Include the tests router
app.include_router(tests_router, tags=["tests"])

# Mount the samples app (this should be LAST so it doesn't catch all routes)
app.mount("", samples_app)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # auto-reload in dev
    )