from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from ortools.sat.python import cp_model


@dataclass
class PlantData:
    plant_id: str
    name: str
    capacity_hours: float
    cost_per_hour: float
    energy_kwh_per_hour: float
    capabilities: list[str] = field(default_factory=list)


@dataclass
class TransferRouteData:
    route_id: str
    origin_plant_id: str
    destination_plant_id: str
    transit_time_hours: float
    cost_per_unit: float
    capacity_units: int
    reliability_score: float


@dataclass
class FleetData:
    fleet_id: str
    route_id: str
    available_units: int
    max_trips_per_day: int
    cost_per_trip: float


@dataclass
class NetworkDemand:
    demand_id: str
    product_id: str
    quantity: int
    required_date: str
    priority_score: float
    penalty_cost: float
    capable_plants: list[str] = field(default_factory=list)


@dataclass
class NetworkResult:
    assignments: list[dict[str, Any]]
    transfers: list[dict[str, Any]]
    total_make_cost: float
    total_transfer_cost: float
    total_penalty: float
    objective_value: float
    solver_status: str
    unsatisfied_demands: list[dict[str, Any]] = field(default_factory=list)


def build_distance_penalty(
    origin_lat: float | None,
    origin_lon: float | None,
    dest_lat: float | None,
    dest_lon: float | None,
) -> float:
    if None in (origin_lat, origin_lon, dest_lat, dest_lon):
        return 1.0
    lat_diff = (origin_lat or 0) - (dest_lat or 0)
    lon_diff = (origin_lon or 0) - (dest_lon or 0)
    return max(1.0, (lat_diff**2 + lon_diff**2) ** 0.5 / 10.0)


def solve_network_optimization(
    plants: list[PlantData],
    routes: list[TransferRouteData],
    fleets: list[FleetData],
    demands: list[NetworkDemand],
    work_centers: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    alpha: float = 0.5,
    horizon_days: int = 14,
    solver_timeout_seconds: int = 60,
) -> NetworkResult:
    model = cp_model.CpModel()
    plant_map = {p.plant_id: p for p in plants}
    route_map: dict[tuple[str, str], TransferRouteData] = {}
    for r in routes:
        route_map[(r.origin_plant_id, r.destination_plant_id)] = r
    fleet_by_route: dict[str, list[FleetData]] = {}
    for f in fleets:
        fleet_by_route.setdefault(f.route_id, []).append(f)

    assign_vars: dict[tuple[str, str], Any] = {}
    transfer_vars: dict[tuple[str, str, str], Any] = {}
    penalty_vars: dict[str, Any] = {}

    for demand in demands:
        make_costs = []
        transfer_costs = []
        for plant_id in demand.capable_plants:
            plant = plant_map.get(plant_id)
            if not plant:
                continue
            make_cost = int(plant.cost_per_hour * 100 * demand.quantity)
            make_var = model.new_int_var(0, make_cost + 1000000, f"make_{demand.demand_id}_{plant_id}")
            is_assigned = model.new_bool_var(f"is_assigned_{demand.demand_id}_{plant_id}")
            model.add(make_var == make_cost * is_assigned)
            assign_vars[(demand.demand_id, plant_id)] = is_assigned
            make_costs.append((make_var, is_assigned))

            for dest_id in demand.capable_plants:
                if dest_id == plant_id:
                    continue
                route = route_map.get((plant_id, dest_id))
                if not route:
                    continue
                transfer_cost = int(route.cost_per_unit * 100 * demand.quantity)
                transfer_var = model.new_int_var(
                    0, 10**12,
                    f"transfer_{demand.demand_id}_{plant_id}_{dest_id}"
                )
                is_transferred = model.new_bool_var(
                    f"is_transferred_{demand.demand_id}_{plant_id}_{dest_id}"
                )
                model.add(transfer_var == transfer_cost * is_transferred)
                transfer_vars[(demand.demand_id, plant_id, dest_id)] = is_transferred
                transfer_costs.append((transfer_var, is_transferred))

        if make_costs:
            total_make = model.new_int_var(
                0, 10**12,
                f"total_make_{demand.demand_id}"
            )
            model.add(total_make == sum(c for c, _ in make_costs))
            model.add_exactly_one(v for _, v in make_costs)

        penalty_var = model.new_int_var(
            0, 10**12,
            f"penalty_{demand.demand_id}"
        )
        assigned_bools = [v for _, v in make_costs]
        penalty_value = int(demand.penalty_cost * 100 * demand.quantity)
        if assigned_bools:
            any_assigned = model.new_bool_var(f"any_assigned_{demand.demand_id}")
            model.add_max_equality(any_assigned, assigned_bools)
            model.add(penalty_var <= penalty_value * (1 - any_assigned))
            model.add(penalty_var >= penalty_value * (1 - any_assigned))
        else:
            model.add(penalty_var == penalty_value)
        penalty_vars[demand.demand_id] = penalty_var

        for plant_id in demand.capable_plants:
            plant = plant_map.get(plant_id)
            if not plant:
                continue
            wc_count = sum(
                1 for wc in work_centers
                if wc.get("plant_id") == plant_id or wc.get("work_center_id", "").startswith(plant_id[:8])
            )
            if wc_count == 0 and plant.capabilities:
                continue

    total_make_obj = model.new_int_var(0, 10**12, "total_make_obj")
    total_transfer_obj = model.new_int_var(0, 10**12, "total_transfer_obj")
    total_penalty_obj = model.new_int_var(0, 10**12, "total_penalty_obj")

    make_expressions = []
    for (d_id, p_id), is_assigned in assign_vars.items():
        demand = next(d for d in demands if d.demand_id == d_id)
        plant = plant_map[p_id]
        cost = int(plant.cost_per_hour * 100 * demand.quantity)
        make_expressions.append(cost * is_assigned)
    if make_expressions:
        model.add(total_make_obj == sum(make_expressions))
    else:
        model.add(total_make_obj == 0)

    transfer_expressions = []
    for (d_id, o_id, dest_id), is_transferred in transfer_vars.items():
        route = route_map.get((o_id, dest_id))
        if not route:
            continue
        demand = next(d for d in demands if d.demand_id == d_id)
        cost = int(route.cost_per_unit * 100 * demand.quantity)
        transfer_expressions.append(cost * is_transferred)
    if transfer_expressions:
        model.add(total_transfer_obj == sum(transfer_expressions))
    else:
        model.add(total_transfer_obj == 0)

    penalty_expressions = []
    for d_id, penalty_var in penalty_vars.items():
        penalty_expressions.append(penalty_var)
    if penalty_expressions:
        model.add(total_penalty_obj == sum(penalty_expressions))
    else:
        model.add(total_penalty_obj == 0)

    weighted_tardiness = model.new_int_var(0, 10**15, "weighted_tardiness")
    model.add(
        weighted_tardiness == int(alpha * 100) * total_penalty_obj
        + int((1 - alpha) * 100) * (total_make_obj + total_transfer_obj)
    )
    model.minimize(weighted_tardiness)

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
    transfers = []
    unsatisfied = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for (d_id, p_id), is_assigned in assign_vars.items():
            if solver.value(is_assigned):
                demand = next(d for d in demands if d.demand_id == d_id)
                plant = plant_map[p_id]
                assignments.append({
                    "demand_id": d_id,
                    "plant_id": p_id,
                    "plant_name": plant.name,
                    "quantity": demand.quantity,
                    "make_cost": plant.cost_per_hour * demand.quantity,
                })

        for (d_id, o_id, dest_id), is_transferred in transfer_vars.items():
            if solver.value(is_transferred):
                route = route_map.get((o_id, dest_id))
                demand = next(d for d in demands if d.demand_id == d_id)
                transfers.append({
                    "demand_id": d_id,
                    "origin_plant_id": o_id,
                    "destination_plant_id": dest_id,
                    "quantity": demand.quantity,
                    "transfer_cost": (route.cost_per_unit * demand.quantity) if route else 0,
                    "transit_time_hours": route.transit_time_hours if route else 0,
                })

        assigned_ids = {a["demand_id"] for a in assignments}
        for demand in demands:
            if demand.demand_id not in assigned_ids:
                unsatisfied.append({
                    "demand_id": demand.demand_id,
                    "product_id": demand.product_id,
                    "quantity": demand.quantity,
                    "reason": "no_capable_plant",
                })

    return NetworkResult(
        assignments=assignments,
        transfers=transfers,
        total_make_cost=solver.value(total_make_obj) / 100.0 if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
        total_transfer_cost=solver.value(total_transfer_obj) / 100.0 if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
        total_penalty=solver.value(total_penalty_obj) / 100.0 if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
        objective_value=solver.objective_value / 100.0 if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
        solver_status=solver_status,
        unsatisfied_demands=unsatisfied,
    )
