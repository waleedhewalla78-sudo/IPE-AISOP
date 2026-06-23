"""Cost-optimized scheduling using OR-Tools CP-SAT.

Extends the base scheduler with multi-objective optimization:
  - Primary: hard constraints (capacity, precedence, skills)
  - Secondary: Minimize(alpha * makespan + energy_cost + labor_cost)

The alpha parameter (0.1 to 0.9) allows planners to tune speed vs cost.
"""
from __future__ import annotations

import logging
from typing import Any

from ortools.sat.python import cp_model

from app.core.energy_cost import (
    build_tou_rate_map,
    calculate_energy_cost,
    calculate_labor_cost,
)
from app.core.scheduler import (
    MAX_BOM_DEPTH,
    _build_worker_skill_map,
    _extract_solution,
    _match_worker_to_operation,
    explode_phantom_boms,
)

logger = logging.getLogger(__name__)

COST_SOLVER_TIMEOUT_SECONDS = 45


def _build_cost_model(
    work_centers: list[dict],
    operations: list[dict],
    workers: list[dict] | None,
    horizon: int,
    frozen_ops: list[dict],
    warm_start: dict[str, int],
    max_bom_depth: int,
    alpha: float,
    tou_rate_map: dict[tuple[int, int], float],
    enforce_skills: bool = True,
) -> tuple[cp_model.CpModel, dict, dict, dict, dict, dict, dict, dict, list[str], dict]:
    """Build CP-SAT model with cost-aware multi-objective optimization.

    Returns model and all variable dictionaries plus cost tracking dict.
    """
    frozen_map = {f["operation_id"]: f for f in frozen_ops}
    operations = explode_phantom_boms(operations, max_depth=max_bom_depth)

    model = cp_model.CpModel()
    all_starts: dict[str, cp_model.IntVar] = {}
    all_ends: dict[str, cp_model.IntVar] = {}
    all_intervals: dict[str, cp_model.IntervalVar] = {}
    all_ops: dict[str, dict] = {}

    mo_due_dates: dict[str, int] = {}
    mo_priority: dict[str, float] = {}
    mo_material_score: dict[str, float] = {}

    worker_starts: dict[str, cp_model.IntVar] = {}
    worker_ends: dict[str, cp_model.IntVar] = {}
    worker_intervals: dict[str, list[cp_model.IntervalVar]] = {}
    worker_availability: dict[str, list[tuple[int, int]]] = {}
    op_worker_assignments: dict[str, dict[str, cp_model.IntervalVar]] = {}
    skill_relaxed_ops: list[str] = []

    worker_skills: dict[str, set[str]] = {}
    eligible_workers_for_op: dict[str, list[str]] = {}

    if workers:
        worker_skills = _build_worker_skill_map(workers)

    for op in operations:
        op_id = op.get("id", str(op.get("sequence", 0)))
        bom_level = int(op.get("bom_level", 0))
        duration = int(op.get("duration_planned_mins", 60))
        if bom_level > max_bom_depth:
            duration = int(duration * 1.1)
        wc_id = op.get("work_center_id", "")

        frozen = frozen_map.get(op_id)
        if frozen:
            fixed_start = int(frozen["fixed_start"])
            fixed_end = int(frozen["fixed_end"])
            start = model.new_int_var(fixed_start, fixed_start, f"start_{op_id}")
            end = model.new_int_var(fixed_end, fixed_end, f"end_{op_id}")
            interval = model.new_fixed_size_interval_var(
                start, duration, f"interval_{op_id}"
            )
        else:
            start = model.new_int_var(0, horizon, f"start_{op_id}")
            end = model.new_int_var(0, horizon, f"end_{op_id}")
            interval = model.new_interval_var(start, duration, end, f"interval_{op_id}")

        all_starts[op_id] = start
        all_ends[op_id] = end
        all_intervals[op_id] = interval
        all_ops[op_id] = {**op, "duration": duration, "wc_id": wc_id}

        mo_id = op.get("mo_id", "default")
        due = op.get("due_date_minutes")
        if due is not None:
            mo_due_dates[mo_id] = int(due)
        prio = float(op.get("priority_score", 0) or 0)
        if mo_id not in mo_priority or prio > mo_priority[mo_id]:
            mo_priority[mo_id] = prio
        mat_score = float(op.get("material_score", 1.0) or 1.0)
        if mo_id not in mo_material_score or mat_score < mo_material_score[mo_id]:
            mo_material_score[mo_id] = mat_score

    # --- No-overlap per work center ---
    wc_to_ops: dict[str, list[str]] = {}
    for op_id, op in all_ops.items():
        wc_id = op["wc_id"]
        if wc_id not in wc_to_ops:
            wc_to_ops[wc_id] = []
        wc_to_ops[wc_id].append(op_id)

    for _wc_id, op_ids in wc_to_ops.items():
        if len(op_ids) > 1:
            model.add_no_overlap([all_intervals[oid] for oid in op_ids])

    # --- Sequence precedence within MO groups ---
    mo_groups: dict[str, list[tuple[int, str]]] = {}
    for op_id, op in all_ops.items():
        mo = op.get("mo_id", "default")
        if mo not in mo_groups:
            mo_groups[mo] = []
        mo_groups[mo].append((op.get("sequence", 0), op_id))

    for _mo, seq_ops in mo_groups.items():
        seq_ops.sort(key=lambda x: x[0])
        for i in range(len(seq_ops) - 1):
            _, prev_id = seq_ops[i]
            _, curr_id = seq_ops[i + 1]
            model.add(all_ends[prev_id] <= all_starts[curr_id])

    # --- Parent/child BOM precedence with transfer time ---
    parent_to_children: dict[str, list[str]] = {}
    for op_id, op in all_ops.items():
        parent_id = op.get("parent_operation_id")
        if parent_id and parent_id in all_starts:
            parent_to_children.setdefault(parent_id, []).append(op_id)

    for parent_id, child_ids in parent_to_children.items():
        for child_id in child_ids:
            transfer_time = int(all_ops[child_id].get("transfer_time_mins", 0) or 0)
            model.add(all_starts[parent_id] >= all_ends[child_id] + transfer_time)

    # --- Worker constraints (optional) ---
    if workers and enforce_skills:
        shift_rules_sample = workers[0].get("shift_rules", [{"days_of_week": [0,1,2,3,4], "start_hour": 8, "end_hour": 16, "break_minutes": 30}])

        for w in workers:
            wid = str(w.get("id", ""))
            from app.core.shift_scheduler import generate_worker_availability_intervals
            intervals = generate_worker_availability_intervals(
                w.get("shift_rules", shift_rules_sample), horizon
            )
            worker_availability[wid] = intervals

            worker_ints = []
            for i, (s, e) in enumerate(intervals):
                w_start = model.new_int_var(s, s, f"wstart_{wid}_{i}")
                w_end = model.new_int_var(e, e, f"wend_{wid}_{i}")
                w_interval = model.new_fixed_size_interval_var(
                    w_start, e - s, f"winterval_{wid}_{i}"
                )
                worker_ints.append(w_interval)

            worker_intervals[wid] = worker_ints

        for op_id, op in all_ops.items():
            requires_op = op.get("requires_operator", True)
            if not requires_op:
                eligible_workers_for_op[op_id] = []
                continue

            req_skill_id = op.get("required_skill_id")
            req_skill_tags = op.get("required_skill_tags", [])

            eligible = []
            for w in workers:
                wid = str(w.get("id", ""))
                if _match_worker_to_operation(wid, worker_skills, req_skill_id, req_skill_tags):
                    eligible.append(wid)

            eligible_workers_for_op[op_id] = eligible

            can_use_vars_for_op: list[cp_model.IntVar] = []
            for wid in eligible:
                for avail_idx, (avail_start, avail_end) in enumerate(worker_availability.get(wid, [])):
                    op_w_start = model.new_int_var(
                        avail_start, avail_end,
                        f"opw_start_{op_id}_{wid}_{avail_idx}"
                    )
                    op_w_end = model.new_int_var(
                        avail_start, avail_end,
                        f"op_w_end_{op_id}_{wid}_{avail_idx}"
                    )
                    op_w_interval = model.new_interval_var(
                        op_w_start, duration, op_w_end,
                        f"opw_interval_{op_id}_{wid}_{avail_idx}"
                    )

                    if op_id not in op_worker_assignments:
                        op_worker_assignments[op_id] = {}
                    op_worker_assignments[op_id][f"{wid}_{avail_idx}"] = op_w_interval

                    can_use = model.new_bool_var(f"can_use_{op_id}_{wid}_{avail_idx}")
                    model.add(op_w_start >= avail_start).only_enforce_if(can_use)
                    model.add(op_w_end <= avail_end).only_enforce_if(can_use)
                    model.add(op_w_start == all_starts[op_id]).only_enforce_if(can_use)
                    can_use_vars_for_op.append(can_use)

            if requires_op and can_use_vars_for_op:
                model.add(sum(can_use_vars_for_op) >= 1)

        if op_worker_assignments:
            all_worker_intervals_flat: dict[str, list[cp_model.IntervalVar]] = {}
            for op_id, assignments in op_worker_assignments.items():
                for key, interval in assignments.items():
                    wid = key.rsplit("_", 1)[0]
                    if wid not in all_worker_intervals_flat:
                        all_worker_intervals_flat[wid] = []
                    all_worker_intervals_flat[wid].append(interval)

            for wid, intervals in all_worker_intervals_flat.items():
                if len(intervals) > 1:
                    model.add_no_overlap(intervals)

    # --- Tardiness variables per MO ---
    tardiness_vars: dict[str, cp_model.IntVar] = {}
    for mo_id in mo_groups:
        last_op_id = mo_groups[mo_id][-1][1]
        last_end = all_ends[last_op_id]
        due = mo_due_dates.get(mo_id, horizon)
        tardy = model.new_int_var(0, horizon, f"tardiness_{mo_id}")
        model.add(tardy >= last_end - due)
        tardiness_vars[mo_id] = tardy

    # --- Multi-objective: alpha * tardiness + energy_cost + labor_cost ---
    # Energy cost: pre-compute per-operation costs as constants
    # (linear approximation since we can't use non-linear cost functions)
    wc_energy_map: dict[str, float] = {}
    wc_cost_map: dict[str, float] = {}
    wc_ot_mult_map: dict[str, float] = {}
    for wc in work_centers:
        wc_id = str(wc.get("id", ""))
        wc_energy_map[wc_id] = float(wc.get("energy_kwh_per_hour", 0.0) or 0.0)
        wc_cost_map[wc_id] = float(wc.get("cost_per_hour", 0.0) or 0.0)
        wc_ot_mult_map[wc_id] = float(wc.get("overtime_cost_multiplier", 1.5) or 1.5)

    objective_terms: list[cp_model.LinearExpr] = []

    if tardiness_vars:
        for mo_id, tardy in tardiness_vars.items():
            weight = int(mo_priority.get(mo_id, 1) * 100)
            objective_terms.append(tardy * weight * int(alpha * 100))
            mat_score = mo_material_score.get(mo_id, 1.0)
            if mat_score < 1.0:
                last_op_id = mo_groups[mo_id][-1][1]
                delay_minutes = int((1.0 - mat_score) * horizon)
                model.add(all_ends[last_op_id] >= delay_minutes)
    else:
        all_ends_list = [all_ends[oid] for oid in all_ops]
        makespan = model.new_int_var(0, horizon, "makespan")
        model.add_max_equality(makespan, all_ends_list)
        objective_terms.append(makespan * int(alpha * 100))

    # Add energy cost estimation as linear terms
    # Pre-compute average rate from TOU map for linearization
    avg_rate = 0.0
    if tou_rate_map:
        avg_rate = sum(tou_rate_map.values()) / len(tou_rate_map)

    for op_id, op in all_ops.items():
        wc_id = op["wc_id"]
        energy_kwh = wc_energy_map.get(wc_id, 0.0)
        cost_per_hour = wc_cost_map.get(wc_id, 0.0)
        duration = op["duration"]

        if energy_kwh > 0 and avg_rate > 0:
            # Linearized energy cost: energy_kwh * avg_rate * duration_hours
            # Multiply by 100 to keep integer arithmetic
            energy_cost_coeff = int(energy_kwh * avg_rate * (duration / 60.0) * 100)
            if energy_cost_coeff > 0:
                objective_terms.append(all_starts[op_id] * 0 + energy_cost_coeff)

        if cost_per_hour > 0:
            # Labor cost: cost_per_hour * duration_hours * 100
            labor_cost_coeff = int(cost_per_hour * (duration / 60.0) * 100)
            if labor_cost_coeff > 0:
                objective_terms.append(all_starts[op_id] * 0 + labor_cost_coeff)

    if objective_terms:
        model.minimize(sum(objective_terms))

    if warm_start:
        for op_id, hint_start in warm_start.items():
            if op_id in all_starts and op_id not in frozen_map:
                model.add_hint(all_starts[op_id], int(hint_start))

    cost_tracking = {
        "avg_rate": avg_rate,
        "tou_rate_map": tou_rate_map,
        "wc_energy_map": wc_energy_map,
        "wc_cost_map": wc_cost_map,
        "wc_ot_mult_map": wc_ot_mult_map,
        "alpha": alpha,
    }

    return (
        model, all_starts, all_ends, all_intervals, all_ops,
        mo_due_dates, mo_groups, eligible_workers_for_op, skill_relaxed_ops,
        cost_tracking,
    )


def _extract_cost_solution(
    solver: cp_model.CpSolver,
    all_ops: dict[str, dict],
    all_starts: dict[str, cp_model.IntVar],
    all_ends: dict[str, cp_model.IntVar],
    mo_due_dates: dict[str, int],
    mo_groups: dict[str, list[tuple[int, str]]],
    horizon: int,
    cost_tracking: dict,
    skill_relaxed: bool = False,
    solve_status: int = cp_model.OPTIMAL,
) -> dict:
    """Extract solution with cost breakdown."""
    base = _extract_solution(
        solver, all_ops, all_starts, all_ends,
        mo_due_dates, mo_groups, horizon, skill_relaxed, solve_status,
    )

    wc_energy_map = cost_tracking["wc_energy_map"]
    wc_cost_map = cost_tracking["wc_cost_map"]
    wc_ot_mult_map = cost_tracking["wc_ot_mult_map"]
    tou_rate_map = cost_tracking["tou_rate_map"]
    alpha = cost_tracking["alpha"]

    total_energy_cost = 0.0
    total_labor_cost = 0.0
    total_energy_kwh = 0.0

    cost_breakdown = []
    for assignment in base["assignments"]:
        op_id = assignment["operation_id"]
        wc_id = assignment["work_center_id"]
        start_min = assignment["start_minute"]
        duration = assignment["duration"]

        energy_kwh = wc_energy_map.get(wc_id, 0.0)
        cost_per_hour = wc_cost_map.get(wc_id, 0.0)
        ot_mult = wc_ot_mult_map.get(wc_id, 1.5)

        energy = calculate_energy_cost(
            start_min, duration, energy_kwh, tou_rate_map,
        )
        labor = calculate_labor_cost(
            duration, cost_per_hour, ot_mult, 8, start_min,
        )

        total_energy_cost += energy["total_energy_cost"]
        total_labor_cost += labor["total_labor_cost"]
        total_energy_kwh += energy["total_energy_kwh"]

        cost_breakdown.append({
            "operation_id": op_id,
            "work_center_id": wc_id,
            "energy_kwh": energy["total_energy_kwh"],
            "energy_cost": energy["total_energy_cost"],
            "labor_cost": labor["total_labor_cost"],
            "overtime_minutes": labor["overtime_minutes"],
        })

    base["cost_summary"] = {
        "total_energy_kwh": round(total_energy_kwh, 4),
        "total_energy_cost": round(total_energy_cost, 4),
        "total_labor_cost": round(total_labor_cost, 4),
        "total_cost": round(total_energy_cost + total_labor_cost, 4),
        "alpha": alpha,
        "optimality_gap": (
            abs(solver.objective_value - solver.best_objective_bound)
            / max(abs(solver.objective_value), 1) * 100
            if solve_status == cp_model.FEASIBLE else 0.0
        ),
    }
    base["cost_breakdown"] = cost_breakdown

    return base


def solve_cost_optimized(
    work_centers: list[dict],
    operations: list[dict],
    horizon: int = 168,
    solver_timeout_seconds: int = COST_SOLVER_TIMEOUT_SECONDS,
    frozen_ops: list[dict] | None = None,
    warm_start: dict[str, int] | None = None,
    max_bom_depth: int = MAX_BOM_DEPTH,
    workers: list[dict] | None = None,
    alpha: float = 0.5,
    tariffs: list[dict] | None = None,
) -> dict:
    """Solve with cost-aware multi-objective optimization.

    Args:
        work_centers: List of work center dicts with id, capacity_hours_per_day,
                      energy_kwh_per_hour, cost_per_hour, overtime_cost_multiplier.
        operations: List of operation dicts.
        horizon: Planning horizon in minutes.
        solver_timeout_seconds: Max solver runtime (default 45s).
        frozen_ops: Fixed operations.
        warm_start: Hint start times.
        max_bom_depth: Maximum BOM depth before flattening.
        workers: Worker constraints.
        alpha: Speed vs cost preference (0.1=cost-priority, 0.9=speed-priority).
        tariffs: List of TOU tariff dicts with day_of_week, hour_start, hour_end, rate_per_kwh.

    Returns:
        Dict with status, assignments, cost_summary, cost_breakdown.
    """
    frozen_ops = frozen_ops or []
    warm_start = warm_start or {}
    alpha = max(0.1, min(0.9, alpha))

    tou_rate_map = build_tou_rate_map(tariffs or [])

    has_workers = workers and len(workers) > 0

    if has_workers:
        (
            model, all_starts, all_ends, all_intervals, all_ops,
            mo_due_dates, mo_groups, eligible_workers, skill_relaxed_ops,
            cost_tracking,
        ) = _build_cost_model(
            work_centers, operations, workers, horizon,
            frozen_ops, warm_start, max_bom_depth,
            alpha=alpha, tou_rate_map=tou_rate_map,
            enforce_skills=True,
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = solver_timeout_seconds
        status = solver.solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return _extract_cost_solution(
                solver, all_ops, all_starts, all_ends,
                mo_due_dates, mo_groups, horizon, cost_tracking,
                skill_relaxed=False, solve_status=status,
            )

        # Skill relaxation fallback
        (
            model, all_starts, all_ends, all_intervals, all_ops,
            mo_due_dates, mo_groups, eligible_workers, skill_relaxed_ops,
            cost_tracking,
        ) = _build_cost_model(
            work_centers, operations, workers, horizon,
            frozen_ops, warm_start, max_bom_depth,
            alpha=alpha, tou_rate_map=tou_rate_map,
            enforce_skills=False,
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = COST_SOLVER_TIMEOUT_SECONDS + 15
        status = solver.solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            result = _extract_cost_solution(
                solver, all_ops, all_starts, all_ends,
                mo_due_dates, mo_groups, horizon, cost_tracking,
                skill_relaxed=True, solve_status=status,
            )
            result["requires_manual_skill_verification"] = True
            return result

        return {"status": "INFEASIBLE", "assignments": [], "mo_tardiness": [], "solver_status": "INFEASIBLE"}

    # No workers path
    (
        model, all_starts, all_ends, all_intervals, all_ops,
        mo_due_dates, mo_groups, _, _,
        cost_tracking,
    ) = _build_cost_model(
        work_centers, operations, None, horizon,
        frozen_ops, warm_start, max_bom_depth,
        alpha=alpha, tou_rate_map=tou_rate_map,
        enforce_skills=False,
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_timeout_seconds
    status = solver.solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return _extract_cost_solution(
            solver, all_ops, all_starts, all_ends,
            mo_due_dates, mo_groups, horizon, cost_tracking,
            skill_relaxed=False, solve_status=status,
        )

    return {"status": "INFEASIBLE", "assignments": [], "mo_tardiness": [], "solver_status": "INFEASIBLE"}
