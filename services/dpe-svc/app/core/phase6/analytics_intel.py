"""A14 Analytics Intelligence — SAC-equivalent.

Automated insight generation, trend detection, anomaly alerting, and a light
predictive-analytics engine. Pure statistics on caller-supplied series — no
analyst setup, no live market-data feed (market data = PH1-02 OPEN, treated as
optional injected input).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any


@dataclass
class Insight:
    insight_id: str
    category: str
    title: str
    detail: str
    confidence: float
    suggested_action: str
    severity: str = "info"


def _linreg_slope(values: list[float]) -> float:
    """Least-squares slope of ``values`` over index 0..n-1."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values, strict=False))
    return num / denom


def detect_trend(series: list[float], *, label: str = "series") -> dict[str, Any]:
    """Direction, slope, and total pct change across a numeric series."""
    if not series or len(series) < 2:
        return {
            "label": label,
            "direction": "flat",
            "slope": 0.0,
            "pct_change": 0.0,
            "points": len(series),
        }
    slope = _linreg_slope(series)
    first, last = series[0], series[-1]
    pct_change = round(((last - first) / first) * 100, 1) if first else 0.0
    if abs(pct_change) < 2.0:
        direction = "flat"
    elif pct_change > 0:
        direction = "rising"
    else:
        direction = "falling"
    return {
        "label": label,
        "direction": direction,
        "slope": round(slope, 4),
        "pct_change": pct_change,
        "first": first,
        "last": last,
        "points": len(series),
    }


def detect_anomaly(
    series: list[float],
    *,
    label: str = "series",
    z_threshold: float = 2.0,
) -> dict[str, Any]:
    """Flag the latest point as an anomaly if its z-score exceeds threshold.

    Baseline = all points except the last. Returns anomaly=false gracefully when
    there is not enough data or zero variance (avoids false precision).
    """
    if len(series) < 4:
        return {
            "label": label,
            "anomaly": False,
            "reason": "insufficient_data",
            "points": len(series),
        }
    baseline = series[:-1]
    latest = series[-1]
    mean = statistics.fmean(baseline)
    try:
        stdev = statistics.stdev(baseline)
    except statistics.StatisticsError:
        stdev = 0.0
    if stdev == 0:
        return {
            "label": label,
            "anomaly": False,
            "reason": "no_variance",
            "baseline_mean": round(mean, 2),
        }
    z = (latest - mean) / stdev
    deviation_pct = round((latest - mean) / mean * 100, 1) if mean else 0.0
    return {
        "label": label,
        "anomaly": abs(z) >= z_threshold,
        "z_score": round(z, 2),
        "latest": latest,
        "baseline_mean": round(mean, 2),
        "deviation_pct": deviation_pct,
        "direction": "spike" if z > 0 else "drop",
    }


def predict_next(
    series: list[float], *, periods: int = 1, label: str = "series"
) -> dict[str, Any]:
    """Naive linear projection with a confidence band derived from residuals."""
    if len(series) < 3:
        last = series[-1] if series else 0.0
        return {
            "label": label,
            "method": "carry_forward",
            "predictions": [round(last, 2)] * periods,
            "confidence": 0.4,
        }
    slope = _linreg_slope(series)
    n = len(series)
    intercept = statistics.fmean(series) - slope * (n - 1) / 2
    fitted = [intercept + slope * i for i in range(n)]
    residuals = [abs(a - f) for a, f in zip(series, fitted, strict=False)]
    mean_abs_res = statistics.fmean(residuals)
    scale = statistics.fmean([abs(v) for v in series]) or 1.0
    # Higher relative residual → lower confidence.
    confidence = round(max(0.3, min(0.95, 1 - (mean_abs_res / scale))), 2)
    preds = [round(intercept + slope * (n - 1 + k), 2) for k in range(1, periods + 1)]
    return {
        "label": label,
        "method": "linear_regression",
        "slope": round(slope, 4),
        "predictions": preds,
        "confidence": confidence,
    }


def generate_insights(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Produce a weekly-style auto insight report.

    ``payload`` may carry named series (demand, cost, oee, throughput, cash_cycle).
    When absent, representative demo series from the Phase 6 doc are used so the
    endpoint always returns a meaningful report shape.
    """
    payload = payload or {}
    demand = payload.get("demand_series", [8, 9, 11, 10, 12, 8, 9, 11])
    copper_cost = payload.get("copper_cost_series", [175, 181, 186, 190, 193, 196])
    oee = payload.get("oee_series", [68, 70, 72, 74, 75, 76])
    throughput = payload.get("throughput_series", [120, 122, 119, 121, 118, 102])
    cash_cycle = payload.get("cash_cycle_series", [45, 46, 48, 49, 51, 52])

    insights: list[Insight] = []

    cost_trend = detect_trend(copper_cost, label="copper_cost")
    if cost_trend["direction"] == "rising" and cost_trend["pct_change"] >= 5:
        insights.append(
            Insight(
                insight_id="INS-COST-01",
                category="cost_trend",
                title="Copper wire cost rising",
                detail=(
                    f"Copper wire cost up {cost_trend['pct_change']}% over "
                    f"{cost_trend['points']} periods. Margin pressure on copper-bearing SKUs."
                ),
                confidence=0.82,
                suggested_action="Lock 6-month supplier pricing OR adjust product pricing ~5%.",
                severity="warning",
            )
        )

    oee_trend = detect_trend(oee, label="oee")
    if oee_trend["direction"] == "rising":
        gap = round(82.0 - oee[-1], 1)
        insights.append(
            Insight(
                insight_id="INS-OPS-01",
                category="operational_benchmark",
                title="Winding OEE improving",
                detail=(
                    f"OEE improved to {oee[-1]}% (+{oee_trend['pct_change']}%). "
                    f"Industry top quartile 82%; gap {gap} pts."
                ),
                confidence=0.75,
                suggested_action="Sustain availability gains; target performance efficiency next.",
                severity="info",
            )
        )

    tp_anom = detect_anomaly(throughput, label="throughput")
    if tp_anom.get("anomaly"):
        insights.append(
            Insight(
                insight_id="INS-ANOM-01",
                category="anomaly",
                title="Testing throughput anomaly",
                detail=(
                    f"Throughput {tp_anom['direction']} "
                    f"{abs(tp_anom['deviation_pct'])}% vs baseline "
                    f"(z={tp_anom['z_score']}). No equipment issue logged."
                ),
                confidence=0.7,
                suggested_action="Investigate product-mix shift or undocumented quality holds.",
                severity="warning",
            )
        )

    cash_trend = detect_trend(cash_cycle, label="cash_conversion_cycle")
    if cash_trend["direction"] == "rising":
        insights.append(
            Insight(
                insight_id="INS-FIN-01",
                category="financial_pattern",
                title="Cash conversion cycle lengthening",
                detail=(
                    f"CCC lengthened from {cash_cycle[0]} to {cash_cycle[-1]} days "
                    f"(+{cash_trend['pct_change']}%). Working capital tied up."
                ),
                confidence=0.78,
                suggested_action="Review collection process for slowest payers.",
                severity="warning",
            )
        )

    demand_pred = predict_next(demand, periods=1, label="demand")
    insights.append(
        Insight(
            insight_id="INS-DEM-01",
            category="demand_pattern",
            title="Demand pattern prediction",
            detail=(
                f"Next-period demand projected ~{demand_pred['predictions'][0]} units "
                f"(method {demand_pred['method']})."
            ),
            confidence=demand_pred["confidence"],
            suggested_action="Pre-position materials for projected demand.",
            severity="info",
        )
    )

    return {
        "agent_id": "A14",
        "capability": "automated_insights",
        "generated": len(insights),
        "insights": [insight.__dict__ for insight in insights],
        "trends": {
            "copper_cost": cost_trend,
            "oee": oee_trend,
            "cash_cycle": cash_trend,
        },
    }


def build_predictions(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Continuous predictive-analytics engine across demand/ops/finance."""
    payload = payload or {}
    demand_by_sku = payload.get(
        "demand_by_sku",
        {
            "DT100": [40, 42, 44, 45, 47, 49],
            "DT250": [30, 29, 28, 28, 27, 26],
            "PT500": [10, 11, 9, 12, 14, 18],
        },
    )
    margin_series = payload.get("margin_series", [28, 27.5, 27, 26.5, 26, 25.5])

    demand_predictions = {
        sku: predict_next(series, periods=1, label=sku) for sku, series in demand_by_sku.items()
    }
    margin_pred = predict_next(margin_series, periods=2, label="gross_margin")

    return {
        "agent_id": "A14",
        "capability": "predictive_analytics",
        "demand_predictions": demand_predictions,
        "financial_predictions": {
            "gross_margin": margin_pred,
            "note": (
                "Market/FX/commodity live feed is PH1-02 OPEN — "
                "projections use supplied history only."
            ),
        },
    }


class AnalyticsIntelligence:
    """A14 facade."""

    agent_id = "A14"
    name = "Analytics Intelligence"

    def insights(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return generate_insights(payload)

    def predictions(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return build_predictions(payload)

    def trend(self, series: list[float], *, label: str = "series") -> dict[str, Any]:
        return {"agent_id": "A14", **detect_trend(series, label=label)}

    def anomaly(
        self, series: list[float], *, label: str = "series", z_threshold: float = 2.0
    ) -> dict[str, Any]:
        return {"agent_id": "A14", **detect_anomaly(series, label=label, z_threshold=z_threshold)}
