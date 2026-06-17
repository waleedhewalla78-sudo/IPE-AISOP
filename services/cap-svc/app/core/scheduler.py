from ortools.sat.python import cp_model


def solve_schedule(
    work_centers: list[dict],
    operations: list[dict],
    horizon: int = 168,
    solver_timeout_seconds: int = 30,
) -> dict:
    model = cp_model.CpModel()
    all_starts: dict[str, cp_model.IntVar] = {}
    all_ends: dict[str, cp_model.IntVar] = {}
    all_intervals: dict[str, cp_model.IntervalVar] = {}
    all_ops: dict[str, dict] = {}

    mo_due_dates: dict[str, int] = {}
    mo_priority: dict[str, float] = {}

    for op in operations:
        op_id = op.get("id", str(op.get("sequence", 0)))
        duration = int(op.get("duration_planned_mins", 60))
        wc_id = op.get("work_center_id", "")
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

    wc_to_ops: dict[str, list[str]] = {}
    for op_id, op in all_ops.items():
        wc_id = op["wc_id"]
        if wc_id not in wc_to_ops:
            wc_to_ops[wc_id] = []
        wc_to_ops[wc_id].append(op_id)

    for _wc_id, op_ids in wc_to_ops.items():
        if len(op_ids) > 1:
            model.add_no_overlap([all_intervals[oid] for oid in op_ids])

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

    tardiness_vars: dict[str, cp_model.IntVar] = {}
    for mo_id in mo_groups:
        last_op_id = mo_groups[mo_id][-1][1]
        last_end = all_ends[last_op_id]
        due = mo_due_dates.get(mo_id, horizon)
        tardy = model.new_int_var(0, horizon, f"tardiness_{mo_id}")
        model.add(tardy >= last_end - due)
        tardiness_vars[mo_id] = tardy

    if tardiness_vars:
        weighted_tardiness: list[cp_model.LinearExpr] = []
        for mo_id, tardy in tardiness_vars.items():
            weight = int(mo_priority.get(mo_id, 1) * 100)
            weighted_tardiness.append(tardy * weight)
        model.minimize(sum(weighted_tardiness))
    else:
        all_ends_list = [all_ends[oid] for oid in all_ops]
        makespan = model.new_int_var(0, horizon, "makespan")
        model.add_max_equality(makespan, all_ends_list)
        model.minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_timeout_seconds
    status = solver.solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
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

        return {
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
            "assignments": assignments,
            "mo_tardiness": list(mo_tardiness.values()),
            "solver_status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
        }

    return {"status": "INFEASIBLE", "assignments": [], "mo_tardiness": [], "solver_status": "INFEASIBLE"}
