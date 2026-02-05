"""Alert models and handlers for AI Red Blue Platform."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import PlatformException


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(str, Enum):
    """Types of security alerts."""

    INTRUSION = "intrusion"
    MALWARE = "malware"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DENIAL_OF_SERVICE = "dos"
    VULNERABILITY = "vulnerability"
    POLICY_VIOLATION = "policy_violation"
    ANOMALY = "anomaly"
    RECONNAISSANCE = "reconnaissance"
    LATERAL_MOVEMENT = "lateral_movement"
    COMMAND_CONTROL = "command_control"
    EXFILTRATION = "exfiltration"


class AlertStatus(str, Enum):
    """Alert status states."""

    NEW = "new"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"
    DISMISSED = "dismissed"


class AlertSource(BaseModel):
    """Source of the alert."""

    type: str
    name: str
    id: Optional[str] = None
    ip: Optional[str] = None
    hostname: Optional[str] = None
    user: Optional[str] = None


class AlertContext(BaseModel):
    """Contextual information about the alert."""

    affected_assets: list[str] = Field(default_factory=list)
    affected_users: list[str] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)
    tags: dict[str, str] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class Alert(BaseModel):
    """Security alert model."""

    id: str
    title: str
    description: str
    severity: AlertSeverity
    type: AlertType
    status: AlertStatus = AlertStatus.NEW

    # Source information
    source: AlertSource

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Context
    context: AlertContext = Field(default_factory=AlertContext)

    # Related data
    raw_event: Optional[dict[str, Any]] = None
    related_alerts: list[str] = Field(default_factory=list)
    investigations: list[str] = Field(default_factory=list)

    # Confidence and scoring
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)

    # Assignment
    assigned_to: Optional[str] = None
    team: Optional[str] = None

    # Notes and timeline
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[dict[str, Any]] = Field(default_factory=list)

    def add_note(self, user: str, content: str) -> None:
        """Add a note to the alert."""
        self.notes.append({
            "user": user,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def add_timeline_event(
        self,
        event_type: str,
        description: str,
        user: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        """Add an event to the alert timeline."""
        self.timeline.append({
            "type": event_type,
            "description": description,
            "user": user,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def update_status(self, new_status: AlertStatus, user: Optional[str] = None) -> None:
        """Update the alert status."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        if new_status in [AlertStatus.CLOSED, AlertStatus.DISMISSED, AlertStatus.RECOVERED]:
            self.resolved_at = datetime.now(timezone.utc)

        self.add_timeline_event(
            "status_change",
            f"Status changed from {old_status} to {new_status}",
            user=user,
            data={"old_status": old_status, "new_status": new_status},
        )

    def calculate_risk_score(self) -> float:
        """Calculate risk score based on severity and confidence."""
        severity_weights = {
            AlertSeverity.CRITICAL: 100,
            AlertSeverity.HIGH: 75,
            AlertSeverity.MEDIUM: 50,
            AlertSeverity.LOW: 25,
            AlertSeverity.INFO: 10,
        }
        base_score = severity_weights.get(self.severity, 0)
        return min(base_score * (0.5 + 0.5 * self.confidence), 100.0)


class AlertHandler:
    """Base class for alert handlers."""

    def handle(self, alert: Alert) -> bool:
        """Handle an alert. Returns True if handled successfully."""
        raise NotImplementedError


class AlertManager:
    """Manager for handling and routing alerts."""

    def __init__(self):
        self.handlers: list[AlertHandler] = []
        self.alerts: dict[str, Alert] = {}

    def register_handler(self, handler: AlertHandler) -> None:
        """Register an alert handler."""
        self.handlers.append(handler)

    def process_alert(self, alert: Alert) -> bool:
        """Process an alert through all registered handlers."""
        self.alerts[alert.id] = alert

        for handler in self.handlers:
            try:
                if handler.handle(alert):
                    continue
            except Exception as e:
                # Log error but continue with other handlers
                continue

        return True

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self.alerts.get(alert_id)

    def get_alerts_by_status(self, status: AlertStatus) -> list[Alert]:
        """Get all alerts with a specific status."""
        return [a for a in self.alerts.values() if a.status == status]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> list[Alert]:
        """Get all alerts with a specific severity."""
        return [a for a in self.alerts.values() if a.severity == severity]

    def get_statistics(self) -> dict[str, Any]:
        """Get alert statistics."""
        return {
            "total": len(self.alerts),
            "by_status": {s.value: len(self.get_alerts_by_status(s)) for s in AlertStatus},
            "by_severity": {s.value: len(self.get_alerts_by_severity(s)) for s in AlertSeverity},
        }
