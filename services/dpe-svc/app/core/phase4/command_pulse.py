"""M1–M6 Command module pulse for Manufacturing Intelligence hub."""

from __future__ import annotations

from typing import Any


MODULE_DEFS = [
    {
        "module_id": "M1",
        "name": "Demand Command",
        "route": "/intelligence/demand",
        "agents": ["A1", "A8"],
        "kpi_keys": ["forecast_units", "forecast_accuracy_pct", "anomalies"],
    },
    {
        "module_id": "M2",
        "name": "Production Command",
        "route": "/intelligence/production",
        "agents": ["A3", "A4", "A5"],
        "kpi_keys": ["mos_scheduled", "at_risk", "utilisation_pct"],
    },
    {
        "module_id": "M3",
        "name": "Supply Command",
        "route": "/intelligence/supply",
        "agents": ["A2", "A9"],
        "kpi_keys": ["stock_health_pct", "po_pending", "supplier_risk"],
    },
    {
        "module_id": "M4",
        "name": "Quality Command",
        "route": "/intelligence/quality",
        "agents": ["A10"],
        "kpi_keys": ["defect_rate_pct", "capa_open", "predictions"],
    },
    {
        "module_id": "M5",
        "name": "Finance Command",
        "route": "/intelligence/finance",
        "agents": ["A11", "A6"],
        "kpi_keys": ["revenue_mtd", "margin_pct", "cash_balance"],
    },
    {
        "module_id": "M6",
        "name": "Customer Command",
        "route": "/intelligence/customer",
        "agents": ["A8"],
        "kpi_keys": ["customers", "satisfaction_pct", "at_risk"],
    },
]


DEFAULT_KPIS: dict[str, dict[str, Any]] = {
    "M1": {"forecast_units": 245, "forecast_accuracy_pct": 86, "anomalies": 1},
    "M2": {"mos_scheduled": 47, "at_risk": 5, "utilisation_pct": 84},
    "M3": {"stock_health_pct": 92, "po_pending": 3, "supplier_risk": 1},
    "M4": {"defect_rate_pct": 1.8, "capa_open": 2, "predictions": 1},
    "M5": {"revenue_mtd": 2_100_000, "margin_pct": 28.4, "cash_balance": 342_000},
    "M6": {"customers": 12, "satisfaction_pct": 87, "at_risk": 0},
}


def build_intelligence_pulse(
    *,
    tenant_id: str,
    planner_name: str = "Planner",
    overlays: dict[str, dict[str, Any]] | None = None,
    attention: list[str] | None = None,
    auto_actions_overnight: int = 0,
    otd_pct: float = 89.0,
    mos_on_track: tuple[int, int] = (42, 47),
) -> dict[str, Any]:
    overlays = overlays or {}
    modules = []
    for defn in MODULE_DEFS:
        mid = defn["module_id"]
        kpis = {**DEFAULT_KPIS.get(mid, {}), **overlays.get(mid, {})}
        modules.append({**defn, "kpis": kpis, "status": "ok"})

    on_track, total = mos_on_track
    at_risk = total - on_track
    items = attention or [
        "copper wire stockout risk",
        "Winding capacity overlap",
    ]
    brief = (
        f"Good morning {planner_name}. {len(items)} things need your attention: "
        + " and ".join(items)
        + ". Everything else is handled."
    )
    return {
        "tenant_id": tenant_id,
        "pulse": {
            "mos_on_track": on_track,
            "mos_total": total,
            "at_risk": at_risk,
            "otd_pct": otd_pct,
            "margin_pct": DEFAULT_KPIS["M5"]["margin_pct"],
            "auto_actions_overnight": auto_actions_overnight,
            "brief": brief,
        },
        "modules": modules,
        "agent_activity": [
            {"agent_id": "A4", "message": "scored MOs"},
            {"agent_id": "A9", "message": "generated PO recommendations"},
            {"agent_id": "A10", "message": "flagged quality risk"},
            {"agent_id": "A11", "message": "margin alert"},
        ],
    }
