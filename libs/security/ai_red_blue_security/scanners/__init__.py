"""Security scanners for vulnerability assessment."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, AsyncIterator
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class ScanStatus(str, Enum):
    """Scan status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Vulnerability(BaseModel):
    """Vulnerability finding."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    description: str
    severity: VulnerabilitySeverity
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None

    # Location
    target: str
    location: Optional[str] = None
    parameter: Optional[str] = None

    # Technical details
    proof: Optional[str] = None
    remediation: Optional[str] = None
    references: list[str] = Field(default_factory=list)

    # Discovery
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scanner: str = "unknown"


class ScanResult(BaseModel):
    """Base scan result."""

    id: str = Field(default_factory=generate_uuid)
    scan_type: str
    target: str
    status: ScanStatus
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Findings
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)

    # Statistics
    total_scanned: int = 0
    issues_found: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def add_vulnerability(self, vuln: Vulnerability) -> None:
        """Add a vulnerability to the result."""
        self.vulnerabilities.append(vuln)
        self.issues_found += 1

        if vuln.severity == VulnerabilitySeverity.CRITICAL:
            self.critical_count += 1
        elif vuln.severity == VulnerabilitySeverity.HIGH:
            self.high_count += 1
        elif vuln.severity == VulnerabilitySeverity.MEDIUM:
            self.medium_count += 1
        elif vuln.severity == VulnerabilitySeverity.LOW:
            self.low_count += 1

    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning to the result."""
        self.warnings.append(warning)

    def complete(self) -> None:
        """Mark scan as completed."""
        self.status = ScanStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        """Mark scan as failed."""
        self.status = ScanStatus.FAILED
        self.add_error(error)
        self.completed_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Cancel the scan."""
        self.status = ScanStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)

    def get_summary(self) -> dict[str, Any]:
        """Get scan summary."""
        return {
            "scan_id": self.id,
            "scan_type": self.scan_type,
            "target": self.target,
            "status": self.status.value,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at else None
            ),
            "summary": {
                "total": self.issues_found,
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
        }


class BaseScanner(ABC):
    """Abstract base class for security scanners."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = None  # Will be set by subclass

    @property
    @abstractmethod
    def scan_type(self) -> str:
        """Type of scanner."""
        pass

    @abstractmethod
    async def scan(
        self,
        target: str,
        options: Optional[dict[str, Any]] = None,
    ) -> ScanResult:
        """Perform a scan on the target."""
        pass

    async def scan_stream(
        self,
        target: str,
        options: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream scan progress updates."""
        result = await self.scan(target, options)
        yield {"type": "result", "data": result.get_summary()}

    def _create_result(self, target: str) -> ScanResult:
        """Create a new scan result."""
        return ScanResult(
            scan_type=self.scan_type,
            target=target,
            status=ScanStatus.RUNNING,
        )


class VulnerabilityScanner(BaseScanner):
    """General vulnerability scanner."""

    def __init__(self):
        super().__init__("vulnerability-scanner", "1.0.0")
        from ai_red_blue_common import get_logger

        self.logger = get_logger("vuln-scanner")

    @property
    def scan_type(self) -> str:
        return "vulnerability"

    async def scan(
        self,
        target: str,
        options: Optional[dict[str, Any]] = None,
    ) -> ScanResult:
        """Perform vulnerability scan."""
        result = self._create_result(target)

        # Implement actual scanning logic here
        self.logger.info(f"Scanning {target} for vulnerabilities")

        # Simulate scan
        result.add_vulnerability(
            Vulnerability(
                name="Test Vulnerability",
                description="A test vulnerability found during scan",
                severity=VulnerabilitySeverity.MEDIUM,
                target=target,
                cve_id="CVE-2024-0001",
            )
        )

        result.complete()
        return result


class PortScanner(BaseScanner):
    """Port scanner."""

    def __init__(self):
        super().__init__("port-scanner", "1.0.0")
        from ai_red_blue_common import get_logger

        self.logger = get_logger("port-scanner")

    @property
    def scan_type(self) -> str:
        return "port"

    async def scan(
        self,
        target: str,
        options: Optional[dict[str, Any]] = None,
    ) -> ScanResult:
        """Perform port scan."""
        result = self._create_result(target)

        ports = options.get("ports", [22, 80, 443, 8080]) if options else [22, 80, 443, 8080]
        timeout = options.get("timeout", 1) if options else 1

        self.logger.info(f"Scanning ports {ports} on {target}")

        # Simulate port scan
        open_ports = []
        for port in ports:
            if port in [22, 80, 443]:
                open_ports.append(port)
                result.add_vulnerability(
                    Vulnerability(
                        name=f"Port {port} Open",
                        description=f"Port {port} is open and accessible",
                        severity=VulnerabilitySeverity.INFO,
                        target=target,
                        location=f"tcp:{port}",
                    )
                )

        result.metadata["open_ports"] = open_ports
        result.complete()
        return result


class WebScanner(BaseScanner):
    """Web application scanner."""

    def __init__(self):
        super().__init__("web-scanner", "1.0.0")
        from ai_red_blue_common import get_logger

        self.logger = get_logger("web-scanner")

    @property
    def scan_type(self) -> str:
        return "web"

    async def scan(
        self,
        target: str,
        options: Optional[dict[str, Any]] = None,
    ) -> ScanResult:
        """Perform web application scan."""
        result = self._create_result(target)

        self.logger.info(f"Scanning web application at {target}")

        # Simulate web scan
        result.add_vulnerability(
            Vulnerability(
                name="Missing Security Headers",
                description="Several security headers are missing",
                severity=VulnerabilitySeverity.LOW,
                target=target,
                remediation="Add X-Content-Type-Options, X-Frame-Options headers",
            )
        )

        result.complete()
        return result
