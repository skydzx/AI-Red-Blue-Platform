"""Attack analysis models for AI Red Blue Platform."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class AttackPhase(str, Enum):
    """MITRE ATT&CK phases."""

    RECON = "recon"
    WEAPONIZE = "weaponize"
    DELIVER = "deliver"
    EXPLOIT = "exploit"
    INSTALL = "install"
    COMMAND_CONTROL = "command_control"
    ACTIONS = "actions"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class AttackTechnique(BaseModel):
    """MITRE ATT&CK technique."""

    id: str  # e.g., "T1059"
    name: str
    tactic: AttackPhase
    description: str = ""
    url: Optional[str] = None
    detection: Optional[str] = None
    data_sources: list[str] = Field(default_factory=list)


class AttackTactic(BaseModel):
    """Attack tactic information."""

    phase: AttackPhase
    techniques: list[AttackTechnique] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AttackPattern(BaseModel):
    """Attack pattern model based on MITRE ATT&CK."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    description: str
    techniques: list[AttackTechnique] = Field(default_factory=list)
    tactics: list[AttackPhase] = Field(default_factory=list)
    severity: str = "medium"
    likelihood: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: float = Field(default=0.5, ge=0.0, le=1.0)
    mitigations: list[str] = Field(default_factory=list)
    detection_rules: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def calculate_risk(self) -> float:
        """Calculate risk score based on likelihood and impact."""
        return self.likelihood * self.impact * 100


class AttackStep(BaseModel):
    """A single step in an attack chain."""

    id: str = Field(default_factory=generate_uuid)
    phase: AttackPhase
    technique: Optional[AttackTechnique] = None
    description: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: Optional[str] = None
    target: Optional[str] = None
    tools: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    evidence: list[str] = Field(default_factory=list)
    detection: bool = False
    detection_info: Optional[dict] = None


class AttackChain(BaseModel):
    """Attack chain / kill chain model."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    description: str = ""
    steps: list[AttackStep] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    actors: list[str] = Field(default_factory=list)
    targets: list[str] = Field(default_factory=list)
    status: str = "active"  # active, completed, detected, stopped
    severity: str = "medium"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    coverage: dict[str, float] = Field(default_factory=dict)  # technique_id -> coverage

    def add_step(self, step: AttackStep) -> None:
        """Add a step to the attack chain."""
        self.steps.append(step)

    def get_steps_by_phase(self, phase: AttackPhase) -> list[AttackStep]:
        """Get all steps in a specific phase."""
        return [s for s in self.steps if s.phase == phase]

    def calculate_progress(self) -> dict[str, Any]:
        """Calculate attack chain progress."""
        total = len(self.steps)
        if total == 0:
            return {"completed": 0, "total": 0, "percentage": 0.0}

        completed = sum(1 for s in self.steps if s.success)
        detected = sum(1 for s in self.steps if s.detection)

        return {
            "completed": completed,
            "total": total,
            "percentage": (completed / total) * 100 if total > 0 else 0.0,
            "detected": detected,
            "undetected": completed - detected,
        }

    def identify_gaps(self) -> list[AttackPhase]:
        """Identify missing phases in the attack chain."""
        covered = set(s.phase for s in self.steps)
        all_phases = set(AttackPhase)

        # Key phases for a complete attack
        key_phases = [
            AttackPhase.RECON,
            AttackPhase.WEAPONIZE,
            AttackPhase.DELIVER,
            AttackPhase.EXPLOIT,
            AttackPhase.INSTALL,
            AttackPhase.COMMAND_CONTROL,
            AttackPhase.ACTIONS,
        ]

        return [p for p in key_phases if p not in covered]

    def get_attack_matrix(self) -> dict[AttackPhase, list[AttackTechnique]]:
        """Generate MITRE ATT&CK matrix view."""
        matrix: dict[AttackPhase, list[AttackTechnique]] = {}

        for step in self.steps:
            if step.technique:
                if step.phase not in matrix:
                    matrix[step.phase] = []
                if step.technique not in matrix[step.phase]:
                    matrix[step.phase].append(step.technique)

        return matrix


class AttackAnalyzer:
    """Analyzer for attack patterns and chains."""

    def __init__(self):
        self.patterns: dict[str, AttackPattern] = {}
        self.chains: dict[str, AttackChain] = {}

    def register_pattern(self, pattern: AttackPattern) -> None:
        """Register an attack pattern."""
        self.patterns[pattern.id] = pattern

    def analyze_chain(self, chain: AttackChain) -> dict[str, Any]:
        """Analyze an attack chain and return insights."""
        progress = chain.calculate_progress()
        gaps = chain.identify_gaps()
        matrix = chain.get_attack_matrix()

        # Calculate overall risk
        risk_factors = []
        if chain.severity == "critical":
            risk_factors.append(100)
        elif chain.severity == "high":
            risk_factors.append(75)
        elif chain.severity == "medium":
            risk_factors.append(50)
        else:
            risk_factors.append(25)

        risk_factors.append(chain.confidence * 50)
        risk_factors.append(progress["percentage"] * 0.3)

        overall_risk = sum(risk_factors) / len(risk_factors)

        return {
            "chain_id": chain.id,
            "progress": progress,
            "gaps": [p.value for p in gaps],
            "attack_matrix": {
                k.value: [t.id for t in v] for k, v in matrix.items()
            },
            "overall_risk": overall_risk,
            "recommendations": self._generate_recommendations(gaps, matrix),
        }

    def _generate_recommendations(
        self,
        gaps: list[AttackPhase],
        matrix: dict[AttackPhase, list[AttackTechnique]],
    ) -> list[str]:
        """Generate security recommendations based on gaps."""
        recommendations = []

        if AttackPhase.RECON in gaps:
            recommendations.append(
                "Enhance network monitoring to detect reconnaissance activity"
            )
        if AttackPhase.COMMAND_CONTROL in gaps:
            recommendations.append(
                "Monitor for unusual external communications"
            )
        if AttackPhase.PERSISTENCE in gaps:
            recommendations.append(
                "Review system startup locations and scheduled tasks"
            )
        if AttackPhase.PRIVILEGE_ESCALATION in gaps:
            recommendations.append(
                "Audit user permission changes and privilege assignments"
            )
        if AttackPhase.EXFILTRATION in gaps:
            recommendations.append(
                "Monitor data transfer patterns and sensitive data access"
            )

        return recommendations

    def match_pattern(
        self,
        chain: AttackChain,
        min_confidence: float = 0.7,
    ) -> list[AttackPattern]:
        """Match an attack chain against known patterns."""
        matched = []

        chain_techniques = set()
        for step in chain.steps:
            if step.technique:
                chain_techniques.add(step.technique.id)

        for pattern in self.patterns.values():
            pattern_techniques = set(t.id for t in pattern.techniques)

            # Calculate Jaccard similarity
            if chain_techniques:
                intersection = chain_techniques & pattern_techniques
                union = chain_techniques | pattern_techniques
                similarity = len(intersection) / len(union) if union else 0

                if similarity >= min_confidence:
                    matched.append(pattern)

        return matched
