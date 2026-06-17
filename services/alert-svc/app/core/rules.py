"""Alert rule definitions and evaluation engine.

Evaluates incoming events (feasibility scored MOs, work center status changes)
against threshold-based rules and triggers notifications when conditions are met.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Alert:
    alert_type: str
    severity: str
    title: str
    description: str
    tenant_id: str | None = None
    entity_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


FEASIBILITY_THRESHOLD_LOW = 70
UTILIZATION_THRESHOLD_HIGH = 85


def evaluate_feasibility_event(payload: dict) -> list[Alert]:
    alerts: list[Alert] = []
    score = payload.get("feasibility_score")
    mo_id = payload.get("mo_id", "unknown")
    tenant_id = payload.get("tenant_id")

    if score is not None and score < FEASIBILITY_THRESHOLD_LOW:
        alerts.append(Alert(
            alert_type="feasibility_critical",
            severity="high",
            title=f"MO {mo_id} feasibility score critically low",
            description=(
                f"MO {mo_id} scored {score}/100 (threshold: {FEASIBILITY_THRESHOLD_LOW}). "
                f"Primary constraint: {payload.get('primary_constraint', 'unknown')}. "
                "Immediate planner review required."
            ),
            tenant_id=tenant_id,
            entity_id=mo_id,
            metadata={
                "score": score,
                "threshold": FEASIBILITY_THRESHOLD_LOW,
                "constraint": payload.get("primary_constraint"),
            },
        ))

    return alerts


def evaluate_workcenter_event(payload: dict) -> list[Alert]:
    alerts: list[Alert] = []
    utilization = payload.get("utilization_pct")
    wc_id = payload.get("work_center_id", "unknown")
    wc_name = payload.get("work_center_name", wc_id)
    tenant_id = payload.get("tenant_id")

    if utilization is not None and utilization > UTILIZATION_THRESHOLD_HIGH:
        alerts.append(Alert(
            alert_type="workcenter_overloaded",
            severity="medium",
            title=f"Work center {wc_name} utilization exceeds {UTILIZATION_THRESHOLD_HIGH}%",
            description=(
                f"Work center {wc_name} is at {utilization}% capacity. "
                "Consider redistributing load or scheduling overtime."
            ),
            tenant_id=tenant_id,
            entity_id=wc_id,
            metadata={
                "utilization_pct": utilization,
                "threshold": UTILIZATION_THRESHOLD_HIGH,
            },
        ))

    return alerts


def evaluate_event(event_type: str, payload: dict) -> list[Alert]:
    if event_type == "ipe.mo.feasibility_scored":
        return evaluate_feasibility_event(payload)
    if event_type == "ipe.workcenter.status_changed":
        return evaluate_workcenter_event(payload)
    return []
