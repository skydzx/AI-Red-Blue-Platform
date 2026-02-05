"""Response service for incident handling."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class ResponseAction(str, Enum):
    """Types of response actions."""

    INVESTIGATE = "investigate"
    CONTAIN = "contain"
    ERADICATE = "eradicate"
    RECOVER = "recover"
    CLOSE = "close"
    ESCALATE = "escalate"


class ContainmentAction(str, Enum):
    """Types of containment actions."""

    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    DISABLE_USER = "disable_user"
    STOP_SERVICE = "stop_service"
    QUARANTINE_FILE = "quarantine_file"
    REVOKE_SESSION = "revoke_session"


class IncidentContext(BaseModel):
    """Context for incident response."""

    affected_ips: list[str] = Field(default_factory=list)
    affected_hosts: list[str] = Field(default_factory=list)
    affected_users: list[str] = Field(default_factory=list)
    affected_files: list[str] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)
    timeline: list[dict] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)


class ResponseTask(BaseModel):
    """Response task to be executed."""

    id: str = Field(default_factory=generate_uuid)
    action: ResponseAction
    target: str
    status: str = "pending"
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    notes: str = ""


class ResponseService:
    """Service for incident response coordination."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("response-service")
        self.pending_tasks: list[ResponseTask] = []
        self.completed_tasks: list[ResponseTask] = []

    async def create_task(
        self,
        action: ResponseAction,
        target: str,
        assigned_to: Optional[str] = None,
    ) -> ResponseTask:
        """Create a new response task."""
        task = ResponseTask(
            action=action,
            target=target,
            assigned_to=assigned_to,
        )
        self.pending_tasks.append(task)
        self.logger.info(f"Created response task: {action.value} on {target}")
        return task

    async def execute_task(
        self,
        task_id: str,
    ) -> Optional[ResponseTask]:
        """Execute a response task."""
        task = next((t for t in self.pending_tasks if t.id == task_id), None)
        if task:
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.result = {"success": True}
            self.completed_tasks.append(task)
            self.logger.info(f"Executed response task: {task.id}")
        return task

    async def contain_host(
        self,
        hostname: str,
        reason: str = "",
    ) -> ResponseTask:
        """Create containment task for a host."""
        return await self.create_task(
            ResponseAction.CONTAIN,
            f"host:{hostname}",
        )

    async def block_ip(
        self,
        ip_address: str,
        reason: str = "",
    ) -> ResponseTask:
        """Create task to block an IP address."""
        return await self.create_task(
            ResponseAction.CONTAIN,
            f"ip:{ip_address}",
        )

    async def isolate_network(
        self,
        asset_id: str,
    ) -> ResponseTask:
        """Create task to isolate a network asset."""
        return await self.create_task(
            ResponseAction.CONTAIN,
            f"network:{asset_id}",
        )

    async def get_pending_tasks(self) -> list[ResponseTask]:
        """Get all pending response tasks."""
        return self.pending_tasks

    async def get_completed_tasks(self) -> list[ResponseTask]:
        """Get all completed response tasks."""
        return self.completed_tasks
