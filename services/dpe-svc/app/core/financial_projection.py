from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class BOMComponent:
    component_id: str
    quantity_per: float
    standard_cost: float = 0.0
    scrap_rate_pct: float = 0.0


@dataclass
class RoutingStep:
    work_center_id: str
    duration_mins: float
    cost_per_hour: float = 0.0
    energy_kwh_per_hour: float = 0.0
    energy_cost_per_kwh: float = 0.0


@dataclass
class FinancialProjectionInput:
    product_id: str
    quantity: int
    selling_price: float = 0.0
    bom_components: list[BOMComponent] = field(default_factory=list)
    routing_steps: list[RoutingStep] = field(default_factory=list)
    overhead_pct: float = 0.15
    labor_cost_per_hour: float = 50.0


@dataclass
class FinancialProjectionResult:
    product_id: str
    quantity: int
    unit_cost: float
    total_cost: float
    revenue: float
    margin: float
    margin_pct: float
    labor_cost: float
    material_cost: float
    energy_cost: float
    overhead_cost: float
    wip_value: float
    cost_breakdown: dict[str, float] = field(default_factory=dict)
    margin_alert: str | None = None


def calculate_material_cost(
    bom_components: list[BOMComponent],
    quantity: int,
) -> tuple[float, float]:
    total = 0.0
    for comp in bom_components:
        effective_qty = comp.quantity_per * quantity * (1 + comp.scrap_rate_pct / 100.0)
        total += effective_qty * comp.standard_cost
    unit_cost = total / quantity if quantity > 0 else 0.0
    return total, unit_cost


def calculate_labor_cost(
    routing_steps: list[RoutingStep],
    quantity: int,
    labor_cost_per_hour: float = 50.0,
) -> float:
    total_hours = 0.0
    for step in routing_steps:
        total_hours += (step.duration_mins * quantity) / 60.0
    return total_hours * labor_cost_per_hour


def calculate_energy_cost(
    routing_steps: list[RoutingStep],
    quantity: int,
) -> float:
    total_cost = 0.0
    for step in routing_steps:
        hours = (step.duration_mins * quantity) / 60.0
        total_cost += hours * step.energy_kwh_per_hour * step.energy_cost_per_kwh
    return total_cost


def calculate_wip_value(
    bom_components: list[BOMComponent],
    routing_steps: list[RoutingStep],
    quantity: int,
    completion_pct: float = 100.0,
) -> float:
    material_total, _ = calculate_material_cost(bom_components, quantity)
    labor = calculate_labor_cost(routing_steps, quantity)
    energy = calculate_energy_cost(routing_steps, quantity)
    total = material_total + labor + energy
    return total * (completion_pct / 100.0)


def assess_margin(margin_pct: float) -> str | None:
    if margin_pct < 0:
        return "negative_margin"
    if margin_pct < 5:
        return "low_margin_warning"
    if margin_pct < 10:
        return "margin_below_target"
    return None


def generate_financial_projection(
    input_data: FinancialProjectionInput,
) -> FinancialProjectionResult:
    material_cost, material_unit_cost = calculate_material_cost(
        input_data.bom_components, input_data.quantity
    )
    labor_cost = calculate_labor_cost(
        input_data.routing_steps, input_data.quantity, input_data.labor_cost_per_hour
    )
    energy_cost = calculate_energy_cost(input_data.routing_steps, input_data.quantity)
    overhead_cost = (material_cost + labor_cost + energy_cost) * input_data.overhead_pct

    total_cost = material_cost + labor_cost + energy_cost + overhead_cost
    unit_cost = total_cost / input_data.quantity if input_data.quantity > 0 else 0.0
    revenue = input_data.selling_price * input_data.quantity
    margin = revenue - total_cost
    margin_pct = (margin / revenue * 100.0) if revenue > 0 else 0.0

    wip_value = calculate_wip_value(
        input_data.bom_components, input_data.routing_steps, input_data.quantity
    )

    margin_alert = assess_margin(margin_pct)

    cost_breakdown = {
        "material": material_cost,
        "labor": labor_cost,
        "energy": energy_cost,
        "overhead": overhead_cost,
        "total": total_cost,
    }

    return FinancialProjectionResult(
        product_id=input_data.product_id,
        quantity=input_data.quantity,
        unit_cost=unit_cost,
        total_cost=total_cost,
        revenue=revenue,
        margin=margin,
        margin_pct=margin_pct,
        labor_cost=labor_cost,
        material_cost=material_cost,
        energy_cost=energy_cost,
        overhead_cost=overhead_cost,
        wip_value=wip_value,
        cost_breakdown=cost_breakdown,
        margin_alert=margin_alert,
    )
