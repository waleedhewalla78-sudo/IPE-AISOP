"""B1.1 / B1.2 Command Center — live ops dashboard + war room."""

from __future__ import annotations

from typing import Any


def build_ops_dashboard(
    *,
    tenant_id: str,
    shift: str = "B",
    supervisor: str = "Mohamed",
    work_centres: list[dict[str, Any]] | None = None,
    alerts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    work_centres = work_centres or [
        {"id": "WC-CCS", "utilisation_pct": 62, "mo": "MO-ST-001", "product": "DT100"},
        {"id": "WC-WND", "utilisation_pct": 94, "mo": "MO-ST-003", "product": "PT500"},
        {"id": "WC-ASM", "utilisation_pct": 42, "mo": "MO-ST-008", "product": "DT250"},
        {"id": "WC-TQC", "utilisation_pct": 58, "mo": "MO-ST-002", "product": "DT250"},
        {"id": "WC-PNT", "utilisation_pct": 0, "mo": None, "product": None},
    ]
    alerts = alerts or [
        {"time": "15:23", "severity": "amber", "message": "MO-ST-003 started 15 min late"},
        {"time": "14:45", "severity": "green", "message": "MO-ST-002 completed — on time"},
        {"time": "13:10", "severity": "red", "message": "Quality hold: copper wire batch #089"},
    ]
    in_prod = sum(1 for w in work_centres if w.get("mo"))
    behind = sum(1 for a in alerts if a.get("severity") in ("amber", "red"))
    return {
        "tenant_id": tenant_id,
        "right_now": {
            "shift": shift,
            "supervisor": supervisor,
            "mos_in_production": in_prod,
            "on_schedule": max(0, in_prod - 1),
            "behind": min(behind, in_prod),
            "work_centres": work_centres,
        },
        "scorecard": {
            "output_planned": 6,
            "output_done": 4,
            "oee_pct": 78.0,
            "quality_pct": 99.2,
            "on_time_starts": "5/6",
            "scrap_pct": 0.8,
            "safety_incidents": 0,
        },
        "live_alerts": alerts,
    }


def build_war_room(
    *,
    incident_id: str,
    title: str,
    affected_mos: list[str],
    revenue_at_risk: float,
    customers: list[str],
    estimated_repair_hours: tuple[float, float] = (4.0, 8.0),
    downtime_hours_so_far: float = 2.25,
) -> dict[str, Any]:
    lo, hi = estimated_repair_hours
    options = [
        {
            "option_id": 1,
            "label": f"Wait for repair ({lo:.0f}-{hi:.0f}h)",
            "cost": 0,
            "delay_days": 1,
            "risk": "medium",
        },
        {
            "option_id": 2,
            "label": "Redirect to alternate WC / overtime",
            "cost": 4500,
            "delay_days": 0,
            "risk": "low",
        },
        {
            "option_id": 3,
            "label": "Split affected MOs / deprioritise B customers",
            "cost": 1200,
            "delay_days": 0,
            "risk": "medium",
        },
    ]
    return {
        "mode": "war_room",
        "incident_id": incident_id,
        "title": title,
        "downtime_hours_so_far": downtime_hours_so_far,
        "impact": {
            "affected_mos": affected_mos,
            "revenue_at_risk": revenue_at_risk,
            "customers": customers,
            "estimated_repair_hours": {"min": lo, "max": hi},
            "cascade_if_gt_8h": max(0, len(affected_mos) - 1),
        },
        "resolution_options": options,
        "recommended_option": 2,
        "stakeholders_notified": ["ops_director", "planner", "maintenance"],
        "status": "active",
    }
