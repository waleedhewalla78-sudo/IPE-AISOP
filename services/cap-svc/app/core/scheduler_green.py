from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from ortools.sat.python import cp_model


@dataclass
class EmissionFactorData:
    energy_source: str
    region: str
    factor_kg_co2_per_kwh: float


@dataclass
class MaterialCarbonData:
    product_id: str
    kg_co2_per_unit: float
    kg_co2_per_kg: float | None = None
    recycled_content_pct: float = 0.0


@dataclass
class TransportEmissionData:
    route_id: str
    vehicle_type: str
    kg_co2_per_unit_per_km: float
    load_factor_avg: float = 0.8


@dataclass
class GreenScheduleResult:
    assignments: list[dict[str, Any]]
    total_carbon_kg: float
    total_make_cost: float
    total_tardiness: float
    objective_value: float
    solver_status: str
    carbon_breakdown: dict[str, float] = field(default_factory=dict)
    carbon_per_unit: float = 0.0


EMISSION_FACTORS_DEFAULT = {
    "grid": 0.5,
    "natural_gas": 0.2,
    "solar": 0.05,
    "wind": 0.02,
    "coal": 0.9,
}


def calculate_operation_carbon(
    duration_mins: float,
    energy_kwh_per_hour: float,
    emission_factor: float,
) -> float:
    hours = duration_mins / 60.0
    return hours * energy_kwh_per_hour * emission_factor


def calculate_transport_carbon(
    quantity: int,
    distance_km: float,
    kg_co2_per_unit_per_km: float,
    load_factor: float = 0.8,
) -> float:
    if load_factor <= 0:
        load_factor = 0.8
    effective_units = quantity * load_factor
    return effective_units * distance_km * kg_co2_per_unit_per_km


def solve_green_schedule(
    work_centers: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    emission_factors: list[EmissionFactorData],
    material_carbons: list[MaterialCarbonData],
    transport_emissions: list[TransportEmissionData],
    horizon_mins: int = 10080,
    alpha: float = 0.5,
    beta: float = 0.3,
    solver_timeout_seconds: int = 30,
) -> GreenScheduleResult:
    model = cp_model.CpModel()

    ef_map: dict[str, float] = {}
    for ef in emission_factors:
        ef_map[ef.energy_source] = ef.factor_kg_co2_per_kwh

    wc_map: dict[str, dict] = {}
    for wc in work_centers:
        wc_id = wc.get("id", "")
        energy = float(wc.get("energy_kwh_per_hour", 0))
        cost = float(wc.get("cost_per_hour", 0))
        source = wc.get("energy_source", "grid")
        ef = ef_map.get(source, EMISSION_FACTORS_DEFAULT.get(source, 0.5))
        wc_map[wc_id] = {
            "energy_kwh": energy,
            "cost_per_hour": cost,
            "emission_factor": ef,
            "carbon_per_hour": energy * ef,
        }

    op_vars: dict[str, dict[str, Any]] = {}
    for op in operations:
        op_id = op.get("id", "")
        dur = int(op.get("duration_planned_mins", 60))
        wc_id = op.get("work_center_id", "")
        wc_info = wc_map.get(wc_id, {"carbon_per_hour": 0, "cost_per_hour": 0})

        start_var = model.new_int_var(0, horizon_mins, f"start_{op_id}")
        end_var = model.new_int_var(0, horizon_mins + dur, f"end_{op_id}")
        model.add(end_var == start_var + dur)

        is_present = model.new_bool_var(f"is_present_{op_id}")

        carbon_for_op = int(wc_info["carbon_per_hour"] * dur / 60.0 * 1000)
        cost_for_op = int(wc_info["cost_per_hour"] * dur / 60.0 * 100)

        model.add(is_present == 1)

        op_vars[op_id] = {
            "start": start_var,
            "end": end_var,
            "is_present": is_present,
            "duration": dur,
            "carbon": carbon_for_op,
            "cost": cost_for_op,
            "wc_id": wc_id,
        }

    wc_groups: dict[str, list[str]] = {}
    for op in operations:
        wc_id = op.get("work_center_id", "")
        wc_groups.setdefault(wc_id, []).append(op.get("id", ""))

    for wc_id, op_ids in wc_groups.items():
        intervals = []
        for op_id in op_ids:
            v = op_vars[op_id]
            interval = model.new_interval_var(v["start"], v["duration"], v["end"], f"interval_{op_id}")
            intervals.append(interval)
        if len(intervals) > 1:
            model.add_no_overlap(intervals)

    for op in operations:
        op_id = op.get("id", "")
        pred_id = op.get("parent_operation_id")
        if pred_id and pred_id in op_vars:
            model.add(op_vars[op_id]["start"] >= op_vars[pred_id]["end"])

    total_carbon = model.new_int_var(0, 10**12, "total_carbon")
    total_cost = model.new_int_var(0, 10**12, "total_cost")

    carbon_exprs = [v["carbon"] * v["is_present"] for v in op_vars.values()]
    cost_exprs = [v["cost"] * v["is_present"] for v in op_vars.values()]

    if carbon_exprs:
        model.add(total_carbon == sum(carbon_exprs))
    else:
        model.add(total_carbon == 0)

    if cost_exprs:
        model.add(total_cost == sum(cost_exprs))
    else:
        model.add(total_cost == 0)

    weighted_obj = model.new_int_var(0, 10**15, "weighted_obj")
    model.add(
        weighted_obj == int(beta * 1000) * total_carbon
        + int((1 - alpha - beta) * 1000) * total_cost
    )
    model.minimize(weighted_obj)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_timeout_seconds
    status = solver.solve(model)

    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    solver_status = status_map.get(status, "UNKNOWN")

    assignments = []
    total_carbon_val = 0.0
    total_cost_val = 0.0
    carbon_breakdown: dict[str, float] = {}

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for op in operations:
            op_id = op.get("id", "")
            v = op_vars[op_id]
            if solver.value(v["is_present"]):
                wc_id = v["wc_id"]
                wc_info = wc_map.get(wc_id, {})
                carbon_kg = v["carbon"] / 1000.0
                cost_val = v["cost"] / 100.0

                assignments.append({
                    "operation_id": op_id,
                    "mo_id": op.get("mo_id", ""),
                    "work_center_id": wc_id,
                    "start_mins": solver.value(v["start"]),
                    "end_mins": solver.value(v["end"]),
                    "duration_mins": v["duration"],
                    "carbon_kg": carbon_kg,
                    "cost": cost_val,
                })
                total_carbon_val += carbon_kg
                total_cost_val += cost_val
                carbon_breakdown[wc_id] = carbon_breakdown.get(wc_id, 0) + carbon_kg

        total_units = len(assignments) if assignments else 1
        carbon_per_unit = total_carbon_val / total_units
    else:
        carbon_per_unit = 0

    return GreenScheduleResult(
        assignments=assignments,
        total_carbon_kg=total_carbon_val,
        total_make_cost=total_cost_val,
        total_tardiness=0.0,
        objective_value=solver.objective_value / 1000.0 if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
        solver_status=solver_status,
        carbon_breakdown=carbon_breakdown,
        carbon_per_unit=carbon_per_unit,
    )
