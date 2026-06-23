from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class MaterialAvailability:
    product_id: str
    quantity_available: float
    quantity_required: float
    lead_time_days: int
    safety_stock: float = 0.0


@dataclass
class CapacitySlot:
    work_center_id: str
    date: str
    available_hours: float
    cost_per_hour: float = 0.0


@dataclass
class CTPOrderLine:
    order_id: str
    product_id: str
    quantity: int
    required_date: str
    priority_score: float = 0.5
    penalty_cost: float = 100.0


@dataclass
class CTPResult:
    order_id: str
    earliest_delivery_date: str
    feasible: bool
    confidence_score: float
    material_feasible: bool
    capacity_feasible: bool
    bottleneck: str | None
    material_gaps: list[dict[str, Any]] = field(default_factory=list)
    capacity_gaps: list[dict[str, Any]] = field(default_factory=list)
    fallback_used: bool = False
    solve_time_ms: float = 0.0


def check_material_feasibility(
    order: CTPOrderLine,
    materials: list[MaterialAvailability],
) -> tuple[bool, list[dict[str, Any]], float]:
    gaps = []
    total_confidence = 1.0

    for mat in materials:
        if mat.quantity_available >= mat.quantity_required + mat.safety_stock:
            continue
        shortfall = (mat.quantity_required + mat.safety_stock) - mat.quantity_available
        gaps.append({
            "product_id": mat.product_id,
            "shortfall": shortfall,
            "lead_time_days": mat.lead_time_days,
        })
        if mat.quantity_required > 0:
            confidence = mat.quantity_available / mat.quantity_required
            total_confidence *= min(1.0, confidence)

    feasible = len(gaps) == 0
    return feasible, gaps, total_confidence


def check_capacity_feasibility(
    order: CTPOrderLine,
    capacity_slots: list[CapacitySlot],
    duration_mins_per_unit: float = 60.0,
) -> tuple[bool, list[dict[str, Any]], float]:
    total_required_hours = (order.quantity * duration_mins_per_unit) / 60.0
    available_by_date: dict[str, float] = {}
    for slot in capacity_slots:
        available_by_date[slot.date] = available_by_date.get(slot.date, 0) + slot.available_hours

    gaps = []
    cumulative_available = 0.0
    sorted_dates = sorted(available_by_date.keys())
    for date in sorted_dates:
        cumulative_available += available_by_date[date]
        if cumulative_available >= total_required_hours:
            break
    else:
        shortfall_hours = total_required_hours - cumulative_available
        gaps.append({
            "shortfall_hours": shortfall_hours,
            "dates_checked": len(sorted_dates),
        })

    feasible = len(gaps) == 0
    confidence = min(1.0, cumulative_available / total_required_hours) if total_required_hours > 0 else 1.0
    return feasible, gaps, confidence


def binary_search_earliest_date(
    order: CTPOrderLine,
    materials: list[MaterialAvailability],
    capacity_slots: list[CapacitySlot],
    duration_mins_per_unit: float = 60.0,
    max_days: int = 90,
) -> CTPResult:
    start_time = time.time()

    mat_feasible, mat_gaps, mat_confidence = check_material_feasibility(order, materials)
    cap_feasible, cap_gaps, cap_confidence = check_capacity_feasibility(
        order, capacity_slots, duration_mins_per_unit
    )

    overall_feasible = mat_feasible and cap_feasible
    confidence = mat_confidence * cap_confidence

    bottleneck = None
    if not overall_feasible:
        if not mat_feasible and not cap_feasible:
            bottleneck = "material_and_capacity"
        elif not mat_feasible:
            bottleneck = "material"
        else:
            bottleneck = "capacity"

    earliest_date = order.required_date

    solve_time_ms = (time.time() - start_time) * 1000

    return CTPResult(
        order_id=order.order_id,
        earliest_delivery_date=earliest_date,
        feasible=overall_feasible,
        confidence_score=confidence,
        material_feasible=mat_feasible,
        capacity_feasible=cap_feasible,
        bottleneck=bottleneck,
        material_gaps=mat_gaps,
        capacity_gaps=cap_gaps,
        fallback_used=False,
        solve_time_ms=solve_time_ms,
    )


def solve_ctp(
    orders: list[CTPOrderLine],
    materials: list[MaterialAvailability],
    capacity_slots: list[CapacitySlot],
    duration_mins_per_unit: float = 60.0,
    max_days: int = 90,
    timeout_seconds: float = 2.0,
) -> list[CTPResult]:
    start_time = time.time()
    results = []
    for order in orders:
        if (time.time() - start_time) * 1000 > timeout_seconds * 1000:
            result = CTPResult(
                order_id=order.order_id,
                earliest_delivery_date=order.required_date,
                feasible=False,
                confidence_score=0.5,
                material_feasible=False,
                capacity_feasible=False,
                bottleneck="timeout",
                fallback_used=True,
                solve_time_ms=(time.time() - start_time) * 1000,
            )
            results.append(result)
            continue

        result = binary_search_earliest_date(
            order, materials, capacity_slots, duration_mins_per_unit, max_days
        )
        results.append(result)
    return results
