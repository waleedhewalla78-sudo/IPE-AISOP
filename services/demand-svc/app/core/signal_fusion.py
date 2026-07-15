"""Demand signal fusion — multi-source fused demand estimate."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class DemandSignal:
    source: str
    value: float
    confidence: float
    weight: float


@dataclass
class SeasonalFactor:
    factor: float
    description: str


@dataclass
class FusedDemand:
    product_id: str
    fused_qty: float
    confidence: float
    confidence_label: str
    signals: list[DemandSignal]
    seasonal_factor: float
    explanation: str


class DemandSignalFusion:
    async def fuse_signals(
        self,
        db: AsyncSession | None,
        tenant_id: str,
        product_id: str,
        horizon_days: int = 28,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        inputs = inputs or {}
        signals: list[DemandSignal] = []

        stat_qty = float(inputs.get("statistical_qty", 20))
        stat_conf = float(inputs.get("statistical_confidence", 0.75))
        signals.append(DemandSignal("statistical", stat_qty, stat_conf, 0.40))

        open_orders = float(inputs.get("open_orders_qty", 0))
        if open_orders > 0:
            signals.append(DemandSignal("confirmed_orders", open_orders, 0.95, 0.30))

        pipeline_qty = float(inputs.get("crm_pipeline_qty", 0))
        if pipeline_qty > 0:
            signals.append(DemandSignal("crm_pipeline", pipeline_qty, 0.50, 0.15))

        pattern_qty = float(inputs.get("customer_pattern_qty", 0))
        pattern_conf = float(inputs.get("customer_pattern_confidence", 0.6))
        if pattern_qty > 0:
            signals.append(DemandSignal("customer_pattern", pattern_qty, pattern_conf, 0.10))

        seasonal = SeasonalFactor(
            factor=float(inputs.get("seasonal_factor", 1.0)),
            description=str(inputs.get("seasonal_description", "no seasonal adjustment")),
        )

        weight_conf = sum(s.weight * s.confidence for s in signals) or 1.0
        fused_qty = sum(s.value * s.weight * s.confidence for s in signals) / weight_conf
        fused_qty *= seasonal.factor
        overall = self._calculate_confidence(signals)

        result = FusedDemand(
            product_id=product_id,
            fused_qty=round(fused_qty, 1),
            confidence=round(overall, 4),
            confidence_label=self._confidence_label(overall),
            signals=signals,
            seasonal_factor=seasonal.factor,
            explanation=self._generate_explanation(signals, seasonal),
        )

        if db is not None:
            await self._store(db, tenant_id, result, horizon_days)

        out = asdict(result)
        out["horizon_days"] = horizon_days
        out["signals"] = [asdict(s) for s in signals]
        return out

    def _calculate_confidence(self, signals: list[DemandSignal]) -> float:
        if not signals:
            return 0.0
        return sum(s.confidence * s.weight for s in signals) / sum(s.weight for s in signals)

    def _confidence_label(self, conf: float) -> str:
        if conf >= 0.80:
            return "high"
        if conf >= 0.55:
            return "medium"
        return "low"

    def _generate_explanation(self, signals: list[DemandSignal], seasonal: SeasonalFactor) -> str:
        parts = [
            f"{s.source}: {s.value:.0f} units (confidence {s.confidence:.0%})"
            for s in sorted(signals, key=lambda x: x.weight, reverse=True)
        ]
        return (
            f"Fused from {len(signals)} signals: {', '.join(parts)}. "
            f"Seasonal factor: {seasonal.factor:.2f} ({seasonal.description})."
        )

    async def _store(self, db: AsyncSession, tenant_id: str, result: FusedDemand, horizon_days: int) -> None:
        import json

        await db.execute(
            text("""
                INSERT INTO cdm_demand_fusion (
                    tenant_id, product_id, product_code, horizon_days,
                    fused_qty, confidence, confidence_label, seasonal_factor,
                    signals, explanation
                ) VALUES (
                    :tenant_id, :product_id, :product_code, :horizon_days,
                    :fused_qty, :confidence, :confidence_label, :seasonal_factor,
                    CAST(:signals AS jsonb), :explanation
                )
            """),
            {
                "tenant_id": UUID(tenant_id),
                "product_id": UUID(result.product_id) if _is_uuid(result.product_id) else None,
                "product_code": result.product_id if not _is_uuid(result.product_id) else None,
                "horizon_days": horizon_days,
                "fused_qty": result.fused_qty,
                "confidence": result.confidence,
                "confidence_label": result.confidence_label,
                "seasonal_factor": result.seasonal_factor,
                "signals": json.dumps([asdict(s) for s in result.signals]),
                "explanation": result.explanation,
            },
        )


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
