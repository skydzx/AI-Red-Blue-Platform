"""Detection engine for AI Red Blue Platform."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class DetectionType(str, Enum):
    """Types of detection."""

    SIGNATURE = "signature"
    ANOMALY = "anomaly"
    BEHAVIORAL = "behavioral"
    CORRELATION = "correlation"
    HEURISTIC = "heuristic"
    ML_BASED = "ml_based"
    THREAT_INTELLIGENCE = "threat_intelligence"


class DetectionSeverity(str, Enum):
    """Detection severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DetectionStatus(str, Enum):
    """Detection status."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class DetectionRule(BaseModel):
    """Detection rule model."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    description: str
    type: DetectionType
    severity: DetectionSeverity
    status: DetectionStatus = DetectionStatus.ENABLED

    # Rule content
    conditions: dict[str, Any] = Field(default_factory=dict)
    logic: Optional[str] = None  # SIEM query, SPL, etc.

    # Scope
    data_sources: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    users: list[str] = Field(default_factory=list)

    # Thresholds
    threshold: int = 1
    time_window_seconds: Optional[int] = None

    # Response
    actions: list[str] = Field(default_factory=list)
    alert_template: Optional[str] = None

    # Metadata
    tags: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    author: Optional[str] = None
    version: str = "1.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    enabled_at: Optional[datetime] = None

    # Performance
    avg_processing_time_ms: float = 0.0
    false_positive_rate: float = 0.0
    true_positive_rate: float = 0.0

    def enable(self) -> None:
        """Enable the detection rule."""
        self.status = DetectionStatus.ENABLED
        self.enabled_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def disable(self) -> None:
        """Disable the detection rule."""
        self.status = DetectionStatus.DISABLED
        self.updated_at = datetime.now(timezone.utc)

    def update_metrics(
        self,
        processing_time_ms: float,
        is_fp: bool,
        is_tp: bool,
    ) -> None:
        """Update rule performance metrics."""
        # Update rolling average of processing time
        self.avg_processing_time_ms = (
            (self.avg_processing_time_ms * 0.9) + (processing_time_ms * 0.1)
        )

        # Update false positive rate
        if is_fp:
            self.false_positive_rate = (
                (self.false_positive_rate * 0.95) + (0.05)
            )
        else:
            self.false_positive_rate = self.false_positive_rate * 0.95

        # Update true positive rate
        if is_tp:
            self.true_positive_rate = (
                (self.true_positive_rate * 0.95) + (0.05)
            )
        else:
            self.true_positive_rate = self.true_positive_rate * 0.95


class DetectionResult(BaseModel):
    """Result of a detection evaluation."""

    id: str = Field(default_factory=generate_uuid)
    rule_id: str
    rule_name: str
    detected: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Detection details
    matched_conditions: dict[str, Any] = Field(default_factory=dict)
    severity: Optional[DetectionSeverity] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Related data
    events: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)

    # Context
    source_ip: Optional[str] = None
    target_asset: Optional[str] = None
    target_user: Optional[str] = None

    # Processing
    processing_time_ms: float = 0.0
    enrichment: dict[str, Any] = Field(default_factory=dict)


class DetectionEngine:
    """Engine for evaluating detections against events."""

    def __init__(self):
        self.rules: dict[str, DetectionRule] = {}
        self.rule_functions: dict[str, Callable] = {}

    def register_rule(self, rule: DetectionRule) -> None:
        """Register a detection rule."""
        self.rules[rule.id] = rule

    def unregister_rule(self, rule_id: str) -> None:
        """Unregister a detection rule."""
        self.rules.pop(rule_id, None)
        self.rule_functions.pop(rule_id, None)

    def get_enabled_rules(self) -> list[DetectionRule]:
        """Get all enabled detection rules."""
        return [r for r in self.rules.values() if r.status == DetectionStatus.ENABLED]

    def get_rules_by_type(self, dtype: DetectionType) -> list[DetectionRule]:
        """Get all rules of a specific type."""
        return [r for r in self.rules.values() if r.type == dtype]

    def get_rules_by_severity(self, severity: DetectionSeverity) -> list[DetectionRule]:
        """Get all rules of a specific severity."""
        return [r for r in self.rules.values() if r.severity == severity]

    async def evaluate(
        self,
        rule_id: str,
        event: dict[str, Any],
    ) -> DetectionResult:
        """Evaluate a single rule against an event."""
        rule = self.rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        if rule.status != DetectionStatus.ENABLED:
            return DetectionResult(
                rule_id=rule_id,
                rule_name=rule.name,
                detected=False,
                matched_conditions={},
            )

        start_time = datetime.now(timezone.utc)

        # Evaluate conditions
        matched = self._evaluate_conditions(rule.conditions, event)

        processing_time = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        result = DetectionResult(
            rule_id=rule_id,
            rule_name=rule.name,
            detected=matched,
            matched_conditions=matched if isinstance(matched, dict) else {},
            processing_time_ms=processing_time,
        )

        # Update rule metrics
        rule.update_metrics(
            processing_time,
            is_fp=False,  # Will be updated based on feedback
            is_tp=matched,
        )

        return result

    async def evaluate_all(
        self,
        event: dict[str, Any],
    ) -> list[DetectionResult]:
        """Evaluate all enabled rules against an event."""
        results = []
        for rule in self.get_enabled_rules():
            result = await self.evaluate(rule.id, event)
            results.append(result)
        return results

    def _evaluate_conditions(
        self,
        conditions: dict[str, Any],
        event: dict[str, Any],
    ) -> bool:
        """Evaluate rule conditions against an event."""
        if not conditions:
            return True

        # Simple condition evaluation - can be extended
        for key, expected in conditions.items():
            if key.startswith("not_"):
                # Negative condition
                actual_key = key[4:]
                actual = self._get_nested_value(event, actual_key)
                if actual == expected:
                    return False
            else:
                actual = self._get_nested_value(event, key)
                if actual != expected:
                    return False

        return True

    def _get_nested_value(self, obj: dict, key: str, default: Any = None) -> Any:
        """Get a value from a nested dictionary using dot notation."""
        keys = key.split(".")
        value = obj
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_statistics(self) -> dict[str, Any]:
        """Get detection engine statistics."""
        enabled = self.get_enabled_rules()

        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(enabled),
            "disabled_rules": len([r for r in self.rules.values() if r.status == DetectionStatus.DISABLED]),
            "by_type": {
                t.value: len(self.get_rules_by_type(t)) for t in DetectionType
            },
            "by_severity": {
                s.value: len(self.get_rules_by_severity(s)) for s in DetectionSeverity
            },
            "avg_processing_time_ms": sum(
                r.avg_processing_time_ms for r in enabled
            ) / len(enabled) if enabled else 0,
        }
