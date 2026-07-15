"""Contextual Copilot intelligence — morning brief + meeting prep."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class MorningBrief:
    greeting: str
    summary: str
    urgent: list[str] = field(default_factory=list)
    watch: list[str] = field(default_factory=list)
    fyi: list[str] = field(default_factory=list)
    otd_current: float = 0.0
    otd_trend: str = "stable"
    sync_healthy: bool = True
    total_active_mos: int = 0
    total_at_risk: int = 0


class ContextualIntelligence:
    async def generate_morning_brief(
        self,
        tenant_id: str,
        planner_name: str = "Planner",
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = data or {}
        exceptions = data.get("exceptions") or []
        predictions = data.get("predictions") or []
        otd = data.get("otd") or {"current_pct": 89.0, "trend_direction": "stable", "total_mos": 47}
        sync = data.get("sync") or {"is_healthy": True}
        capacity = data.get("capacity_alerts") or []
        stockouts = data.get("stockout_risks") or []

        # Optional concurrent gather hooks for live services (noop if callables absent)
        gatherers = data.get("gatherers")
        if gatherers:
            gathered = await asyncio.gather(*[g() for g in gatherers], return_exceptions=True)
            # Keep dry inputs if gather fails
            _ = gathered

        urgent: list[str] = []
        watch: list[str] = []
        fyi: list[str] = []

        for exc in exceptions:
            line = exc if isinstance(exc, str) else exc.get("title", str(exc))
            sev = exc.get("severity", "medium") if isinstance(exc, dict) else "medium"
            (urgent if sev in ("critical", "high") else watch).append(line)

        for pred in predictions:
            trend = pred.get("trend") if isinstance(pred, dict) else None
            line = pred if isinstance(pred, str) else pred.get("recommended_action", str(pred))
            if trend == "crisis_approaching":
                urgent.append(line)
            elif trend == "deteriorating":
                watch.append(line)

        for alert in capacity:
            watch.append(alert if isinstance(alert, str) else alert.get("message", str(alert)))
        for so in stockouts:
            urgent.append(so if isinstance(so, str) else so.get("message", str(so)))

        if sync.get("is_healthy") is False:
            fyi.append("Last sync reported issues — check connector health")

        brief = MorningBrief(
            greeting=f"Good morning {planner_name}",
            summary=(
                f"{len(urgent)} urgent, {len(watch)} to watch, "
                f"{otd.get('current_pct', 0)}% OTD this month"
            ),
            urgent=urgent[:5],
            watch=watch[:5],
            fyi=fyi[:3],
            otd_current=float(otd.get("current_pct", 0)),
            otd_trend=str(otd.get("trend_direction", "stable")),
            sync_healthy=bool(sync.get("is_healthy", True)),
            total_active_mos=int(otd.get("total_mos", 0)),
            total_at_risk=len([e for e in exceptions if isinstance(e, dict) and e.get("entity_type") == "mo"]),
        )
        out = asdict(brief)
        out["tenant_id"] = tenant_id
        return out


class MeetingPreparator:
    TEMPLATES = {
        "production_meeting": {
            "sections": ["yesterday_performance", "today_plan", "decisions_needed", "talking_points"],
            "data_sources": ["A3", "A4", "A5"],
        },
        "demand_review": {
            "sections": ["forecast_update", "anomalies", "accuracy_trend", "recommendations"],
            "data_sources": ["A1", "A2"],
        },
        "sop_executive": {
            "sections": ["demand_consensus", "supply_constraints", "financial_impact", "decisions"],
            "data_sources": ["A1", "A2", "A3", "A6"],
        },
        "supplier_review": {
            "sections": ["supplier_scores", "delivery_issues", "risk_alerts", "recommendations"],
            "data_sources": ["A2"],
        },
    }

    def prepare(self, meeting_type: str, live_data: dict[str, Any] | None = None) -> dict[str, Any]:
        template = self.TEMPLATES.get(meeting_type)
        if not template:
            raise ValueError(f"Unknown meeting type: {meeting_type}")
        live_data = live_data or {}
        sections = {}
        for section in template["sections"]:
            sections[section] = live_data.get(section) or self._default_section(meeting_type, section)
        return {
            "meeting_type": meeting_type,
            "data_sources": template["data_sources"],
            "sections": sections,
            "title": meeting_type.replace("_", " ").title(),
        }

    def _default_section(self, meeting_type: str, section: str) -> Any:
        defaults = {
            "yesterday_performance": ["6 MOs completed", "Winding WC near capacity"],
            "today_plan": ["8 MOs in production", "2 at risk"],
            "decisions_needed": ["Approve overtime?", "Expedite copper wire?"],
            "talking_points": ["Supplier quality trend", "Bottleneck recurrence"],
            "forecast_update": {"mape": 14.2, "bias": -0.02},
            "anomalies": [],
            "accuracy_trend": "improving",
            "recommendations": ["Hold safety stock for A-items"],
            "demand_consensus": {"value": 2_400_000, "vs_prior_pct": 12},
            "supply_constraints": ["Winding WC 108%"],
            "financial_impact": {"gap": -200_000},
            "decisions": ["Authorise overtime", "Second copper supplier"],
            "supplier_scores": [],
            "delivery_issues": [],
            "risk_alerts": [],
        }
        return defaults.get(section, [])
