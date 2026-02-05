"""Scheduler service for task scheduling."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class ScheduleType(str, Enum):
    """Types of schedules."""

    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"
    DAILY = "daily"
    WEEKLY = "weekly"


class ScheduledTask(BaseModel):
    """Scheduled task definition."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    task_type: str  # workflow, command, scan

    # Schedule
    schedule_type: ScheduleType
    schedule_value: str  # cron expression, interval, datetime

    # Execution
    workflow_id: Optional[str] = None
    command: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)

    # Status
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[str] = None

    # Statistics
    total_runs: int = 0
    success_count: int = 0
    failure_count: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None


class SchedulerService:
    """Service for scheduling tasks."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("scheduler-service")
        self.tasks: dict[str, ScheduledTask] = {}

    def create_task(
        self,
        name: str,
        task_type: str,
        schedule_type: ScheduleType,
        schedule_value: str,
        created_by: Optional[str] = None,
    ) -> ScheduledTask:
        """Create a scheduled task."""
        task = ScheduledTask(
            name=name,
            task_type=task_type,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            created_by=created_by,
        )
        self.tasks[task.id] = task
        self.logger.info(f"Created scheduled task: {name}")
        return task

    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task."""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = True
            self.logger.info(f"Enabled scheduled task: {task.name}")
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task."""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = False
            self.logger.info(f"Disabled scheduled task: {task.name}")
            return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a scheduled task."""
        task = self.tasks.pop(task_id, None)
        if task:
            self.logger.info(f"Deleted scheduled task: {task.name}")
            return True
        return False

    def get_enabled_tasks(self) -> list[ScheduledTask]:
        """Get all enabled tasks."""
        return [t for t in self.tasks.values() if t.enabled]

    def get_due_tasks(self) -> list[ScheduledTask]:
        """Get all tasks that are due to run."""
        now = datetime.now(timezone.utc)
        return [
            t for t in self.get_enabled_tasks()
            if t.next_run and t.next_run <= now
        ]

    def update_run_status(
        self,
        task_id: str,
        success: bool,
    ) -> bool:
        """Update the run status of a task."""
        task = self.tasks.get(task_id)
        if task:
            task.last_run = datetime.now(timezone.utc)
            task.total_runs += 1
            if success:
                task.success_count += 1
                task.last_status = "success"
            else:
                task.failure_count += 1
                task.last_status = "failed"
            return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "total_tasks": len(self.tasks),
            "enabled_tasks": len(self.get_enabled_tasks()),
            "total_runs": sum(t.total_runs for t in self.tasks.values()),
            "success_rate": (
                sum(t.success_count for t in self.tasks.values()) /
                max(sum(t.total_runs for t in self.tasks.values()), 1)
            ) * 100,
        }
