"""Reconnaissance service for information gathering."""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from ai_red_blue_common import generate_uuid


class ReconType(str, Enum):
    """Types of reconnaissance."""

    PASSIVE = "passive"
    ACTIVE = "active"
    SOCIAL = "social"
    NETWORK = "network"
    INFRASTRUCTURE = "infrastructure"
    DNS = "dns"
    WHOIS = "whois"
    OSINT = "osint"


class ReconStatus(str, Enum):
    """Reconnaissance status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReconResult(BaseModel):
    """Result of reconnaissance."""

    id: str = Field(default_factory=generate_uuid)
    recon_type: ReconType
    target: str
    status: ReconStatus

    # Timing
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Findings
    ip_addresses: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    subdomains: list[str] = Field(default_factory=list)
    ports: dict[str, list[int]] = Field(default_factory=dict)
    services: list[dict] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    users: list[str] = Field(default_factory=list)
    social_profiles: list[dict] = Field(default_factory=dict)

    # Raw data
    raw_data: dict[str, Any] = Field(default_factory=dict)

    # Summary
    summary: dict[str, Any] = Field(default_factory=dict)

    def complete(self) -> None:
        """Mark reconnaissance as completed."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = ReconStatus.COMPLETED
        self._generate_summary()

    def _generate_summary(self) -> None:
        """Generate summary of findings."""
        self.summary = {
            "ip_count": len(self.ip_addresses),
            "domain_count": len(self.domains),
            "subdomain_count": len(self.subdomains),
            "open_port_count": sum(len(ports) for ports in self.ports.values()),
            "service_count": len(self.services),
            "technology_count": len(self.technologies),
            "email_count": len(self.emails),
        }


class ReconnaissanceService:
    """Service for managing reconnaissance operations."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("reconnaissance-service")
        self.active_recons: dict[str, ReconResult] = {}

    async def run_recon(
        self,
        recon_type: ReconType,
        target: str,
        options: Optional[dict[str, Any]] = None,
    ) -> ReconResult:
        """Run reconnaissance on target."""
        result = ReconResult(
            recon_type=recon_type,
            target=target,
            status=ReconStatus.RUNNING,
        )

        self.active_recons[result.id] = result
        self.logger.info(f"Running {recon_type.value} recon on {target}")

        # Execute recon (placeholder)
        result.ip_addresses = ["192.168.1.1"]
        result.domains = [target]
        result.complete()

        self.active_recons.pop(result.id, None)
        return result

    async def passive_recon(
        self,
        target: str,
    ) -> ReconResult:
        """Run passive reconnaissance."""
        return await self.run_recon(ReconType.PASSIVE, target)

    async def active_recon(
        self,
        target: str,
    ) -> ReconResult:
        """Run active reconnaissance."""
        return await self.run_recon(ReconType.ACTIVE, target)

    async def dns_recon(
        self,
        domain: str,
    ) -> ReconResult:
        """Run DNS reconnaissance."""
        return await self.run_recon(ReconType.DNS, domain)

    async def network_recon(
        self,
        target: str,
    ) -> ReconResult:
        """Run network reconnaissance."""
        return await self.run_recon(ReconType.NETWORK, target)

    def get_active_recons(self) -> list[ReconResult]:
        """Get all active reconnaissance tasks."""
        return list(self.active_recons.values())
