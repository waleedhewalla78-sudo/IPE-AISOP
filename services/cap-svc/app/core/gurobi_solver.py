"""Gurobi solver implementing the ISolver interface.

Falls back to ORToolsSolver when Gurobi license is not available.
"""
from __future__ import annotations

import logging
import time

from ipe_shared.solver.interface import (
    Assignment,
    Constraint,
    ConstraintType,
    ISolver,
    MOTardiness,
    OperationInput,
    ScheduleResult,
    SolverContext,
    SolverStatus,
)

logger = logging.getLogger(__name__)

_GUROBI_AVAILABLE = False
_GUROBI_IMPORT_ERROR: str | None = None

try:
    import gurobipy as gp
    from gurobipy import GRB

    _GUROBI_AVAILABLE = True
except ImportError:
    _GUROBI_IMPORT_ERROR = "gurobipy not installed"
except Exception as e:
    _GUROBI_IMPORT_ERROR = str(e)


def _check_gurobi_license() -> tuple[bool, str]:
    if not _GUROBI_AVAILABLE:
        return False, _GUROBI_IMPORT_ERROR or "gurobipy not installed"
    try:
        with gp.Env(params={"OutputFlag": 0}) as env:
            env.start()
        return True, ""
    except gp.GurobiError as e:
        return False, f"Gurobi license error: {e}"
    except Exception as e:
        return False, f"Gurobi env error: {e}"


def _solve_with_gurobi(context: SolverContext) -> ScheduleResult:
    start_time = time.time()

    model = gp.Model("ipe_schedule")
    model.Params.OutputFlag = 0
    model.Params.TimeLimit = context.config.solver_timeout_seconds

    horizon = context.horizon

    start_vars: dict[str, gp.Var] = {}
    end_vars: dict[str, gp.Var] = {}

    for op in context.operations:
        s = model.addVar(lb=0, ub=horizon, name=f"start_{op.id}")
        e = model.addVar(lb=0, ub=horizon + op.duration_planned_mins, name=f"end_{op.id}")
        model.addConstr(e == s + op.duration_planned_mins, f"duration_{op.id}")
        start_vars[op.id] = s
        end_vars[op.id] = e

    wc_ops: dict[str, list[str]] = {}
    for op in context.operations:
        wc_ops.setdefault(op.work_center_id, []).append(op.id)

    for wc_id, op_ids in wc_ops.items():
        if len(op_ids) > 1:
            for i in range(len(op_ids)):
                for j in range(i + 1, len(op_ids)):
                    o1, o2 = op_ids[i], op_ids[j]
                    b = model.addVar(vtype=GRB.BINARY, name=f"seq_{o1}_{o2}")
                    model.addConstr(start_vars[o2] >= end_vars[o1] - horizon * (1 - b), f"seq1_{o1}_{o2}")
                    model.addConstr(start_vars[o1] >= end_vars[o2] - horizon * b, f"seq2_{o1}_{o2}")

    mo_groups: dict[str, list[OperationInput]] = {}
    for op in context.operations:
        mo_groups.setdefault(op.mo_id, []).append(op)

    for mo_id, mo_ops in mo_groups.items():
        mo_ops.sort(key=lambda x: x.sequence)
        for i in range(len(mo_ops) - 1):
            transfer = mo_ops[i + 1].transfer_time_mins
            model.addConstr(
                end_vars[mo_ops[i].id] + transfer <= start_vars[mo_ops[i + 1].id],
                f"prec_{mo_ops[i].id}_{mo_ops[i + 1].id}",
            )

    parent_to_children: dict[str, list] = {}
    op_by_id = {op.id: op for op in context.operations}
    for op in context.operations:
        if op.parent_operation_id and op.parent_operation_id in start_vars:
            parent_to_children.setdefault(op.parent_operation_id, []).append(op.id)

    for parent_id, child_ids in parent_to_children.items():
        parent_op = op_by_id[parent_id]
        for child_id in child_ids:
            child_op = op_by_id[child_id]
            transfer = child_op.transfer_time_mins
            if parent_op.sequence > child_op.sequence:
                model.addConstr(
                    start_vars[parent_id] >= end_vars[child_id] + transfer,
                    f"bom_{child_id}_{parent_id}",
                )
            else:
                model.addConstr(
                    start_vars[child_id] >= end_vars[parent_id] + transfer,
                    f"bom_{child_id}_{parent_id}",
                )

    for f in context.frozen_ops:
        if f.operation_id in start_vars:
            model.addConstr(start_vars[f.operation_id] == f.fixed_start, f"freeze_start_{f.operation_id}")
            model.addConstr(end_vars[f.operation_id] == f.fixed_end, f"freeze_end_{f.operation_id}")

    tardiness_vars: dict[str, gp.Var] = {}
    mo_due: dict[str, int] = {}
    for mo_id, mo_ops in mo_groups.items():
        last_op = mo_ops[-1]
        due = last_op.due_date_minutes if last_op.due_date_minutes else horizon
        mo_due[mo_id] = due
        t = model.addVar(lb=0, name=f"tardiness_{mo_id}")
        model.addConstr(t >= end_vars[last_op.id] - due, f"tardy_def_{mo_id}")
        tardiness_vars[mo_id] = t

    mo_priority: dict[str, float] = {}
    objective = 0
    for mo_id, mo_ops in mo_groups.items():
        max_prio = max((op.priority_score for op in mo_ops), default=1.0)
        mo_priority[mo_id] = max_prio
        if mo_id in tardiness_vars:
            objective += int(max_prio * 100) * tardiness_vars[mo_id]

    if not tardiness_vars:
        makespan = model.addVar(lb=0, name="makespan")
        for op_id in end_vars:
            model.addConstr(makespan >= end_vars[op_id], f"makespan_{op_id}")
        objective = makespan

    model.setObjective(objective, GRB.MINIMIZE)

    for ws in context.warm_start:
        if ws.operation_id in start_vars:
            start_vars[ws.operation_id].Start = ws.start_minute

    model.optimize()

    status_map = {
        GRB.OPTIMAL: SolverStatus.OPTIMAL,
        GRB.SUBOPTIMAL: SolverStatus.FEASIBLE,
        GRB.INFEASIBLE: SolverStatus.INFEASIBLE,
        GRB.TIME_LIMIT: SolverStatus.TIMEOUT if model.SolCount == 0 else SolverStatus.FEASIBLE,
    }
    solver_status = status_map.get(model.Status, SolverStatus.UNKNOWN)

    assignments = []
    mo_tardiness = []

    if model.SolCount > 0:
        for op in context.operations:
            s_val = int(round(start_vars[op.id].X))
            e_val = int(round(end_vars[op.id].X))
            due = mo_due.get(op.mo_id, horizon)
            assignments.append(Assignment(
                operation_id=op.id,
                work_center_id=op.work_center_id,
                start_minute=s_val,
                end_minute=e_val,
                duration=op.duration_planned_mins,
                on_time=e_val <= due,
                mo_id=op.mo_id,
                sequence=op.sequence,
                bom_level=op.bom_level,
                parent_operation_id=op.parent_operation_id,
                operation_name=op.operation_name,
            ))

        for mo_id, t_var in tardiness_vars.items():
            t_val = max(0, int(round(t_var.X)))
            last_op = mo_groups[mo_id][-1]
            last_end = int(round(end_vars[last_op.id].X))
            mo_tardiness.append(MOTardiness(
                mo_id=mo_id,
                due_date_minute=mo_due.get(mo_id, horizon),
                completion_minute=last_end,
                tardiness_minutes=t_val,
                on_time=t_val == 0,
            ))

    return ScheduleResult(
        solver_status=solver_status,
        assignments=assignments,
        mo_tardiness=mo_tardiness,
        solve_time_ms=round((time.time() - start_time) * 1000, 2),
        total_operations=len(assignments),
    )


class GurobiSolver(ISolver):
    SUPPORTED_CONSTRAINTS = {
        ConstraintType.NO_OVERLAP,
        ConstraintType.PRECEDENCE,
        ConstraintType.BOM_PRECEDENCE,
        ConstraintType.FROZEN,
        ConstraintType.TARDINESS,
        ConstraintType.MAKESPAN,
    }

    def __init__(self, fallback_solver: ISolver | None = None):
        self._fallback = fallback_solver
        self._license_valid: bool | None = None

    def _ensure_license(self) -> bool:
        if self._license_valid is None:
            self._license_valid, _ = _check_gurobi_license()
            if not self._license_valid:
                logger.warning("Gurobi license not available; will use fallback solver")
        return self._license_valid

    def solve(
        self,
        context: SolverContext,
        constraints: list[Constraint] | None = None,
    ) -> ScheduleResult:
        if not _GUROBI_AVAILABLE or not self._ensure_license():
            if self._fallback:
                logger.info("Falling back to %s solver", self._fallback.name())
                return self._fallback.solve(context, constraints)
            return ScheduleResult(
                solver_status=SolverStatus.NOT_SOLVED,
                solve_time_ms=0,
            )

        try:
            result = _solve_with_gurobi(context)
            if result.solver_status in (SolverStatus.INFEASIBLE, SolverStatus.NOT_SOLVED, SolverStatus.MODEL_INVALID):
                if self._fallback:
                    logger.info("Gurobi returned %s; falling back to %s", result.solver_status, self._fallback.name())
                    return self._fallback.solve(context, constraints)
            return result
        except gp.GurobiError as e:
            logger.error("Gurobi error: %s", e)
            if self._fallback:
                logger.info("Falling back to %s solver", self._fallback.name())
                return self._fallback.solve(context, constraints)
            return ScheduleResult(
                solver_status=SolverStatus.NOT_SOLVED,
                solve_time_ms=0,
            )

    def name(self) -> str:
        return "gurobi"

    def supports_constraint(self, constraint_type: str) -> bool:
        try:
            return ConstraintType(constraint_type) in self.SUPPORTED_CONSTRAINTS
        except ValueError:
            return False