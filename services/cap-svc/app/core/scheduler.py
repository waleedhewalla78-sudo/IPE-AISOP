from ortools.sat.python import cp_model

from app.core.shift_scheduler import generate_worker_availability_intervals

MAX_BOM_DEPTH = 5
SKILL_RELAXATION_TIMEOUT_SECONDS = 60


def explode_phantom_boms(operations: list[dict], max_depth: int = MAX_BOM_DEPTH) -> list[dict]:
    """Recursively expand phantom BOMs by promoting children to parent level.

    Phantom BOMs (is_phantom=True) are intermediate assemblies that are not
    physically stocked. Their child operations are promoted to become direct
    children of the phantom's parent, and the phantom node is removed.

    When BOM depth exceeds max_depth, the deepest operations are aggregated
    into a single block with 10% duration inflation to account for overhead.

    Args:
        operations: List of operation dicts with keys: id, mo_id, sequence,
                    work_center_id, duration_planned_mins, parent_operation_id,
                    bom_level, is_phantom, transfer_time_mins.
        max_depth: Maximum allowed BOM depth. Operations beyond this depth
                   are aggregated into a single block with inflated duration.

    Returns:
        Flattened list of operations with phantom nodes removed and children promoted.
    """
    op_map: dict[str, dict] = {op.get("id"): op for op in operations if op.get("id")}
    children_map: dict[str, list[str]] = {}
    root_ids: list[str] = []

    for op in operations:
        parent_id = op.get("parent_operation_id")
        if parent_id and parent_id in op_map:
            children_map.setdefault(parent_id, []).append(op["id"])
        else:
            root_ids.append(op["id"])

    phantom_ids: set[str] = set()

    def _collect_surviving(op_id: str, depth: int) -> list[dict]:
        """Collect surviving operations, expanding phantoms and enforcing depth."""
        op = op_map[op_id]
        kids = children_map.get(op_id, [])

        if op.get("is_phantom"):
            phantom_ids.add(op_id)
            result = []
            for kid_id in kids:
                result.extend(_collect_surviving(kid_id, depth + 1))
            return result

        bom_level = int(op.get("bom_level", 0))
        if bom_level > max_depth:
            surviving = dict(op)
            surviving["duration_planned_mins"] = int(
                surviving.get("duration_planned_mins", 60) * 1.1
            )
            return [surviving]

        if not kids:
            return [dict(op)]

        result = [dict(op)]
        for kid_id in kids:
            result.extend(_collect_surviving(kid_id, depth + 1))
        return result

    result: list[dict] = []
    for root_id in root_ids:
        result.extend(_collect_surviving(root_id, 0))

    return result


def _build_worker_skill_map(workers: list[dict]) -> dict[str, set[str]]:
    """Build a mapping from worker_id to their skill set."""
    worker_skills: dict[str, set[str]] = {}
    for w in workers:
        wid = str(w.get("id", ""))
        skills = set(w.get("skill_ids", []))
        skill_tags = set(w.get("skill_tags", []))
        worker_skills[wid] = skills | skill_tags
    return worker_skills


def _match_worker_to_operation(
    worker_id: str,
    worker_skills: dict[str, set[str]],
    required_skill_id: str | None,
    required_skill_tags: list[str],
) -> bool:
    """Check if a worker has the required skills for an operation.

    If no skill requirements are specified, any worker can perform the operation.
    """
    if not required_skill_id and not required_skill_tags:
        return True

    skills = worker_skills.get(worker_id, set())

    if required_skill_id and required_skill_id in skills:
        return True

    if required_skill_tags and all(tag in skills for tag in required_skill_tags):
        return True

    return False


def _build_model(
    work_centers: list[dict],
    operations: list[dict],
    workers: list[dict] | None,
    horizon: int,
    frozen_ops: list[dict],
    warm_start: dict[str, int],
    max_bom_depth: int,
    enforce_skills: bool = True,
) -> tuple[cp_model.CpModel, dict, dict, dict, dict, dict, dict, dict, list[str]]:
    """Build the CP-SAT model with optional worker constraints.

    Returns model and all variable dictionaries needed for extraction.
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

    # Worker variables
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

    # --- No-overlap per work center (machine constraint) ---
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
            model.add(
                all_starts[parent_id] >= all_ends[child_id] + transfer_time
            )

    # --- Worker constraints (optional) ---
    if workers and enforce_skills:
        shift_rules_sample = workers[0].get("shift_rules", [{"days_of_week": [0,1,2,3,4], "start_hour": 8, "end_hour": 16, "break_minutes": 30}])

        for w in workers:
            wid = str(w.get("id", ""))
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

        # Determine eligible workers per operation
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

            # Create worker interval variables per operation
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

                    # Link: operation can only use worker interval if they overlap
                    # This is the PerformWork pattern
                    can_use = model.new_bool_var(f"can_use_{op_id}_{wid}_{avail_idx}")
                    model.add(op_w_start >= avail_start).only_enforce_if(can_use)
                    model.add(op_w_end <= avail_end).only_enforce_if(can_use)
                    model.add(op_w_start == all_starts[op_id]).only_enforce_if(can_use)
                    can_use_vars_for_op.append(can_use)

            # If requires_operator and has eligible workers, at least one must be assigned
            if requires_op and can_use_vars_for_op:
                model.add(sum(can_use_vars_for_op) >= 1)

        # No worker can be assigned to two overlapping operations
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

    objective_terms: list[cp_model.LinearExpr] = []

    if tardiness_vars:
        for mo_id, tardy in tardiness_vars.items():
            weight = int(mo_priority.get(mo_id, 1) * 100)
            objective_terms.append(tardy * weight)
            mat_score = mo_material_score.get(mo_id, 1.0)
            if mat_score < 1.0:
                last_op_id = mo_groups[mo_id][-1][1]
                delay_minutes = int((1.0 - mat_score) * horizon)
                model.add(all_ends[last_op_id] >= delay_minutes)
    else:
        all_ends_list = [all_ends[oid] for oid in all_ops]
        makespan = model.new_int_var(0, horizon, "makespan")
        model.add_max_equality(makespan, all_ends_list)
        objective_terms.append(makespan)

    if objective_terms:
        model.minimize(sum(objective_terms))

    if warm_start:
        for op_id, hint_start in warm_start.items():
            if op_id in all_starts and op_id not in frozen_map:
                model.add_hint(all_starts[op_id], int(hint_start))

    return (
        model, all_starts, all_ends, all_intervals, all_ops,
        mo_due_dates, mo_groups, eligible_workers_for_op, skill_relaxed_ops,
    )


def _extract_solution(
    solver: cp_model.CpSolver,
    all_ops: dict[str, dict],
    all_starts: dict[str, cp_model.IntVar],
    all_ends: dict[str, cp_model.IntVar],
    mo_due_dates: dict[str, int],
    mo_groups: dict[str, list[tuple[int, str]]],
    horizon: int,
    skill_relaxed: bool = False,
    solve_status: int = cp_model.OPTIMAL,
) -> dict:
    """Extract solution from a solved model."""
    assignments = []
    wc_load: dict[str, int] = {}
    for op_id in all_ops:
        op = all_ops[op_id]
        start = solver.value(all_starts[op_id])
        end = solver.value(all_ends[op_id])
        wc_id = op["wc_id"]
        wc_load[wc_id] = wc_load.get(wc_id, 0) + op["duration"]
        assignments.append({
            "operation_id": op_id,
            "work_center_id": wc_id,
            "start_minute": start,
            "end_minute": end,
            "duration": op["duration"],
            "operation_name": op.get("operation_name", ""),
            "mo_id": op.get("mo_id", ""),
            "sequence": op.get("sequence", 0),
            "bom_level": op.get("bom_level", 0),
            "parent_operation_id": op.get("parent_operation_id"),
            "on_time": end <= mo_due_dates.get(op.get("mo_id", ""), horizon) if op.get("mo_id") else True,
        })

    mo_tardiness = {}
    for mo_id in mo_groups:
        last_op_id = mo_groups[mo_id][-1][1]
        last_end_val = solver.value(all_ends[last_op_id])
        due = mo_due_dates.get(mo_id, horizon)
        mo_tardiness[mo_id] = {
            "mo_id": mo_id,
            "completion_minute": last_end_val,
            "due_date_minute": due,
            "tardiness_minutes": max(0, last_end_val - due),
            "on_time": last_end_val <= due,
        }

    status = "OPTIMAL" if solve_status == cp_model.OPTIMAL else "FEASIBLE"
    return {
        "status": status,
        "assignments": assignments,
        "mo_tardiness": list(mo_tardiness.values()),
        "solver_status": status,
        "skill_relaxed": skill_relaxed,
    }


def solve_schedule(
    work_centers: list[dict],
    operations: list[dict],
    horizon: int = 168,
    solver_timeout_seconds: int = 30,
    frozen_ops: list[dict] | None = None,
    warm_start: dict[str, int] | None = None,
    max_bom_depth: int = MAX_BOM_DEPTH,
    workers: list[dict] | None = None,
) -> dict:
    """Solve finite capacity scheduling problem with optional worker constraints.

    Args:
        work_centers: List of work center dicts with id, capacity_hours_per_day.
        operations: List of operation dicts with id, mo_id, sequence, work_center_id,
                    duration_planned_mins, due_date_minutes, priority_score,
                    parent_operation_id, bom_level, transfer_time_mins,
                    required_skill_id, required_skill_tags, requires_operator.
        horizon: Planning horizon in minutes (default 168h = 7 days).
        solver_timeout_seconds: Max solver runtime.
        frozen_ops: List of {operation_id, fixed_start, fixed_end} dicts for
                    operations that must stay at their current times.
        warm_start: Dict of {operation_id: start_minute} hints for the solver.
        max_bom_depth: Maximum allowed BOM depth before flattening.
        workers: List of worker dicts with id, skill_ids, skill_tags, shift_rules.
                 If None or empty, worker constraints are skipped.

    Returns:
        Dict with status, assignments, mo_tardiness, solver_status, skill_relaxed flag.
    """
    frozen_ops = frozen_ops or []
    warm_start = warm_start or {}
    skill_relaxed = False

    has_workers = workers and len(workers) > 0

    # Phase 1: Try with full worker/skill constraints
    if has_workers:
        (
            model, all_starts, all_ends, all_intervals, all_ops,
            mo_due_dates, mo_groups, eligible_workers, skill_relaxed_ops,
        ) = _build_model(
            work_centers, operations, workers, horizon,
            frozen_ops, warm_start, max_bom_depth,
            enforce_skills=True,
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = solver_timeout_seconds
        status = solver.solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return _extract_solution(
                solver, all_ops, all_starts, all_ends,
                mo_due_dates, mo_groups, horizon, skill_relaxed=False,
                solve_status=status,
            )

        # Phase 2: Skill Relaxation fallback - relax skill constraints
        skill_relaxed = True
        (
            model, all_starts, all_ends, all_intervals, all_ops,
            mo_due_dates, mo_groups, eligible_workers, skill_relaxed_ops,
        ) = _build_model(
            work_centers, operations, workers, horizon,
            frozen_ops, warm_start, max_bom_depth,
            enforce_skills=False,
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = SKILL_RELAXATION_TIMEOUT_SECONDS
        status = solver.solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            result = _extract_solution(
                solver, all_ops, all_starts, all_ends,
                mo_due_dates, mo_groups, horizon, skill_relaxed=True,
                solve_status=status,
            )
            result["requires_manual_skill_verification"] = True
            return result

        return {"status": "INFEASIBLE", "assignments": [], "mo_tardiness": [], "solver_status": "INFEASIBLE"}

    # No workers - solve without labor constraints
    (
        model, all_starts, all_ends, all_intervals, all_ops,
        mo_due_dates, mo_groups, _, _,
    ) = _build_model(
        work_centers, operations, None, horizon,
        frozen_ops, warm_start, max_bom_depth,
        enforce_skills=False,
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_timeout_seconds
    status = solver.solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return _extract_solution(
            solver, all_ops, all_starts, all_ends,
            mo_due_dates, mo_groups, horizon, skill_relaxed=False,
            solve_status=status,
        )

    from app.core.heuristic_scheduler import heuristic_schedule

    heuristic = heuristic_schedule(work_centers, operations, horizon)
    if heuristic.get("assignments"):
        return heuristic

    return {"status": "INFEASIBLE", "assignments": [], "mo_tardiness": [], "solver_status": "INFEASIBLE"}
