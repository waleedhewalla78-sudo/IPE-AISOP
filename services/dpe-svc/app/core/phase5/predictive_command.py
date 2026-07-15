"""B1.8 Predictive Command — forward look 3/7/14 days."""

from __future__ import annotations

from typing import Any


def build_predictive_command(
    *,
    horizon_days: list[int] | None = None,
    signals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate forward risks for Command Center predictive pane."""
    horizon_days = horizon_days or [3, 7, 14]
    signals = signals or [
        {
            "horizon_days": 3,
            "severity": "amber",
            "code": "SCHEDULE_SLIP",
            "message": "MO-ST-003 likely +0.5 day late if Winding stays >90%",
            "mo_ids": ["MO-ST-003"],
            "confidence": 0.78,
        },
        {
            "horizon_days": 7,
            "severity": "red",
            "code": "MATERIAL_STOCKOUT",
            "message": "RM-CW25 days-to-zero ≈ 4 without PO today",
            "mo_ids": ["MO-ST-004", "MO-ST-008"],
            "confidence": 0.86,
        },
        {
            "horizon_days": 14,
            "severity": "amber",
            "code": "CAPACITY_PEAK",
            "message": "Winding weekly util peaks 113% in W31 without leveling",
            "mo_ids": [],
            "confidence": 0.81,
        },
        {
            "horizon_days": 14,
            "severity": "blue",
            "code": "OTD_TREND",
            "message": "Factory OTD projected 86% → 82% if no action on copper",
            "mo_ids": [],
            "confidence": 0.72,
        },
    ]
    by_horizon: dict[str, list[dict[str, Any]]] = {str(d): [] for d in horizon_days}
    for sig in signals:
        key = str(int(sig.get("horizon_days") or 7))
        by_horizon.setdefault(key, []).append(sig)

    red = sum(1 for s in signals if s.get("severity") == "red")
    return {
        "horizons_days": horizon_days,
        "by_horizon": by_horizon,
        "signals": signals,
        "summary": {
            "total_signals": len(signals),
            "critical": red,
            "recommended_actions": [
                "Run MRP / approve critical copper PO (A9)",
                "Level W31 Winding load (A3)",
                "Open War Room if downtime > 2h on WND#2",
            ],
        },
        "agent": "A4+A7",
    }
