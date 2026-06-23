from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CTPResult:
    is_feasible: bool
    earliest_feasible_date: datetime | None
    confidence_score: float
    binding_constraint: str | None
    constraint_resource: str | None


async def evaluate_ctp(payload: Any, tenant_id: str) -> CTPResult:
    requested_qty = getattr(payload, "requested_qty", 100)
    priority = getattr(payload, "customer_priority", "medium")
    requested_date = getattr(payload, "requested_delivery_date", datetime.now())

    lead_time_days = 7 if priority == "high" else 14 if priority == "medium" else 21
    earliest = datetime.now(requested_date.tzinfo) + timedelta(days=lead_time_days)

    is_feasible = earliest <= requested_date

    capacity_factor = min(1.0, 1000 / max(1, requested_qty)) if requested_qty > 0 else 1.0
    confidence = round(capacity_factor * 0.85, 2)

    if not is_feasible:
        binding_constraint = "capacity"
        constraint_resource = "work_center_group_A"
    else:
        binding_constraint = None
        constraint_resource = None

    return CTPResult(
        is_feasible=is_feasible,
        earliest_feasible_date=earliest if not is_feasible else requested_date,
        confidence_score=confidence,
        binding_constraint=binding_constraint,
        constraint_resource=constraint_resource,
    )