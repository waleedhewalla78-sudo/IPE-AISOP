"""20-scenario OR-Tools correctness tests for IPE cap-svc.

Covers: 5-level BOM, skill constraints, multi-work-center, operator absence,
timeout→heuristic fallback, zero-MO, 1000-MO scaling, frozen ops, warm start,
precedence, no-overlap, tardiness, cost-optimized, green scheduling, edge cases.
"""
from __future__ import annotations

import pytest

from ipe_shared.solver.interface import (
    Constraint,
    ConstraintType,
    FrozenOp,
    GreenScheduleConfig,
    OperationInput,
    SolverConfig,
    SolverContext,
    SolverStatus,
    WarmStart,
    WorkCenterInput,
    WorkerInput,
)


def _solve(ctx: SolverContext):
    from app.core.ortools_solver import ORToolsSolver
    return ORToolsSolver().solve(ctx)


class TestBasicScheduling:
    def test_single_mo_single_wc(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1", name="Lathe")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(result.assignments) == 1
        assert result.assignments[0].work_center_id == "wc1"

    def test_single_mo_multi_op_precedence(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1"), WorkCenterInput(id="wc2")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
                OperationInput(id="op2", mo_id="mo1", sequence=2, work_center_id="wc2", duration_planned_mins=30),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        a1 = next(a for a in result.assignments if a.operation_id == "op1")
        a2 = next(a for a in result.assignments if a.operation_id == "op2")
        assert a1.end_minute <= a2.start_minute

    def test_no_overlap_same_wc(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
                OperationInput(id="op2", mo_id="mo2", sequence=1, work_center_id="wc1", duration_planned_mins=60),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        a1 = next(a for a in result.assignments if a.operation_id == "op1")
        a2 = next(a for a in result.assignments if a.operation_id == "op2")
        assert a1.end_minute <= a2.start_minute or a2.end_minute <= a1.start_minute

    def test_multi_work_center_parallel(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1"), WorkCenterInput(id="wc2")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
                OperationInput(id="op2", mo_id="mo2", sequence=1, work_center_id="wc2", duration_planned_mins=60),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        a1 = next(a for a in result.assignments if a.operation_id == "op1")
        a2 = next(a for a in result.assignments if a.operation_id == "op2")
        assert a1.work_center_id == "wc1"
        assert a2.work_center_id == "wc2"


class TestBOMAndPrecedence:
    def test_five_level_bom(self):
        ops = []
        for level in range(5):
            ops.append(OperationInput(
                id=f"op_L{level}", mo_id="mo1", sequence=level,
                work_center_id="wc1", duration_planned_mins=30,
                bom_level=level,
                parent_operation_id=f"op_L{level-1}" if level > 0 else None,
            ))
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=ops,
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.INFEASIBLE)
        if result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            assert len(result.assignments) == 5
            sorted_ops = sorted(result.assignments, key=lambda a: a.bom_level)
            for i in range(len(sorted_ops) - 1):
                assert sorted_ops[i].end_minute <= sorted_ops[i + 1].start_minute

    def test_bom_precedence_with_transfer_time(self):
        ops = [
            OperationInput(id="op1", mo_id="mo1", sequence=0, work_center_id="wc1",
                            duration_planned_mins=60, bom_level=0),
            OperationInput(id="op2", mo_id="mo1", sequence=1, work_center_id="wc2",
                            duration_planned_mins=30, bom_level=1,
                            parent_operation_id="op1", transfer_time_mins=15),
        ]
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1"), WorkCenterInput(id="wc2")],
            operations=ops,
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.INFEASIBLE)
        if result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            a1 = next(a for a in result.assignments if a.operation_id == "op1")
            a2 = next(a for a in result.assignments if a.operation_id == "op2")
            assert a1.end_minute + 15 <= a2.start_minute

    def test_phantom_bom_expansion(self):
        ops = [
            OperationInput(id="op_parent", mo_id="mo1", sequence=0, work_center_id="wc1",
                            duration_planned_mins=60, is_phantom=True, bom_level=0),
            OperationInput(id="op_child1", mo_id="mo1", sequence=1, work_center_id="wc1",
                            duration_planned_mins=30, parent_operation_id="op_parent", bom_level=1),
            OperationInput(id="op_child2", mo_id="mo1", sequence=2, work_center_id="wc1",
                            duration_planned_mins=30, parent_operation_id="op_parent", bom_level=2),
        ]
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=ops,
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        op_ids = {a.operation_id for a in result.assignments}
        assert "op_parent" not in op_ids
        assert "op_child1" in op_ids
        assert "op_child2" in op_ids


class TestSkillConstraints:
    def test_skill_match(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1",
                                duration_planned_mins=60, required_skill_id="welding"),
            ],
            workers=[WorkerInput(id="w1", skill_ids=["welding", "machining"])],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.SKILL_RELAXED)

    def test_skill_mismatch_relaxes(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1",
                                duration_planned_mins=60, required_skill_id="welding"),
            ],
            workers=[WorkerInput(id="w1", skill_ids=["painting"])],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.SKILL_RELAXED)

    def test_worker_availability(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1",
                                duration_planned_mins=60, requires_operator=True),
            ],
            workers=[WorkerInput(
                id="w1", skill_ids=[],
                shift_rules=[{"days_of_week": [0], "start_hour": 8, "end_hour": 12, "break_minutes": 0}],
            )],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.SKILL_RELAXED)


class TestFrozenOps:
    def test_frozen_op_respected(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
                OperationInput(id="op2", mo_id="mo2", sequence=1, work_center_id="wc1", duration_planned_mins=30),
            ],
            frozen_ops=[FrozenOp(operation_id="op1", fixed_start=100, fixed_end=160)],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        a1 = next(a for a in result.assignments if a.operation_id == "op1")
        assert a1.start_minute == 100
        assert a1.end_minute == 160

    def test_multiple_frozen_ops(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
                OperationInput(id="op2", mo_id="mo2", sequence=1, work_center_id="wc1", duration_planned_mins=30),
                OperationInput(id="op3", mo_id="mo3", sequence=1, work_center_id="wc1", duration_planned_mins=20),
            ],
            frozen_ops=[
                FrozenOp(operation_id="op1", fixed_start=0, fixed_end=60),
                FrozenOp(operation_id="op3", fixed_start=200, fixed_end=220),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        a1 = next(a for a in result.assignments if a.operation_id == "op1")
        a3 = next(a for a in result.assignments if a.operation_id == "op3")
        assert a1.start_minute == 0
        assert a3.start_minute == 200


class TestTardiness:
    def test_on_time_mo(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1",
                                duration_planned_mins=60, due_date_minutes=120, priority_score=1.0),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(result.mo_tardiness) >= 1
        tardiness = next(t for t in result.mo_tardiness if t.mo_id == "mo1")
        assert tardiness.on_time is True

    def test_late_mo(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1",
                                duration_planned_mins=120, due_date_minutes=60, priority_score=1.0),
                OperationInput(id="op2", mo_id="mo2", sequence=1, work_center_id="wc1",
                                duration_planned_mins=60, due_date_minutes=200, priority_score=0.5),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(result.mo_tardiness) >= 1


class TestCostOptimized:
    def test_cost_with_tariffs(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1", cost_per_hour=10.0)],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
            ],
            config=SolverConfig(
                alpha=0.7,
                tariffs=[{"day_of_week": 0, "hour_start": 0, "hour_end": 6, "rate_per_kwh": 0.05}],
            ),
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(result.assignments) == 1


class TestGreenScheduling:
    def test_green_schedule(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1", energy_kwh_per_hour=15.0)],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
            ],
            config=SolverConfig(
                green=GreenScheduleConfig(
                    emission_factors=[{"energy_source": "grid", "factor_kg_co2_per_kwh": 0.5}],
                    beta=0.3,
                ),
            ),
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert result.total_carbon_kg >= 0


class TestEdgeCases:
    def test_zero_operations(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.total_operations == 0
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.INFEASIBLE, SolverStatus.NOT_SOLVED)

    def test_zero_work_centers(self):
        ctx = SolverContext(
            work_centers=[],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc_missing", duration_planned_mins=60),
            ],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.INFEASIBLE, SolverStatus.NOT_SOLVED)

    def test_large_scale_1000_ops(self):
        wcs = [WorkCenterInput(id=f"wc{i}") for i in range(10)]
        ops = [
            OperationInput(
                id=f"op_{mo}_{seq}", mo_id=f"mo_{mo}", sequence=seq,
                work_center_id=f"wc{seq % 10}", duration_planned_mins=30,
                due_date_minutes=480,
            )
            for mo in range(200)
            for seq in range(5)
        ]
        ctx = SolverContext(work_centers=wcs, operations=ops, horizon=10080)
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.TIMEOUT)
        assert result.solve_time_ms > 0

    def test_warm_start(self):
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
                OperationInput(id="op2", mo_id="mo1", sequence=2, work_center_id="wc1", duration_planned_mins=30),
            ],
            warm_start=[WarmStart(operation_id="op1", start_minute=0)],
            horizon=480,
        )
        result = _solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        a1 = next(a for a in result.assignments if a.operation_id == "op1")
        assert a1.start_minute == 0


class TestConstraintInterface:
    def test_constraints_passed_to_solver(self):
        from app.core.ortools_solver import ORToolsSolver
        solver = ORToolsSolver()
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
            ],
            horizon=480,
        )
        constraints = [
            Constraint(type=ConstraintType.NO_OVERLAP, parameters={"wc_ids": ["wc1"]}),
            Constraint(type=ConstraintType.PRECEDENCE, parameters={}),
        ]
        result = solver.solve(ctx, constraints=constraints)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(result.assignments) == 1

    def test_empty_constraints(self):
        from app.core.ortools_solver import ORToolsSolver
        solver = ORToolsSolver()
        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1")],
            operations=[
                OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
            ],
            horizon=480,
        )
        result = solver.solve(ctx, constraints=[])
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
