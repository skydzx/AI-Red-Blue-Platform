"""Detection service for monitoring and alerting."""

from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid
from ai_red_blue_core import (
    DetectionRule,
    DetectionEngine,
    DetectionResult as CoreDetectionResult,
)


class DetectionEvent(BaseModel):
    """Security detection event."""

    id: str = Field(default_factory=generate_uuid)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Event details
    event_type: str
    source: str
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    user: Optional[str] = None
    asset: Optional[str] = None

    # Raw event
    raw_data: dict[str, Any] = Field(default_factory=dict)
    event_data: dict[str, Any] = Field(default_factory=dict)

    # Processing
    processed: bool = False
    detection_result: Optional[CoreDetectionResult] = None


class DetectionResponse(BaseModel):
    """Response to a detection."""

    detection_id: str
    response_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Actions taken
    alert_generated: bool = False
    alert_id: Optional[str] = None
    blocked: bool = False
    quarantined: bool = False
    logged: bool = True

    # Details
    details: dict[str, Any] = Field(default_factory=dict)


class DetectionService:
    """Service for managing security detection."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("detection-service")
        self.engine = DetectionEngine()
        self.active_rules: dict[str, DetectionRule] = {}

    async def process_event(
        self,
        event: DetectionEvent,
    ) -> DetectionResponse:
        """Process a detection event."""
        response = DetectionResponse(
            detection_id=event.id,
            response_type="process",
        )

        # Evaluate against all enabled rules
        results = await self.engine.evaluate_all(event.raw_data)

        # Check for matches
        matches = [r for r in results if r.detected]

        if matches:
            response.alert_generated = True
            response.alert_id = generate_uuid()
            response.details["matched_rules"] = [r.rule_id for r in matches]

        response.details["rules_evaluated"] = len(results)
        self.logger.info(f"Processed event: {len(results)} rules evaluated")

        return response

    async def create_rule(
        self,
        rule: DetectionRule,
    ) -> DetectionRule:
        """Create a new detection rule."""
        self.active_rules[rule.id] = rule
        self.engine.register_rule(rule)
        self.logger.info(f"Created detection rule: {rule.name}")
        return rule

    async def update_rule(
        self,
        rule_id: str,
        updates: dict[str, Any],
    ) -> Optional[DetectionRule]:
        """Update an existing detection rule."""
        rule = self.active_rules.get(rule_id)
        if rule:
            for key, value in updates.items():
                setattr(rule, key, value)
            self.logger.info(f"Updated detection rule: {rule.name}")
        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a detection rule."""
        rule = self.active_rules.pop(rule_id, None)
        if rule:
            self.engine.unregister_rule(rule_id)
            self.logger.info(f"Deleted detection rule: {rule.name}")
            return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get detection service statistics."""
        return {
            "active_rules": len(self.active_rules),
            "engine_stats": self.engine.get_statistics(),
        }
