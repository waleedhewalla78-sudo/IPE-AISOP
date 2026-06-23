"""Shadow ROI validator for IPE.

Compares AI-recommended schedules against manual planner schedules
to quantify business impact (OTD improvement, cost reduction, utilization gain).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("ipe.ml.roi")


@dataclass
class ScheduleComparison:
    manual_otd_pct: float
    ai_otd_pct: float
    manual_cost: float
    ai_cost: float
    manual_utilization: float
    ai_utilization: float
    mo_count: int
    period_days: int = 30

    @property
    def otd_improvement_pct(self) -> float:
        if self.manual_otd_pct == 0:
            return 0.0
        return ((self.ai_otd_pct - self.manual_otd_pct) / self.manual_otd_pct) * 100

    @property
    def cost_savings_pct(self) -> float:
        if self.manual_cost == 0:
            return 0.0
        return ((self.manual_cost - self.ai_cost) / self.manual_cost) * 100

    @property
    def utilization_gain_pct(self) -> float:
        if self.manual_utilization == 0:
            return 0.0
        return ((self.ai_utilization - self.manual_utilization) / self.manual_utilization) * 100


@dataclass
class ROIResult:
    comparison: ScheduleComparison
    annualized_cost_savings: float
    otd_delta: float
    roi_pct: float
    confidence: float
    validated_at: str = ""
    recommendations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.validated_at:
            self.validated_at = datetime.now(UTC).isoformat()


class ShadowROIValidator:
    def __init__(self, ai_cost_per_mo: float = 2.50, planner_hourly_rate: float = 75.0) -> None:
        self._ai_cost_per_mo = ai_cost_per_mo
        self._planner_hourly_rate = planner_hourly_rate
        self._comparisons: list[ScheduleComparison] = []

    def validate(
        self,
        comparison: ScheduleComparison,
        ai_cost_per_mo: float | None = None,
    ) -> ROIResult:
        effective_ai_cost = ai_cost_per_mo or self._ai_cost_per_mo
        annualized_savings = (
            comparison.cost_savings_pct / 100
            * comparison.manual_cost
            * (365 / max(comparison.period_days, 1))
        )

        ai_total_cost = comparison.mo_count * effective_ai_cost * (365 / max(comparison.period_days, 1))
        roi_pct = ((annualized_savings - ai_total_cost) / max(ai_total_cost, 1)) * 100

        recommendations = []
        if comparison.otd_improvement_pct < 1:
            recommendations.append("OTD improvement below 1% — consider tuning scheduler parameters")
        if comparison.cost_savings_pct < 0:
            recommendations.append("AI schedule costs more than manual — review cost model")
        if comparison.utilization_gain_pct < 0:
            recommendations.append("Utilization decreased — check capacity constraints")

        result = ROIResult(
            comparison=comparison,
            annualized_cost_savings=annualized_savings,
            otd_delta=comparison.otd_improvement_pct,
            roi_pct=roi_pct,
            confidence=min(1.0, comparison.mo_count / 100),
            recommendations=recommendations,
        )

        self._comparisons.append(comparison)
        logger.info(
            "Shadow ROI validated: OTD %.1f%% → %.1f%% (Δ%.1f%%), ROI %.1f%%",
            comparison.manual_otd_pct, comparison.ai_otd_pct,
            comparison.otd_improvement_pct, roi_pct,
        )
        return result

    def get_cumulative_roi(self) -> dict[str, Any]:
        if not self._comparisons:
            return {"total_comparisons": 0, "avg_otd_delta": 0.0, "avg_roi_pct": 0.0}

        deltas = [c.otd_improvement_pct for c in self._comparisons]
        costs = [c.cost_savings_pct for c in self._comparisons]
        return {
            "total_comparisons": len(self._comparisons),
            "avg_otd_delta": sum(deltas) / len(deltas),
            "avg_cost_savings": sum(costs) / len(costs),
            "total_mo_count": sum(c.mo_count for c in self._comparisons),
        }
