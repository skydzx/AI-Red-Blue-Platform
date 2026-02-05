"""Web Dashboard application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_red_blue_common import get_settings, setup_logging


settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    setup_logging()
    yield


app = FastAPI(
    title="AI Red Blue Platform - Dashboard",
    description="Security Operations Dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Red Blue Platform Dashboard",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/v1/alerts")
async def get_alerts():
    """Get alerts (placeholder)."""
    return {"alerts": [], "total": 0}


@app.get("/api/v1/detections")
async def get_detections():
    """Get detections (placeholder)."""
    return {"detections": [], "total": 0}


@app.get("/api/v1/statistics")
async def get_statistics():
    """Get platform statistics."""
    return {
        "alerts": {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
        "detections": {"total": 0, "enabled": 0},
        "incidents": {"active": 0, "resolved": 0},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
