from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
import logging
from uuid import uuid4

from sqlalchemy import Column, String, Text, Float, DateTime, Index, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin

logger = logging.getLogger("ipe.compliance")


class TrustPrinciple(StrEnum):
    SECURITY = "security"
    AVAILABILITY = "availability"
    PROCESSING_INTEGRITY = "processing_integrity"
    CONFIDENTIALITY = "confidentiality"
    PRIVACY = "privacy"


class ControlStatus(StrEnum):
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"


class EvidenceType(StrEnum):
    POLICY = "policy"
    IMPLEMENTATION = "implementation"
    MONITORING = "monitoring"
    TESTING = "testing"


@dataclass
class ComplianceControl:
    control_id: str
    principle: TrustPrinciple
    name: str
    description: str
    status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    evidence: list[dict[str, Any]] = field(default_factory=list)
    last_assessed: datetime | None = None
    owner: str = ""

    def add_evidence(self, evidence_type: EvidenceType, description: str, artifact_url: str = "") -> None:
        self.evidence.append({
            "type": evidence_type.value,
            "description": description,
            "artifact_url": artifact_url,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        logger.info("Added %s evidence for control %s: %s", evidence_type.value, self.control_id, description)


class Soc2ControlDB(TenantScopedMixin, Base):
    __tablename__ = "soc2_control"
    __table_args__ = (
        Index("ix_soc2_control_tenant_principle", "tenant_id", "trust_principle"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    control_id = Column(String(20), nullable=False, index=True)
    trust_principle = Column(String(30), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, server_default="not_implemented")
    evidence = Column(JSONB, nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Soc2AssessmentDB(TenantScopedMixin, Base):
    __tablename__ = "soc2_assessment"
    __table_args__ = (
        Index("ix_soc2_assessment_tenant_principle", "tenant_id", "principle"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    principle = Column(String(30), nullable=False, index=True)
    score = Column(Float, nullable=False, server_default="0.0")
    assessed_by = Column(String(200), nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class SOC2Controls:
    CONTROLS: dict[str, ComplianceControl] = {}

    def __init__(self) -> None:
        self._initialize_controls()

    def _initialize_controls(self) -> None:
        controls = [
            ComplianceControl(
                control_id="CC1.1",
                principle=TrustPrinciple.SECURITY,
                name="Control Environment",
                description="The entity demonstrates commitment to integrity and ethical values.",
                status=ControlStatus.IMPLEMENTED,
                owner="compliance",
            ),
            ComplianceControl(
                control_id="CC1.2",
                principle=TrustPrinciple.SECURITY,
                name="Board Independence",
                description="The board of directors demonstrates independence from management.",
                status=ControlStatus.NOT_APPLICABLE,
                owner="board",
            ),
            ComplianceControl(
                control_id="CC2.1",
                principle=TrustPrinciple.SECURITY,
                name="Internal Communication",
                description="The entity internally communicates information about objectives and responsibilities.",
                status=ControlStatus.IMPLEMENTED,
                owner="compliance",
            ),
            ComplianceControl(
                control_id="CC3.1",
                principle=TrustPrinciple.SECURITY,
                name="Risk Assessment",
                description="The entity identifies and assesses risks that may affect objectives.",
                status=ControlStatus.IMPLEMENTED,
                owner="security",
            ),
            ComplianceControl(
                control_id="CC4.1",
                principle=TrustPrinciple.SECURITY,
                name="Monitoring Activities",
                description="The entity monitors controls and evaluates their effectiveness.",
                status=ControlStatus.PARTIAL,
                owner="security",
            ),
            ComplianceControl(
                control_id="CC5.1",
                principle=TrustPrinciple.SECURITY,
                name="Logical Access",
                description="The entity restricts logical access to software and data to authorized users.",
                status=ControlStatus.IMPLEMENTED,
                owner="security",
            ),
            ComplianceControl(
                control_id="CC5.2",
                principle=TrustPrinciple.SECURITY,
                name="User Authentication",
                description="The entity authenticates users before granting access.",
                status=ControlStatus.IMPLEMENTED,
                owner="security",
            ),
            ComplianceControl(
                control_id="CC5.3",
                principle=TrustPrinciple.SECURITY,
                name="Encryption",
                description="The entity encrypts data at rest and in transit.",
                status=ControlStatus.PARTIAL,
                owner="security",
            ),
            ComplianceControl(
                control_id="CC6.1",
                principle=TrustPrinciple.SECURITY,
                name="Network Security",
                description="The entity implements network security controls.",
                status=ControlStatus.PARTIAL,
                owner="infrastructure",
            ),
            ComplianceControl(
                control_id="CC6.2",
                principle=TrustPrinciple.SECURITY,
                name="Endpoint Security",
                description="The entity implements endpoint security controls.",
                status=ControlStatus.NOT_IMPLEMENTED,
                owner="infrastructure",
            ),
            ComplianceControl(
                control_id="CC7.1",
                principle=TrustPrinciple.SECURITY,
                name="Vulnerability Management",
                description="The entity identifies and remediates vulnerabilities.",
                status=ControlStatus.PARTIAL,
                owner="security",
            ),
            ComplianceControl(
                control_id="CC7.2",
                principle=TrustPrinciple.SECURITY,
                name="Incident Response",
                description="The entity responds to security incidents.",
                status=ControlStatus.PARTIAL,
                owner="security",
            ),
            ComplianceControl(
                control_id="A1.1",
                principle=TrustPrinciple.AVAILABILITY,
                name="System Availability",
                description="The entity maintains system availability objectives.",
                status=ControlStatus.IMPLEMENTED,
                owner="infrastructure",
            ),
            ComplianceControl(
                control_id="A1.2",
                principle=TrustPrinciple.AVAILABILITY,
                name="Backup and Recovery",
                description="The entity implements backup and recovery procedures.",
                status=ControlStatus.PARTIAL,
                owner="infrastructure",
            ),
            ComplianceControl(
                control_id="A1.3",
                principle=TrustPrinciple.AVAILABILITY,
                name="Disaster Recovery",
                description="The entity implements disaster recovery procedures.",
                status=ControlStatus.NOT_IMPLEMENTED,
                owner="infrastructure",
            ),
            ComplianceControl(
                control_id="PI1.1",
                principle=TrustPrinciple.PROCESSING_INTEGRITY,
                name="Data Processing Accuracy",
                description="The entity processes data accurately and completely.",
                status=ControlStatus.IMPLEMENTED,
                owner="engineering",
            ),
            ComplianceControl(
                control_id="PI1.2",
                principle=TrustPrinciple.PROCESSING_INTEGRITY,
                name="Data Validation",
                description="The entity validates input and output data.",
                status=ControlStatus.IMPLEMENTED,
                owner="engineering",
            ),
            ComplianceControl(
                control_id="C1.1",
                principle=TrustPrinciple.CONFIDENTIALITY,
                name="Data Classification",
                description="The entity classifies data based on sensitivity.",
                status=ControlStatus.PARTIAL,
                owner="compliance",
            ),
            ComplianceControl(
                control_id="C1.2",
                principle=TrustPrinciple.CONFIDENTIALITY,
                name="Data Retention",
                description="The entity implements data retention policies.",
                status=ControlStatus.NOT_IMPLEMENTED,
                owner="compliance",
            ),
            ComplianceControl(
                control_id="P1.1",
                principle=TrustPrinciple.PRIVACY,
                name="Privacy Policy",
                description="The entity maintains a privacy policy.",
                status=ControlStatus.PARTIAL,
                owner="compliance",
            ),
            ComplianceControl(
                control_id="P1.2",
                principle=TrustPrinciple.PRIVACY,
                name="Data Subject Rights",
                description="The entity respects data subject rights.",
                status=ControlStatus.NOT_IMPLEMENTED,
                owner="compliance",
            ),
            ComplianceControl(
                control_id="P1.3",
                principle=TrustPrinciple.PRIVACY,
                name="Consent Management",
                description="The entity manages consent for data processing.",
                status=ControlStatus.NOT_IMPLEMENTED,
                owner="compliance",
            ),
        ]
        self.CONTROLS = {c.control_id: c for c in controls}

    def get_control(self, control_id: str) -> ComplianceControl | None:
        return self.CONTROLS.get(control_id)

    def get_controls_by_principle(self, principle: TrustPrinciple) -> list[ComplianceControl]:
        return [c for c in self.CONTROLS.values() if c.principle == principle]

    def get_evidence_coverage(self) -> dict[str, float]:
        result = {}
        for principle in TrustPrinciple:
            controls = self.get_controls_by_principle(principle)
            if not controls:
                result[principle.value] = 0.0
                continue
            implemented = sum(1 for c in controls if c.status in (ControlStatus.IMPLEMENTED, ControlStatus.PARTIAL))
            result[principle.value] = implemented / len(controls) * 100
        return result

    def get_summary(self) -> dict[str, Any]:
        total = len(self.CONTROLS)
        implemented = sum(1 for c in self.CONTROLS.values() if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.CONTROLS.values() if c.status == ControlStatus.PARTIAL)
        not_implemented = sum(1 for c in self.CONTROLS.values() if c.status == ControlStatus.NOT_IMPLEMENTED)
        return {
            "total_controls": total,
            "implemented": implemented,
            "partial": partial,
            "not_implemented": not_implemented,
            "readiness_pct": (implemented + partial * 0.5) / total * 100,
            "coverage_by_principle": self.get_evidence_coverage(),
        }


async def get_soc2_summary() -> dict[str, Any]:
    fallback = SOC2Controls()
    try:
        from ipe_shared.database.session import get_session
        from sqlalchemy import select, func as sa_func

        async for session in get_session():
            status_counts = (
                await session.execute(
                    select(Soc2ControlDB.status, sa_func.count())
                    .group_by(Soc2ControlDB.status)
                )
            ).all()
            principle_rows = (
                await session.execute(
                    select(Soc2ControlDB.trust_principle, Soc2ControlDB.status, sa_func.count())
                    .group_by(Soc2ControlDB.trust_principle, Soc2ControlDB.status)
                )
            ).all()
            total = sum(c for _, c in status_counts)
            implemented = dict(status_counts).get(ControlStatus.IMPLEMENTED.value, 0)
            partial = dict(status_counts).get(ControlStatus.PARTIAL.value, 0)
            not_implemented = dict(status_counts).get(ControlStatus.NOT_IMPLEMENTED.value, 0)
            coverage: dict[str, float] = {}
            principle_totals: dict[str, int] = {}
            principle_impl: dict[str, int] = {}
            for principle, status, cnt in principle_rows:
                principle_totals[principle] = principle_totals.get(principle, 0) + cnt
                if status in (ControlStatus.IMPLEMENTED.value, ControlStatus.PARTIAL.value):
                    principle_impl[principle] = principle_impl.get(principle, 0) + cnt
            for p in TrustPrinciple:
                t = principle_totals.get(p.value, 0)
                coverage[p.value] = (principle_impl.get(p.value, 0) / t * 100) if t > 0 else 0.0
            if total == 0:
                return fallback.get_summary()
            return {
                "total_controls": total,
                "implemented": implemented,
                "partial": partial,
                "not_implemented": not_implemented,
                "readiness_pct": (implemented + partial * 0.5) / total * 100,
                "coverage_by_principle": coverage,
            }
    except Exception:
        logger.warning("SOC 2 DB query failed, using in-memory fallback")
        return fallback.get_summary()


async def update_control_status(control_id: str, status: str, evidence: list[dict[str, Any]] | None = None) -> Soc2ControlDB | None:
    from ipe_shared.database.session import get_session
    from sqlalchemy import select

    async for session in get_session():
        result = await session.execute(
            select(Soc2ControlDB).where(Soc2ControlDB.control_id == control_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = status
        row.assessed_at = datetime.now(UTC)
        if evidence is not None:
            row.evidence = evidence
        await session.flush()
        await session.commit()
        await session.refresh(row)
        return row
    return None


async def create_assessment(principle: str, score: float, assessed_by: str = "", notes: str = "") -> Soc2AssessmentDB:
    from ipe_shared.database.session import get_session

    async for session in get_session():
        assessment = Soc2AssessmentDB(
            principle=principle,
            score=score,
            assessed_by=assessed_by or "system",
            assessed_at=datetime.now(UTC),
            notes=notes,
        )
        session.add(assessment)
        await session.flush()
        await session.commit()
        await session.refresh(assessment)
        return assessment
    raise RuntimeError("No database session available")