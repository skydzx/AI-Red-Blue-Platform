"""Web Dashboard application entry point."""

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai_red_blue_common import get_settings, setup_logging, get_logger
from ai_red_blue_core import Alert, AlertSeverity, AlertStatus, AlertType, DetectionEngine, DetectionRule, DetectionType
from ai_red_blue_ai import OpenAIProvider, AnthropicProvider, ProviderConfig, ProviderType, ChatMessage, ChatRole
from ai_red_blue_security import SecurityUtils


# Initialize
settings = get_settings()
setup_logging()
logger = get_logger("dashboard")

# In-memory storage for demo (replace with database in production)
alerts_db: dict[str, Alert] = {}
detections_db: dict[str, DetectionRule] = {}


# Pydantic models for API
class AlertCreate(BaseModel):
    """Alert creation model."""
    title: str
    description: str
    severity: str
    type: str
    source: str
    target: Optional[str] = None
    artifacts: list[str] = Field(default_factory=list)


class AlertUpdate(BaseModel):
    """Alert update model."""
    status: Optional[str] = None
    assignee: Optional[str] = None
    notes: Optional[str] = None


class DetectionCreate(BaseModel):
    """Detection rule creation model."""
    name: str
    description: str
    type: str
    severity: str
    conditions: dict = Field(default_factory=dict)
    actions: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    model: Optional[str] = None
    provider: str = "openai"


# Dashboard Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Red Blue Platform Dashboard",
        "version": "0.1.0",
        "status": "running",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Alert API
@app.get("/api/v1/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
):
    """Get alerts with optional filtering."""
    alerts = list(alerts_db.values())

    if severity:
        alerts = [a for a in alerts if a.severity.value == severity]
    if status:
        alerts = [a for a in alerts if a.status.value == status]

    total = len(alerts)
    alerts = sorted(alerts, key=lambda x: x.created_at, reverse=True)[offset:offset+limit]

    return {
        "alerts": [a.model_dump() for a in alerts],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """Get a specific alert."""
    alert = alerts_db.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.model_dump()


@app.post("/api/v1/alerts")
async def create_alert(alert_data: AlertCreate):
    """Create a new alert."""
    alert = Alert(
        title=alert_data.title,
        description=alert_data.description,
        severity=AlertSeverity(alert_data.severity),
        type=AlertType(alert_data.type),
        source=alert_data.source,
        target=alert_data.target,
        artifacts=alert_data.artifacts,
    )
    alerts_db[alert.id] = alert
    logger.info(f"Created alert: {alert.id}")
    return alert.model_dump()


@app.patch("/api/v1/alerts/{alert_id}")
async def update_alert(alert_id: str, update: AlertUpdate):
    """Update an alert."""
    alert = alerts_db.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if update.status:
        alert.status = AlertStatus(update.status)
    if update.assignee:
        alert.assignee = update.assignee
    if update.notes:
        alert.notes = update.notes

    logger.info(f"Updated alert: {alert_id}")
    return alert.model_dump()


# Detection API
@app.get("/api/v1/detections")
async def get_detections(
    dtype: Optional[str] = None,
    enabled: Optional[bool] = None,
):
    """Get detection rules."""
    detections = list(detections_db.values())

    if dtype:
        detections = [d for d in detections if d.type.value == dtype]
    if enabled is not None:
        detections = [d for d in detections if d.status.value == ("enabled" if enabled else "disabled")]

    return {
        "detections": [d.model_dump() for d in detections],
        "total": len(detections),
    }


@app.post("/api/v1/detections")
async def create_detection(detection_data: DetectionCreate):
    """Create a new detection rule."""
    rule = DetectionRule(
        name=detection_data.name,
        description=detection_data.description,
        type=DetectionType(detection_data.type),
        severity=AlertSeverity(detection_data.severity),
        conditions=detection_data.conditions,
        actions=detection_data.actions,
    )
    detections_db[rule.id] = rule
    logger.info(f"Created detection rule: {rule.id}")
    return rule.model_dump()


# Statistics API
@app.get("/api/v1/statistics")
async def get_statistics():
    """Get platform statistics."""
    alerts = list(alerts_db.values())
    detections = list(detections_db.values())

    return {
        "alerts": {
            "total": len(alerts),
            "critical": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
            "high": len([a for a in alerts if a.severity == AlertSeverity.HIGH]),
            "medium": len([a for a in alerts if a.severity == AlertSeverity.MEDIUM]),
            "low": len([a for a in alerts if a.severity == AlertSeverity.LOW]),
            "by_status": {
                "open": len([a for a in alerts if a.status == AlertStatus.OPEN]),
                "investigating": len([a for a in alerts if a.status == AlertStatus.INVESTIGATING]),
                "resolved": len([a for a in alerts if a.status == AlertStatus.RESOLVED]),
                "closed": len([a for a in alerts if a.status == AlertStatus.CLOSED]),
            }
        },
        "detections": {
            "total": len(detections),
            "enabled": len([d for d in detections if d.status.value == "enabled"]),
            "disabled": len([d for d in detections if d.status.value == "disabled"]),
        },
        "threat_intel": {
            "iocs_count": 0,
            "feeds_count": 0,
        },
    }


# AI Chat API
@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """AI chat endpoint."""
    try:
        if request.provider == "openai":
            config = ProviderConfig(
                type=ProviderType.OPENAI,
                name="openai",
                api_key=settings.openai_api_key or "",
            )
            provider = OpenAIProvider(config)
        elif request.provider == "anthropic":
            config = ProviderConfig(
                type=ProviderType.ANTHROPIC,
                name="anthropic",
                api_key=settings.anthropic_api_key or "",
            )
            provider = AnthropicProvider(config)
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")

        messages = [
            ChatMessage(role=ChatRole.USER, content=request.message)
        ]

        response = await provider.chat(messages, model=request.model)

        return {
            "response": response.content,
            "provider": request.provider,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Security Utils API
@app.post("/api/v1/utils/hash")
async def calculate_hash(data: dict):
    """Calculate hash of data."""
    content = data.get("content", "").encode("utf-8")
    algorithm = data.get("algorithm", "sha256")
    return {
        "hash": SecurityUtils.generate_fingerprint(content).get(algorithm, ""),
        "algorithm": algorithm,
    }


@app.post("/api/v1/utils/encode")
async def encode_data(data: dict):
    """Encode data."""
    content = data.get("content", "").encode("utf-8")
    encoding = data.get("encoding", "base64")
    return {
        "encoded": SecurityUtils.encode_payload(content, encoding),
        "encoding": encoding,
    }


@app.post("/api/v1/utils/decode")
async def decode_data(data: dict):
    """Decode data."""
    encoded = data.get("encoded", "")
    encoding = data.get("encoding", "base64")
    try:
        decoded = SecurityUtils.decode_payload(encoded, encoding)
        return {
            "decoded": decoded.decode("utf-8", errors="replace"),
            "encoding": encoding,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decode failed: {str(e)}")


# Demo data endpoint
@app.post("/api/v1/demo/seed")
async def seed_demo_data():
    """Seed demo data for testing."""
    # Create sample alerts
    sample_alerts = [
        Alert(
            title="Suspicious PowerShell Execution",
            description="Detected PowerShell execution with encoded commands",
            severity=AlertSeverity.HIGH,
            type=AlertType.THREAT_DETECTION,
            source="EDR",
            target="workstation-01",
        ),
        Alert(
            title="Brute Force Attempt Detected",
            description="Multiple failed login attempts from IP 192.168.1.100",
            severity=AlertSeverity.MEDIUM,
            type=AlertType.INTRUSION_DETECTION,
            source="WAF",
            target="web-server-01",
        ),
        Alert(
            title="Malware Signature Detected",
            description="Known malware signature found in file",
            severity=AlertSeverity.CRITICAL,
            type=AlertType.MALWARE_DETECTION,
            source="AV",
            target="file-server",
        ),
    ]

    for alert in sample_alerts:
        alerts_db[alert.id] = alert

    # Create sample detection rules
    sample_detections = [
        DetectionRule(
            name="Suspicious PowerShell",
            description="Detect encoded PowerShell commands",
            type=DetectionType.SIGNATURE,
            severity=AlertSeverity.HIGH,
            conditions={"process.name": "powershell.exe"},
            actions=["alert", "block"],
        ),
        DetectionRule(
            name="Lateral Movement",
            description="Detect potential lateral movement",
            type=DetectionType.BEHAVIORAL,
            severity=AlertSeverity.HIGH,
            conditions={"event.type": "network_connection"},
            actions=["alert"],
        ),
    ]

    for detection in sample_detections:
        detections_db[detection.id] = detection

    return {
        "message": "Demo data seeded",
        "alerts_created": len(sample_alerts),
        "detections_created": len(sample_detections),
    }


@lifespan
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    setup_logging()
    logger.info("Dashboard started")
    yield
    logger.info("Dashboard stopped")


app = FastAPI(
    title="AI Red Blue Platform - Dashboard",
    description="Security Operations Dashboard API",
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


if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
