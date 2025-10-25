import uvicorn

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from samples import router as samples_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the samples router
app.include_router(samples_router)


@app.get("/status")
async def status():
    """
    Simple healthcheck.
    """
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # auto-reload in dev
    )