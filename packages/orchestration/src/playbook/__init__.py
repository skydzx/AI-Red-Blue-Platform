"""Playbook service for incident response playbooks."""

from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class PlaybookStepType(str, Enum):
    """Types of playbook steps."""

    MANUAL = "manual"
    AUTOMATED = "automated"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    CONDITION = "condition"


class Playbook(BaseModel):
    """Incident response playbook."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    description: str
    category: str  # malware, phishing, data_breach, etc.

    # Steps
    steps: list[dict] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)

    # Metadata
    version: str = "1.0"
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Usage
    incident_types: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int = 60

    # Status
    enabled: bool = True


class PlaybookExecution(BaseModel):
    """Execution of a playbook."""

    id: str = Field(default_factory=generate_uuid)
    playbook_id: str
    playbook_name: str

    # Incident context
    incident_id: Optional[str] = None
    incident_type: Optional[str] = None

    # Execution status
    status: str = "pending"
    current_step: int = 0

    # Timing
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Results
    completed_steps: list[dict] = Field(default_factory=list)
    skipped_steps: list[int] = Field(default_factory=list)
    failed_steps: list[int] = Field(default_factory=list)

    # Notes
    notes: list[dict] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)

    # Execution details
    executed_by: Optional[str] = None
    execution_type: str = "manual"  # manual, automated, hybrid

    def complete(self, success: bool) -> None:
        """Mark playbook execution as completed."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = "completed" if success else "failed"

    def add_note(
        self,
        step: int,
        note: str,
        user: Optional[str] = None,
    ) -> None:
        """Add a note to the execution."""
        self.notes.append({
            "step": step,
            "note": note,
            "user": user,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


class PlaybookService:
    """Service for managing incident response playbooks."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("playbook-service")
        self.playbooks: dict[str, Playbook] = {}
        self.executions: dict[str, PlaybookExecution] = {}

    def create_playbook(
        self,
        name: str,
        description: str,
        category: str,
        created_by: Optional[str] = None,
    ) -> Playbook:
        """Create a new playbook."""
        playbook = Playbook(
            name=name,
            description=description,
            category=category,
            created_by=created_by,
        )
        self.playbooks[playbook.id] = playbook
        self.logger.info(f"Created playbook: {name}")
        return playbook

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Get a playbook by ID."""
        return self.playbooks.get(playbook_id)

    def get_playbooks_by_category(self, category: str) -> list[Playbook]:
        """Get all playbooks in a category."""
        return [p for p in self.playbooks.values() if p.category == category]

    def get_playbooks_by_incident_type(self, incident_type: str) -> list[Playbook]:
        """Get all playbooks for an incident type."""
        return [
            p for p in self.playbooks.values()
            if incident_type in p.incident_types
        ]

    async def execute(
        self,
        playbook_id: str,
        incident_id: Optional[str] = None,
        executed_by: Optional[str] = None,
    ) -> PlaybookExecution:
        """Execute a playbook."""
        playbook = self.playbooks.get(playbook_id)
        if not playbook:
            raise ValueError(f"Playbook {playbook_id} not found")

        execution = PlaybookExecution(
            playbook_id=playbook_id,
            playbook_name=playbook.name,
            incident_id=incident_id,
            executed_by=executed_by,
        )
        self.executions[execution.id] = execution

        self.logger.info(f"Starting playbook execution: {playbook.name}")
        # Execute steps (placeholder)
        execution.complete(success=True)

        return execution

    def get_execution(self, execution_id: str) -> Optional[PlaybookExecution]:
        """Get a playbook execution by ID."""
        return self.executions.get(execution_id)

    def list_executions(
        self,
        playbook_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[PlaybookExecution]:
        """List playbook executions."""
        results = list(self.executions.values())
        if playbook_id:
            results = [e for e in results if e.playbook_id == playbook_id]
        if status:
            results = [e for e in results if e.status == status]
        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get playbook statistics."""
        return {
            "total_playbooks": len(self.playbooks),
            "enabled_playbooks": len([p for p in self.playbooks.values() if p.enabled]),
            "total_executions": len(self.executions),
            "completed_executions": len(
                [e for e in self.executions.values() if e.status == "completed"]
            ),
        }
