"""Phase 7 §5.2 — Digital Gemba Walk (real-time WC/operator/job view).

NOTE: live machine status requires IoT/MES integration (PH1-02, OPEN). This view is
served from the last-known/synthetic snapshot and is flagged ``iot_live=false``.
"""

from __future__ import annotations

from typing import Any

_STATUS_META = {
    "running": {"icon": "🟢", "label": "RUNNING"},
    "running_slow": {"icon": "🟡", "label": "RUNNING SLOW"},
    "waiting": {"icon": "🔵", "label": "WAITING"},
    "idle": {"icon": "⚪", "label": "IDLE"},
    "down": {"icon": "🔴", "label": "DOWN"},
}


def build_gemba(
    *,
    as_of: str = "2026-07-14 08:30",
    speed_threshold_pct: float = 90.0,
    work_centres: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    work_centres = work_centres or [
        {
            "wc": "WC-CCS",
            "name": "Core Cutting",
            "status": "running",
            "mo": "MO-ST-001",
            "product": "DT100",
            "progress_pct": 62,
            "operator": "Hassan",
            "speed_pct": 98,
            "quality_pct": 100,
        },
        {
            "wc": "WC-WND",
            "name": "Winding",
            "status": "running_slow",
            "mo": "MO-ST-003",
            "product": "PT500",
            "progress_pct": 45,
            "operator": "Mohamed",
            "speed_pct": 85,
            "quality_pct": 96,
            "issue": "Wire tensioner needs adjustment",
        },
        {
            "wc": "WC-ASM",
            "name": "Assembly",
            "status": "waiting",
            "operator": "Ahmed",
            "utilisation_pct": 35,
            "reason": "waiting for WC-WND output",
        },
        {
            "wc": "WC-TQC",
            "name": "Testing",
            "status": "running",
            "mo": "MO-ST-002",
            "product": "DT250",
            "operator": "Fatima",
            "quality_pct": 100,
        },
        {"wc": "WC-PNT", "name": "Painting", "status": "idle", "operator": "Sara (float)"},
    ]

    cards: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for wc in work_centres:
        meta = _STATUS_META.get(wc.get("status", "idle"), _STATUS_META["idle"])
        speed = wc.get("speed_pct")
        below = speed is not None and float(speed) < speed_threshold_pct
        card = {
            **wc,
            "status_icon": meta["icon"],
            "status_label": meta["label"],
            "speed_below_threshold": below,
        }
        cards.append(card)
        if below:
            observations.append(
                {
                    "wc": wc["wc"],
                    "severity": "amber",
                    "observation": f"Speed {speed}% below target. {wc.get('issue', '')}".strip(),
                    "action": "Maintenance to check at next break; risk of downstream delay.",
                }
            )
        elif wc.get("status") == "waiting":
            observations.append(
                {
                    "wc": wc["wc"],
                    "severity": "blue",
                    "observation": f"{wc['name']} idle due to upstream delay.",
                    "action": f"Redeploy {wc.get('operator', 'operator')} to a cross-trained WC.",
                }
            )

    return {
        "as_of": as_of,
        "iot_live": False,
        "source": "last-known snapshot (IoT/MES integration PH1-02 OPEN)",
        "work_centres": cards,
        "observations": observations,
        "summary": {
            "running": sum(1 for c in cards if c["status"] == "running"),
            "attention": sum(1 for c in cards if c["status"] in ("running_slow", "down")),
            "idle_or_waiting": sum(1 for c in cards if c["status"] in ("idle", "waiting")),
        },
    }
