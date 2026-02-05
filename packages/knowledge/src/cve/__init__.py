"""CVE database service."""

from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class CVE(BaseModel):
    """CVE (Common Vulnerabilities and Exposures) entry."""

    id: str  # e.g., "CVE-2024-0001"
    published_date: datetime
    modified_date: datetime

    # Basic info
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    cvss_score: float = 0.0

    # Technical details
    cvss_vector: Optional[str] = None
    cwe_id: Optional[str] = None
    cpe: list[str] = Field(default_factory=list)

    # Affected products
    affected_vendor: Optional[str] = None
    affected_product: Optional[str] = None
    affected_version: Optional[str] = None

    # References
    references: list[str] = Field(default_factory=list)

    # Exploitation
    exploit_available: bool = False
    exploit_in_wild: bool = False

    # Remediation
    solution: Optional[str] = None
    workaround: Optional[str] = None

    # Metadata
    source: str = "NVD"
    status: str = "published"  # published, deprecated, rejected


class CVEService:
    """Service for managing CVE database."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("cve-service")
        self.cves: dict[str, CVE] = {}

    async def add_cve(
        self,
        cve_id: str,
        description: str,
        published_date: datetime,
        severity: str = "MEDIUM",
    ) -> CVE:
        """Add a CVE to the database."""
        cve = CVE(
            id=cve_id,
            description=description,
            published_date=published_date,
            modified_date=datetime.now(timezone.utc),
            severity=severity,
        )
        self.cves[cve_id] = cve
        self.logger.info(f"Added CVE: {cve_id}")
        return cve

    def get_cve(self, cve_id: str) -> Optional[CVE]:
        """Get a CVE by ID."""
        return self.cves.get(cve_id)

    def search_cves(
        self,
        query: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 10,
    ) -> list[CVE]:
        """Search for CVEs."""
        results = list(self.cves.values())

        if severity:
            results = [c for c in results if c.severity.upper() == severity.upper()]

        if query:
            query_lower = query.lower()
            results = [
                c for c in results
                if query_lower in c.id.lower() or query_lower in c.description.lower()
            ]

        return results[:limit]

    def get_cves_by_cwe(self, cwe_id: str) -> list[CVE]:
        """Get all CVEs with a specific CWE."""
        return [c for c in self.cves.values() if c.cwe_id == cwe_id]

    def get_statistics(self) -> dict[str, Any]:
        """Get CVE database statistics."""
        return {
            "total_cves": len(self.cves),
            "by_severity": {
                s: len([c for c in self.cves.values() if c.severity.upper() == s])
                for s in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            },
            "exploits_available": len(
                [c for c in self.cves.values() if c.exploit_available]
            ),
        }
