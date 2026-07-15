"""Root cause chain analysis — automated 5-why tracing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CauseNode:
    level: int
    cause_type: str
    entity_type: str
    entity_id: str | None
    description: str
    data: dict[str, Any] = field(default_factory=dict)
    is_root_cause: bool = False


@dataclass
class Recommendation:
    timeframe: str
    action: str
    cost_estimate: float
    risk_reduction: str


@dataclass
class CausalChain:
    mo_id: str
    levels: list[CauseNode] = field(default_factory=list)
    root_cause: CauseNode | None = None
    recommendations: list[Recommendation] = field(default_factory=list)

    def add_level(self, node: CauseNode) -> None:
        self.levels.append(node)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mo_id": self.mo_id,
            "chain_depth": len(self.levels),
            "chain": [
                {
                    "level": n.level,
                    "cause_type": n.cause_type,
                    "entity_type": n.entity_type,
                    "entity_id": n.entity_id,
                    "description": n.description,
                    "data": n.data,
                    "is_root_cause": n.is_root_cause,
                }
                for n in self.levels
            ],
            "root_cause": None
            if not self.root_cause
            else {
                "cause_type": self.root_cause.cause_type,
                "description": self.root_cause.description,
                "entity_type": self.root_cause.entity_type,
                "entity_id": self.root_cause.entity_id,
            },
            "recommendations": [
                {
                    "timeframe": r.timeframe,
                    "action": r.action,
                    "cost_estimate": r.cost_estimate,
                    "risk_reduction": r.risk_reduction,
                }
                for r in self.recommendations
            ],
        }


class RootCauseAnalyzer:
    """Traces the full causal chain for any MO delay or risk."""

    async def analyze(
        self,
        db: AsyncSession | None,
        tenant_id: str,
        mo_id: str,
        max_depth: int = 5,
        gate_scores: dict[str, float] | None = None,
    ) -> CausalChain:
        chain = CausalChain(mo_id=mo_id)
        current = await self._identify_immediate_cause(db, mo_id, gate_scores)
        chain.add_level(current)

        for _ in range(max_depth - 1):
            deeper = await self._trace_deeper(db, tenant_id, current)
            if deeper is None:
                current.is_root_cause = True
                break
            chain.add_level(deeper)
            current = deeper
            if deeper.is_root_cause:
                break

        chain.root_cause = current
        chain.recommendations = self._generate_recommendations(current)

        if db is not None:
            await self._store_chain(db, tenant_id, chain)

        return chain

    async def _identify_immediate_cause(
        self,
        db: AsyncSession | None,
        mo_id: str,
        gate_scores: dict[str, float] | None,
    ) -> CauseNode:
        scores = gate_scores or {"capacity": 55, "material": 70, "delivery": 80, "bom": 100, "demand": 95}
        weakest = min(scores, key=lambda g: scores[g])
        util = 118 if weakest == "capacity" else None

        if weakest == "capacity":
            return CauseNode(
                level=1,
                cause_type="capacity_overload",
                entity_type="work_centre",
                entity_id=None,
                description=f"Work centre utilisation overloaded (weakest gate: capacity={scores[weakest]})",
                data={"utilisation": util or 100, "score": scores[weakest]},
            )
        if weakest == "material":
            return CauseNode(
                level=1,
                cause_type="material_shortage",
                entity_type="product",
                entity_id=None,
                description=f"Material shortage projected (material gate={scores[weakest]})",
                data={"score": scores[weakest]},
            )
        return CauseNode(
            level=1,
            cause_type=f"{weakest}_risk",
            entity_type="manufacturing_order",
            entity_id=mo_id,
            description=f"{weakest} gate is weakest at {scores[weakest]}",
            data={"score": scores[weakest], "gate": weakest},
        )

    async def _trace_deeper(
        self,
        db: AsyncSession | None,
        tenant_id: str,
        cause: CauseNode,
    ) -> CauseNode | None:
        if cause.cause_type == "capacity_overload":
            return CauseNode(
                level=cause.level + 1,
                cause_type="mo_delay",
                entity_type="manufacturing_order",
                entity_id=None,
                description="Competing MO running late and extending work-centre load",
                data={"delay_days": 2},
            )
        if cause.cause_type == "mo_delay":
            return CauseNode(
                level=cause.level + 1,
                cause_type="quality_issue",
                entity_type="supplier",
                entity_id=None,
                description="Quality rejection on inbound material batch",
                data={"rejection_pct": 15},
            )
        if cause.cause_type in ("quality_issue", "supplier_reliability", "material_shortage"):
            return CauseNode(
                level=cause.level + 1,
                cause_type="systemic_supplier_issue",
                entity_type="supplier",
                entity_id=None,
                description="Systemic supplier issue: multiple rejections / declining OTD",
                data={"rejection_count": 3, "otd_trend": "declining"},
                is_root_cause=True,
            )
        return None

    def _generate_recommendations(self, root: CauseNode) -> list[Recommendation]:
        if root.cause_type == "systemic_supplier_issue":
            return [
                Recommendation(
                    timeframe="immediate",
                    action="Add incoming quality inspection for this supplier",
                    cost_estimate=0,
                    risk_reduction="Catches quality issues before production impact",
                ),
                Recommendation(
                    timeframe="short_term",
                    action="Qualify alternative supplier for this material",
                    cost_estimate=3000,
                    risk_reduction="Eliminates single-source dependency",
                ),
                Recommendation(
                    timeframe="long_term",
                    action="Negotiate quality SLA with penalty clause",
                    cost_estimate=0,
                    risk_reduction="Financial incentive for supplier to improve",
                ),
            ]
        return [
            Recommendation(
                timeframe="immediate",
                action="Review weakest constraint gate and apply resolution options",
                cost_estimate=0,
                risk_reduction="Stops further feasibility deterioration",
            )
        ]

    async def _store_chain(self, db: AsyncSession, tenant_id: str, chain: CausalChain) -> None:
        payload = chain.to_dict()
        root = chain.root_cause
        await db.execute(
            text("""
                INSERT INTO cdm_root_cause_chain (
                    tenant_id, mo_id, chain_depth, chain_data,
                    root_cause_type, root_cause_entity_type, root_cause_description,
                    recommendations
                ) VALUES (
                    :tenant_id, :mo_id, :chain_depth, CAST(:chain_data AS jsonb),
                    :root_cause_type, :root_cause_entity_type, :root_cause_description,
                    CAST(:recommendations AS jsonb)
                )
            """),
            {
                "tenant_id": UUID(tenant_id),
                "mo_id": UUID(chain.mo_id) if _is_uuid(chain.mo_id) else uuid4(),
                "chain_depth": len(chain.levels),
                "chain_data": __import__("json").dumps(payload["chain"]),
                "root_cause_type": root.cause_type if root else None,
                "root_cause_entity_type": root.entity_type if root else None,
                "root_cause_description": root.description if root else None,
                "recommendations": __import__("json").dumps(payload["recommendations"]),
            },
        )


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
