import uvicorn

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sample import app as samples_app
from db.redis import redis_client
from db.elasticsearch import elasticsearch_client


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the samples app
app.mount("", samples_app)


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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # auto-reload in dev
    )