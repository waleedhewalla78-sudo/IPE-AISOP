"""Phase 7 §5.3 — Andon System (digital problem escalation).

In-memory board (mirrors the phase5 ActionTracker pattern) so behaviour is
deterministic and testable without a live DB. Spec 029 dual-writes to
`cdm_andon_alert` (migration 067) via `andon_persist` when a DB session is available.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

# colour → escalation policy
_ANDON_POLICY = {
    "red": {
        "meaning": "Production stopped (machine breakdown, safety issue)",
        "notify": ["supervisor", "maintenance", "planner"],
        "response_minutes": 15,
        "escalate_after_minutes": 30,
        "escalation": "War Room auto-activated",
    },
    "yellow": {
        "meaning": "Problem detected, production continues at reduced rate",
        "notify": ["supervisor"],
        "response_minutes": 60,
        "escalate_after_minutes": None,
        "escalation": "A3 recalculates delivery-delay risk",
    },
    "blue": {
        "meaning": "Material or information needed",
        "notify": ["material_handler", "planner"],
        "response_minutes": 30,
        "escalate_after_minutes": None,
        "escalation": "A2 checks material availability and provides ETA",
    },
    "white": {
        "meaning": "Suggestion or observation",
        "notify": [],
        "response_minutes": None,
        "escalate_after_minutes": None,
        "escalation": "A14 analytics categorizes and trends",
    },
}


class AndonBoard:
    """Deterministic in-memory Andon alert board."""

    def __init__(self) -> None:
        self._alerts: dict[str, dict[str, Any]] = {}

    def trigger(
        self,
        *,
        color: str,
        work_centre: str,
        reported_by: str,
        message: str,
        impact: str | None = None,
    ) -> dict[str, Any]:
        color = color.lower()
        if color not in _ANDON_POLICY:
            color = "white"
        policy = _ANDON_POLICY[color]
        alert_id = f"AND-{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC)
        alert = {
            "id": alert_id,
            "color": color,
            "meaning": policy["meaning"],
            "work_centre": work_centre,
            "reported_by": reported_by,
            "message": message,
            "impact": impact,
            "notify": policy["notify"],
            "response_minutes": policy["response_minutes"],
            "escalate_after_minutes": policy["escalate_after_minutes"],
            "escalation": policy["escalation"],
            "status": "active",
            "triggered_at": now.isoformat(),
            "resolved_at": None,
            "resolution": None,
        }
        self._alerts[alert_id] = alert
        return alert

    def resolve(self, alert_id: str, resolution: str) -> dict[str, Any] | None:
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        alert["status"] = "resolved"
        alert["resolved_at"] = datetime.now(UTC).isoformat()
        alert["resolution"] = resolution
        return alert

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        items = list(self._alerts.values())
        if status:
            items = [a for a in items if a["status"] == status]
        return sorted(items, key=lambda a: a["triggered_at"], reverse=True)

    def board(self) -> dict[str, Any]:
        active = self.list(status="active")
        resolved = self.list(status="resolved")
        by_color: dict[str, int] = {}
        for a in self._alerts.values():
            by_color[a["color"]] = by_color.get(a["color"], 0) + 1
        return {
            "active_alerts": active,
            "resolved_today": resolved,
            "statistics": {
                "active": len(active),
                "resolved": len(resolved),
                "by_color": by_color,
            },
            "policy": _ANDON_POLICY,
        }
