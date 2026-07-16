"""Phase 7 §5.4 — KPI Tree (factory → department → work centre → operator)."""

from __future__ import annotations

from typing import Any


def build_kpi_tree(
    *,
    factory: dict[str, Any] | None = None,
    departments: list[dict[str, Any]] | None = None,
    work_centres: list[dict[str, Any]] | None = None,
    operators: dict[str, list[dict[str, Any]]] | None = None,
    oee_attention_threshold: float = 75.0,
) -> dict[str, Any]:
    """Drill-down KPI hierarchy with attention flags at each level."""

    factory = factory or {"otd_pct": 89, "revenue_usd": 2_100_000, "oee_pct": 76}
    departments = departments or [
        {"name": "Production", "otd_pct": 89, "oee_pct": 76, "adherence_pct": 83},
        {"name": "Quality", "fpy_pct": 97, "capa_open": 2, "cost_usd": 12_000},
        {"name": "Materials", "stock_health_pct": 92, "stockout": 0, "excess_usd": 45_000},
        {"name": "Maintenance", "mtbf_h": 120, "mttr_h": 2.5, "pm_compliance_pct": 88},
    ]
    work_centres = work_centres or [
        {"wc": "WC-CCS", "oee_pct": 82, "utilisation_pct": 65, "quality_pct": 99},
        {"wc": "WC-WND", "oee_pct": 71, "utilisation_pct": 94, "quality_pct": 96},
        {"wc": "WC-ASM", "oee_pct": 78, "utilisation_pct": 55, "quality_pct": 98},
        {"wc": "WC-TQC", "oee_pct": 85, "utilisation_pct": 48, "quality_pct": 100},
        {"wc": "WC-PNT", "oee_pct": 80, "utilisation_pct": 42, "quality_pct": 99},
    ]
    operators = operators or {
        "WC-WND": [
            {"name": "Mohamed", "output_pct": 95, "quality_pct": 96, "attendance_pct": 100},
            {"name": "Sara", "output_pct": 92, "quality_pct": 98, "attendance_pct": 95},
            {
                "name": "Omar",
                "shift": "B",
                "output_pct": 88,
                "quality_pct": 94,
                "attendance_pct": 98,
            },
            {
                "name": "Layla",
                "shift": "B",
                "output_pct": 90,
                "quality_pct": 97,
                "attendance_pct": 100,
            },
        ]
    }

    wc_nodes = []
    for wc in work_centres:
        flag = float(wc.get("oee_pct", 100)) < oee_attention_threshold
        wc_nodes.append({**wc, "attention": flag, "operators": operators.get(wc["wc"], [])})

    return {
        "level_0_factory": factory,
        "level_1_departments": departments,
        "level_2_work_centres": wc_nodes,
        "level_3_operators": operators,
        "attention_work_centres": [w["wc"] for w in wc_nodes if w["attention"]],
        "drill_down": "Click any KPI → trend, root cause, improvement actions",
    }
