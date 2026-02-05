"""Security analyzers for code and behavior analysis."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class AnalysisType(str, Enum):
    """Types of security analysis."""

    STATIC = "static"
    DYNAMIC = "dynamic"
    NETWORK = "network"
    MALWARE = "malware"
    CODE = "code"
    CONFIG = "configuration"


class AnalysisStatus(str, Enum):
    """Analysis status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Finding(BaseModel):
    """Security finding from analysis."""

    id: str = Field(default_factory=generate_uuid)
    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    category: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    line_content: Optional[str] = None

    # Technical details
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    remediation: Optional[str] = None
    references: list[str] = Field(default_factory=list)

    # Evidence
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    # Metadata
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analyzer: str = "unknown"


class AnalysisResult(BaseModel):
    """Result of a security analysis."""

    id: str = Field(default_factory=generate_uuid)
    analysis_type: AnalysisType
    target: str
    status: AnalysisStatus
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Findings
    findings: list[Finding] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)

    # Statistics
    files_analyzed: int = 0
    lines_of_code: int = 0
    analysis_time_seconds: float = 0.0

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    def add_finding(self, finding: Finding) -> None:
        """Add a finding to the result."""
        self.findings.append(finding)
        severity = finding.severity.lower()
        self.summary[severity] = self.summary.get(severity, 0) + 1

    def complete(self) -> None:
        """Mark analysis as completed."""
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.analysis_time_seconds = (
            self.completed_at - self.started_at
        ).total_seconds()

    def fail(self, error: str) -> None:
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.errors.append(error)
        self.completed_at = datetime.now(timezone.utc)


class BaseAnalyzer(ABC):
    """Abstract base class for security analyzers."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version

    @property
    @abstractmethod
    def analysis_type(self) -> AnalysisType:
        """Type of analyzer."""
        pass

    @abstractmethod
    async def analyze(
        self,
        target: Any,
        options: Optional[dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Perform analysis on target."""
        pass


class StaticAnalyzer(BaseAnalyzer):
    """Static code analyzer for security issues."""

    def __init__(self):
        super().__init__("static-analyzer", "1.0.0")
        from ai_red_blue_common import get_logger

        self.logger = get_logger("static-analyzer")

    @property
    def analysis_type(self) -> AnalysisType:
        return AnalysisType.STATIC

    async def analyze(
        self,
        target: Any,
        options: Optional[dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Perform static analysis on code."""
        result = AnalysisResult(
            analysis_type=self.analysis_type,
            target=str(target),
            status=AnalysisStatus.RUNNING,
        )

        self.logger.info(f"Static analyzing {target}")

        # Implement static analysis logic
        result.add_finding(
            Finding(
                title="Hardcoded Password",
                description="Hardcoded password detected in source code",
                severity="high",
                category="Secrets",
                file_path="src/auth.py",
                line_number=42,
                cwe_id="CWE-259",
                remediation="Use environment variables or secure secret management",
            )
        )

        result.files_analyzed = 10
        result.lines_of_code = 1500
        result.complete()
        return result


class DynamicAnalyzer(BaseAnalyzer):
    """Dynamic behavior analyzer for running applications."""

    def __init__(self):
        super().__init__("dynamic-analyzer", "1.0.0")
        from ai_red_blue_common import get_logger

        self.logger = get_logger("dynamic-analyzer")

    @property
    def analysis_type(self) -> AnalysisType:
        return AnalysisType.DYNAMIC

    async def analyze(
        self,
        target: Any,
        options: Optional[dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Perform dynamic analysis on running application."""
        result = AnalysisResult(
            analysis_type=self.analysis_type,
            target=str(target),
            status=AnalysisStatus.RUNNING,
        )

        self.logger.info(f"Dynamic analyzing {target}")

        # Implement dynamic analysis logic
        result.add_finding(
            Finding(
                title="SQL Injection Vulnerability",
                description="User input is concatenated directly into SQL query",
                severity="critical",
                category="Injection",
                cwe_id="CWE-89",
                remediation="Use parameterized queries or ORM",
            )
        )

        result.complete()
        return result


class NetworkAnalyzer(BaseAnalyzer):
    """Network traffic analyzer."""

    def __init__(self):
        super().__init__("network-analyzer", "1.0.0")
        from ai_red_blue_common import get_logger

        self.logger = get_logger("network-analyzer")

    @property
    def analysis_type(self) -> AnalysisType:
        return AnalysisType.NETWORK

    async def analyze(
        self,
        target: Any,
        options: Optional[dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Perform network analysis."""
        result = AnalysisResult(
            analysis_type=self.analysis_type,
            target=str(target),
            status=AnalysisStatus.RUNNING,
        )

        self.logger.info(f"Analyzing network traffic from {target}")

        result.complete()
        return result


class MalwareAnalyzer(BaseAnalyzer):
    """Malware analyzer for suspicious files."""

    def __init__(self):
        super().__init__("malware-analyzer", "1.0.0")
        from ai_red_blue_common import get_logger

        self.logger = get_logger("malware-analyzer")

    @property
    def analysis_type(self) -> AnalysisType:
        return AnalysisType.MALWARE

    async def analyze(
        self,
        target: Any,
        options: Optional[dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Analyze file for malware indicators."""
        result = AnalysisResult(
            analysis_type=self.analysis_type,
            target=str(target),
            status=AnalysisStatus.RUNNING,
        )

        self.logger.info(f"Analyzing file {target} for malware")

        result.complete()
        return result
