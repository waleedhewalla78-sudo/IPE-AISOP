from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class QualityEventType(StrEnum):
    INSPECTION_FAIL = "inspection_fail"
    DEFECT_DETECTED = "defect_detected"
    REWORK_COMPLETE = "rework_complete"
    SCRAP = "scrap"
    CORRECTIVE_ACTION = "corrective_action"
    PREVENTIVE_ACTION = "preventive_action"


class Severity(StrEnum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    OBSERVATION = "observation"


class DefectCategory(StrEnum):
    DIMENSIONAL = "dimensional"
    SURFACE = "surface"
    FUNCTIONAL = "functional"
    COSMETIC = "cosmetic"
    MATERIAL = "material"
    ASSEMBLY = "assembly"
    ELECTRICAL = "electrical"
    OTHER = "other"


@dataclass
class QualityEventInput:
    event_type: str
    severity: str = "minor"
    defect_category: str | None = None
    defect_count: int = 1
    inspection_method: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    rework_required: bool = False
    rework_cycles: int = 0
    max_rework_cycles: int = 3
    scrap_quantity: int = 0
    cost_impact: float = 0.0


@dataclass
class QualityDecision:
    action: str
    rework_eligible: bool
    rework_cycles: int
    max_rework_cycles: int
    scrap_quantity: int
    status: str
    severity: str
    requires_quarantine: bool
    requires_root_cause: bool
    requires_corrective_action: bool
    escalation_level: str
    impact_summary: dict[str, Any] = field(default_factory=dict)


SEVERITY_WEIGHTS = {
    "critical": 4.0,
    "major": 3.0,
    "minor": 2.0,
    "observation": 1.0,
}

DEFECT_COST_MULTIPLIERS = {
    "dimensional": 1.5,
    "surface": 1.2,
    "functional": 2.0,
    "cosmetic": 0.8,
    "material": 1.8,
    "assembly": 1.3,
    "electrical": 1.7,
    "other": 1.0,
}

REWORK_COST_BASE = 50.0
SCRAP_COST_PER_UNIT = 100.0


def classify_severity(defect_count: int, defect_category: str | None) -> str:
    if defect_count >= 10:
        return "critical"
    if defect_count >= 5:
        return "major"
    if defect_count >= 2:
        return "minor"
    return "observation"


def calculate_cost_impact(
    defect_count: int,
    defect_category: str | None,
    scrap_quantity: int,
    rework_cycles: int,
) -> float:
    category_multiplier = DEFECT_COST_MULTIPLIERS.get(defect_category or "other", 1.0)
    rework_cost = rework_cycles * REWORK_COST_BASE * category_multiplier
    scrap_cost = scrap_quantity * SCRAP_COST_PER_UNIT * category_multiplier
    defect_cost = defect_count * 10.0 * category_multiplier
    return rework_cost + scrap_cost + defect_cost


def determine_escalation(severity: str, defect_count: int, rework_cycles: int) -> str:
    if severity == "critical" or defect_count >= 10:
        return "executive"
    if severity == "major" or defect_count >= 5 or rework_cycles >= 2:
        return "manager"
    if severity == "minor" or defect_count >= 2:
        return "supervisor"
    return "operator"


def process_quality_event(event: QualityEventInput) -> QualityDecision:
    severity = classify_severity(event.defect_count, event.defect_category)
    rework_eligible = event.rework_required and event.rework_cycles < event.max_rework_cycles
    requires_quarantine = severity in ("critical", "major") or event.defect_count >= 5
    requires_root_cause = severity in ("critical", "major")
    requires_corrective_action = severity == "critical" or event.rework_cycles >= 2

    if rework_eligible:
        action = "rework"
        status = "in_rework"
        scrap_quantity = 0
    elif event.scrap_quantity > 0 or severity == "critical":
        action = "scrap"
        status = "scapped"
        scrap_quantity = max(event.scrap_quantity, 1)
    elif event.event_type == "corrective_action":
        action = "corrective_action"
        status = "correcting"
        scrap_quantity = 0
    else:
        action = "accept_with_deviation"
        status = "closed"
        scrap_quantity = 0

    escalation = determine_escalation(severity, event.defect_count, event.rework_cycles)
    cost_impact = calculate_cost_impact(
        event.defect_count, event.defect_category, scrap_quantity, event.rework_cycles
    )

    return QualityDecision(
        action=action,
        rework_eligible=rework_eligible,
        rework_cycles=event.rework_cycles,
        max_rework_cycles=event.max_rework_cycles,
        scrap_quantity=scrap_quantity,
        status=status,
        severity=severity,
        requires_quarantine=requires_quarantine,
        requires_root_cause=requires_root_cause,
        requires_corrective_action=requires_corrective_action,
        escalation_level=escalation,
        impact_summary={
            "cost_impact": cost_impact,
            "defect_count": event.defect_count,
            "rework_cycles": event.rework_cycles,
            "scrap_quantity": scrap_quantity,
            "severity": severity,
            "escalation": escalation,
        },
    )
