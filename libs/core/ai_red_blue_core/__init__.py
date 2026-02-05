"""Core analysis library for AI Red Blue Platform."""

from .alert import (
    Alert,
    AlertSeverity,
    AlertType,
    AlertStatus,
    AlertHandler,
    AlertManager,
)
from .attack import (
    AttackPattern,
    AttackAnalyzer,
    AttackChain,
    AttackPhase,
)
from .detection import (
    DetectionRule,
    DetectionEngine,
    DetectionResult,
    DetectionType,
)

__all__ = [
    # Alert
    "Alert",
    "AlertSeverity",
    "AlertType",
    "AlertStatus",
    "AlertHandler",
    "AlertManager",
    # Attack
    "AttackPattern",
    "AttackAnalyzer",
    "AttackChain",
    "AttackPhase",
    # Detection
    "DetectionRule",
    "DetectionEngine",
    "DetectionResult",
    "DetectionType",
]
