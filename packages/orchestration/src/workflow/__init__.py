"""Workflow service for orchestrating security operations."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """A step in a workflow."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    step_type: str  # task, approval, condition, parallel
    action: str  # The action to execute
    parameters: dict[str, Any] = Field(default_factory=dict)

    # Flow control
    next_on_success: Optional[str] = None  # Next step ID
    next_on_failure: Optional[str] = None
    condition: Optional[str] = None  # Expression for conditional steps

    # Execution
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None

    # Retry
    retry_count: int = 0
    max_retries: int = 3


class Workflow(BaseModel):
    """Workflow definition."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    description: str = ""

    # Steps
    steps: list[WorkflowStep] = Field(default_factory=list)
    start_step_id: Optional[str] = None

    # Metadata
    version: str = "1.0"
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Configuration
    timeout_seconds: int = 3600
    parallel_execution: bool = False
    auto_start: bool = False

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        return next((s for s in self.steps if s.id == step_id), None)

    def get_next_step(
        self,
        current_step: WorkflowStep,
        success: bool,
    ) -> Optional[WorkflowStep]:
        """Get the next step based on execution result."""
        next_id = current_step.next_on_success if success else current_step.next_on_failure
        if next_id:
            return self.get_step(next_id)
        return None


class WorkflowExecution(BaseModel):
    """Execution instance of a workflow."""

    id: str = Field(default_factory=generate_uuid)
    workflow_id: str
    workflow_name: str

    # Status
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_id: Optional[str] = None

    # Timing
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None

    # Results
    step_results: dict[str, dict] = Field(default_factory=dict)
    overall_result: dict[str, Any] = Field(default_factory=dict)

    # Execution context
    context: dict[str, Any] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)

    # Error handling
    error: Optional[str] = None
    error_step_id: Optional[str] = None

    def complete(self, success: bool) -> None:
        """Mark execution as completed."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED

    def add_step_result(
        self,
        step_id: str,
        result: dict[str, Any],
    ) -> None:
        """Add result from a step execution."""
        self.step_results[step_id] = result


class WorkflowService:
    """Service for managing workflows."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("workflow-service")
        self.workflows: dict[str, Workflow] = {}
        self.executions: dict[str, WorkflowExecution] = {}

    def create_workflow(
        self,
        name: str,
        description: str = "",
        created_by: Optional[str] = None,
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            name=name,
            description=description,
            created_by=created_by,
        )
        self.workflows[workflow.id] = workflow
        self.logger.info(f"Created workflow: {name}")
        return workflow

    def add_step(
        self,
        workflow_id: str,
        step: WorkflowStep,
    ) -> Optional[Workflow]:
        """Add a step to a workflow."""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            workflow.steps.append(step)
            workflow.updated_at = datetime.now(timezone.utc)
        return workflow

    async def execute(
        self,
        workflow_id: str,
        context: Optional[dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            context=context or {},
            status=WorkflowStatus.RUNNING,
        )
        self.executions[execution.id] = execution

        self.logger.info(f"Starting workflow execution: {workflow.name}")
        # Execute steps (placeholder)
        execution.complete(success=True)

        return execution

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        return self.executions.get(execution_id)

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
    ) -> list[WorkflowExecution]:
        """List workflow executions."""
        results = list(self.executions.values())
        if workflow_id:
            results = [e for e in results if e.workflow_id == workflow_id]
        if status:
            results = [e for e in results if e.status == status]
        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get workflow statistics."""
        return {
            "total_workflows": len(self.workflows),
            "total_executions": len(self.executions),
            "active_executions": len(
                [e for e in self.executions.values() if e.status == WorkflowStatus.RUNNING]
            ),
            "completed_executions": len(
                [e for e in self.executions.values() if e.status == WorkflowStatus.COMPLETED]
            ),
        }
