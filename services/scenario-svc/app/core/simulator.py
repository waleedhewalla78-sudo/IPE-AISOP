"""Compute KPI deltas from scenario parameter overlays."""

from __future__ import annotations


DEFAULT_BASELINE = {
    "otd_pct": 87.5,
    "avg_feasibility": 74.9,
    "orders_at_risk": 1.0,
    "total_cost_usd": 125000.0,
    "capacity_util_pct": 82.0,
}


def parse_multiplier(raw: str, default: float = 1.0) -> float:
    try:
        if raw.endswith("%"):
            return 1.0 + float(raw.rstrip("%")) / 100.0
        return float(raw)
    except ValueError:
        return default


def simulate_kpis(parameters: dict[str, str]) -> dict[str, float]:
    baseline = dict(DEFAULT_BASELINE)
    demand_mult = parse_multiplier(parameters.get("demand_change_pct", "0%"))
    capacity_mult = parse_multiplier(parameters.get("capacity_change_pct", "0%"))
    lead_time_mult = parse_multiplier(parameters.get("lead_time_change_pct", "0%"))

    baseline["orders_at_risk"] = max(0.0, baseline["orders_at_risk"] * demand_mult)
    baseline["capacity_util_pct"] = min(100.0, baseline["capacity_util_pct"] * capacity_mult)
    baseline["otd_pct"] = max(50.0, baseline["otd_pct"] - (lead_time_mult - 1.0) * 15.0)
    baseline["total_cost_usd"] = baseline["total_cost_usd"] * demand_mult * (2.0 - capacity_mult * 0.5)
    baseline["avg_feasibility"] = max(40.0, baseline["avg_feasibility"] - (demand_mult - 1.0) * 20.0)
    return {k: round(v, 2) for k, v in baseline.items()}


def compare_scenarios(results: list[dict[str, float]], baseline: dict[str, float]) -> list[dict]:
    comparisons = []
    for idx, result in enumerate(results):
        deltas = {k: round(result.get(k, 0) - baseline.get(k, 0), 2) for k in baseline}
        score = round(
            result.get("otd_pct", 0) * 0.4
            + result.get("avg_feasibility", 0) * 0.3
            - result.get("orders_at_risk", 0) * 5
            - result.get("total_cost_usd", 0) / 10000 * 0.1,
            2,
        )
        comparisons.append({"index": idx, "deltas": deltas, "fitness_score": score})
    return comparisons
