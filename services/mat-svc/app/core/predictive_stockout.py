"""Predictive stockout warning + supplier reliability scoring (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class StockoutPrediction:
    product_code: str
    on_hand: float
    avg_daily_consumption: float
    days_of_stock: float
    avg_lead_time_days: float
    lead_time_variability_days: float
    stockout_window_days: tuple[float, float]
    recommended_actions: list[dict[str, Any]]
    financial_impact_do_nothing: float


class PredictiveStockout:
    def predict(
        self,
        product_code: str,
        on_hand: float,
        avg_daily_consumption: float,
        avg_lead_time_days: float,
        lead_time_variability_days: float = 2.0,
        expedite_cost: float = 800.0,
        stockout_penalty: float = 12400.0,
    ) -> dict[str, Any]:
        daily = max(avg_daily_consumption, 0.01)
        days_of_stock = on_hand / daily
        low = max(0.0, days_of_stock - lead_time_variability_days)
        high = max(low, days_of_stock + lead_time_variability_days / 2)
        at_risk = days_of_stock < avg_lead_time_days

        actions = []
        if at_risk:
            actions = [
                {
                    "action": "expedite_po",
                    "cost_estimate": expedite_cost,
                    "description": "Expedite open PO to arrive before stockout",
                },
                {
                    "action": "reduce_mo_qty",
                    "cost_estimate": 0,
                    "description": "Reduce near-term MO quantity to stretch available stock",
                },
                {
                    "action": "do_nothing",
                    "cost_estimate": stockout_penalty,
                    "description": "Accept stockout risk",
                },
            ]

        pred = StockoutPrediction(
            product_code=product_code,
            on_hand=on_hand,
            avg_daily_consumption=avg_daily_consumption,
            days_of_stock=round(days_of_stock, 1),
            avg_lead_time_days=avg_lead_time_days,
            lead_time_variability_days=lead_time_variability_days,
            stockout_window_days=(round(low, 1), round(high, 1)),
            recommended_actions=actions,
            financial_impact_do_nothing=stockout_penalty if at_risk else 0,
        )
        out = asdict(pred)
        out["at_risk"] = at_risk
        out["stockout_window_days"] = list(pred.stockout_window_days)
        return out


class SupplierReliabilityScorer:
    """Composite supplier score: OTD, quality, lead-time trend, concentration."""

    def score(
        self,
        supplier_name: str,
        on_time_pct: float,
        quality_rejection_pct: float,
        lead_time_trend: str,
        concentration_pct: float,
        sample_size: int = 0,
    ) -> dict[str, Any]:
        otd_component = min(max(on_time_pct, 0), 100)
        quality_component = max(0.0, 100 - quality_rejection_pct * 10)
        trend_component = {"improving": 90, "stable": 75, "worsening": 40, "declining": 40}.get(
            lead_time_trend.lower(), 60
        )
        concentration_component = max(0.0, 100 - max(0, concentration_pct - 40))

        overall = (
            0.40 * otd_component
            + 0.25 * quality_component
            + 0.20 * trend_component
            + 0.15 * concentration_component
        )

        recommendation = None
        if overall < 60 or concentration_pct >= 90:
            recommendation = "Qualify a second supplier before next quarter"
        elif overall < 75:
            recommendation = "Increase incoming inspection and renegotiate lead times"

        return {
            "supplier_name": supplier_name,
            "on_time_pct": on_time_pct,
            "quality_rejection_pct": quality_rejection_pct,
            "lead_time_trend": lead_time_trend,
            "concentration_pct": concentration_pct,
            "sample_size": sample_size,
            "overall_score": round(overall, 1),
            "risk_tier": "high" if overall < 60 else "medium" if overall < 80 else "low",
            "recommendation": recommendation,
            "components": {
                "otd": round(otd_component, 1),
                "quality": round(quality_component, 1),
                "trend": trend_component,
                "concentration": round(concentration_component, 1),
            },
        }

    async def persist(
        self,
        db: AsyncSession,
        tenant_id: str,
        supplier_id: str,
        score: dict[str, Any],
    ) -> None:
        await db.execute(
            text("""
                INSERT INTO cdm_supplier_score (
                    tenant_id, supplier_id, reliability_score, risk_tier,
                    on_time_pct, sample_size, quality_rejection_pct,
                    concentration_pct, lead_time_trend, overall_score, recommendation,
                    contributing_factors
                ) VALUES (
                    :tenant_id, :supplier_id, :reliability_score, :risk_tier,
                    :on_time_pct, :sample_size, :quality_rejection_pct,
                    :concentration_pct, :lead_time_trend, :overall_score, :recommendation,
                    CAST(:factors AS jsonb)
                )
            """),
            {
                "tenant_id": UUID(tenant_id),
                "supplier_id": UUID(supplier_id),
                "reliability_score": score["overall_score"] / 100.0,
                "risk_tier": score["risk_tier"],
                "on_time_pct": score["on_time_pct"],
                "sample_size": score["sample_size"],
                "quality_rejection_pct": score["quality_rejection_pct"],
                "concentration_pct": score["concentration_pct"],
                "lead_time_trend": score["lead_time_trend"],
                "overall_score": score["overall_score"],
                "recommendation": score.get("recommendation"),
                "factors": __import__("json").dumps(score.get("components", {})),
            },
        )
