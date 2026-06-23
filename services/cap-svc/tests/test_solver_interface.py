"""Tests for the ISolver interface, SolverFactory, and data types."""
import pytest

from ipe_shared.solver.interface import (
    Assignment,
    Constraint,
    ConstraintType,
    FrozenOp,
    GreenScheduleConfig,
    ISolver,
    MOTardiness,
    OperationInput,
    ScheduleResult,
    SolverConfig,
    SolverContext,
    SolverStatus,
    WarmStart,
    WorkCenterInput,
    WorkerInput,
)
from ipe_shared.solver.factory import SolverFactory, _SOLVER_REGISTRY, register_solver, unregister_solver


def _make_simple_context():
    wcs = [WorkCenterInput(id="wc1", name="Lathe")]
    ops = [
        OperationInput(id="op1", mo_id="mo1", sequence=1, work_center_id="wc1", duration_planned_mins=60),
        OperationInput(id="op2", mo_id="mo1", sequence=2, work_center_id="wc1", duration_planned_mins=30, due_date_minutes=120),
    ]
    return SolverContext(work_centers=wcs, operations=ops, horizon=10080)


class TestInterfaceDataTypes:
    def test_solver_status_enum(self):
        assert SolverStatus.OPTIMAL == "OPTIMAL"
        assert SolverStatus.FEASIBLE == "FEASIBLE"
        assert SolverStatus.INFEASIBLE == "INFEASIBLE"
        assert SolverStatus.NOT_SOLVED == "NOT_SOLVED"
        assert SolverStatus.TIMEOUT == "TIMEOUT"
        assert SolverStatus.SKILL_RELAXED == "SKILL_RELAXED"

    def test_constraint_type_enum(self):
        assert ConstraintType.NO_OVERLAP == "no_overlap"
        assert ConstraintType.PRECEDENCE == "precedence"
        assert ConstraintType.BOM_PRECEDENCE == "bom_precedence"
        assert ConstraintType.FROZEN == "frozen"
        assert ConstraintType.SKILL == "skill"
        assert ConstraintType.ENERGY_COST == "energy_cost"
        assert ConstraintType.CARBON == "carbon"

    def test_work_center_input(self):
        wc = WorkCenterInput(id="wc1", name="Lathe", energy_kwh_per_hour=15.0)
        assert wc.id == "wc1"
        assert wc.name == "Lathe"
        assert wc.energy_kwh_per_hour == 15.0
        assert wc.capacity_per_hour == 1.0

    def test_operation_input_defaults(self):
        op = OperationInput(id="op1")
        assert op.duration_planned_mins == 60
        assert op.priority_score == 0.5
        assert op.is_phantom is False
        assert op.requires_operator is True
        assert op.transfer_time_mins == 0
        assert op.material_score == 1.0

    def test_worker_input(self):
        w = WorkerInput(id="w1", skill_ids=["welding"], skill_tags=["heavy"])
        assert w.id == "w1"
        assert w.skill_ids == ["welding"]
        assert w.skill_tags == ["heavy"]
        assert w.shift_rules == []

    def test_frozen_op(self):
        f = FrozenOp(operation_id="op1", fixed_start=100, fixed_end=160)
        assert f.operation_id == "op1"
        assert f.fixed_start == 100
        assert f.fixed_end == 160

    def test_warm_start(self):
        ws = WarmStart(operation_id="op1", start_minute=0)
        assert ws.operation_id == "op1"
        assert ws.start_minute == 0

    def test_constraint(self):
        c = Constraint(type=ConstraintType.NO_OVERLAP, parameters={"wc_ids": ["wc1"]})
        assert c.type == ConstraintType.NO_OVERLAP
        assert c.parameters == {"wc_ids": ["wc1"]}

    def test_green_schedule_config(self):
        green = GreenScheduleConfig(beta=0.4)
        assert green.beta == 0.4
        assert green.emission_factors == []
        assert green.material_carbons == []
        assert green.transport_emissions == []

    def test_solver_config_defaults(self):
        config = SolverConfig()
        assert config.alpha == 0.5
        assert config.solver_timeout_seconds == 30
        assert config.max_bom_depth == 5
        assert config.enforce_skills is True
        assert config.tariffs == []
        assert config.green is None

    def test_solver_context_defaults(self):
        ctx = SolverContext(work_centers=[], operations=[])
        assert ctx.horizon == 168
        assert ctx.workers == []
        assert ctx.frozen_ops == []
        assert ctx.warm_start == []
        assert ctx.config.alpha == 0.5
        assert ctx.tenant_id is None

    def test_schedule_result_defaults(self):
        r = ScheduleResult(solver_status=SolverStatus.OPTIMAL)
        assert r.assignments == []
        assert r.mo_tardiness == []
        assert r.cost_summary is None
        assert r.carbon_breakdown is None
        assert r.skill_relaxed is False
        assert r.solve_time_ms == 0.0
        assert r.total_operations == 0

    def test_assignment(self):
        a = Assignment(
            operation_id="op1", work_center_id="wc1",
            start_minute=0, end_minute=60, duration=60,
        )
        assert a.operation_id == "op1"
        assert a.on_time is True
        assert a.worker_id is None

    def test_mo_tardiness(self):
        t = MOTardiness(
            mo_id="mo1", due_date_minute=120, completion_minute=90,
            tardiness_minutes=0, on_time=True,
        )
        assert t.mo_id == "mo1"
        assert t.tardiness_minutes == 0
        assert t.on_time is True

    def test_isolver_is_abstract(self):
        with pytest.raises(TypeError):
            ISolver()


class TestSolverFactory:
    def test_register_and_unregister(self):
        class MockSolver(ISolver):
            def solve(self, context, constraints=None):
                return ScheduleResult(solver_status=SolverStatus.OPTIMAL)
            def name(self):
                return "mock"
            def supports_constraint(self, ct):
                return True

        register_solver("mock", MockSolver)
        assert "mock" in SolverFactory.available_solvers()

        factory = SolverFactory()
        solver = factory.create_solver("mock")
        assert solver.name() == "mock"

        unregister_solver("mock")
        assert "mock" not in SolverFactory.available_solvers()

    def test_unknown_solver_raises(self):
        factory = SolverFactory()
        with pytest.raises(ValueError, match="Unknown solver"):
            factory.create_solver("nonexistent_solver_xyz")

    def test_singleton_factory(self):
        f1 = SolverFactory.get_instance()
        f2 = SolverFactory.get_instance()
        assert f1 is f2

    def test_available_solvers_after_registration(self):
        from app.core.ortools_solver import ORToolsSolver
        register_solver("ortools", ORToolsSolver)
        assert "ortools" in SolverFactory.available_solvers()
        unregister_solver("ortools")

    def test_default_solver_after_registration(self):
        from app.core.ortools_solver import ORToolsSolver
        register_solver("ortools", ORToolsSolver)
        factory = SolverFactory()
        solver = factory.get_solver()
        assert solver.name() == "ortools"
        unregister_solver("ortools")


class TestORToolsSolver:
    def test_basic_schedule(self):
        from app.core.ortools_solver import ORToolsSolver

        solver = ORToolsSolver()
        result = solver.solve(_make_simple_context())
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(result.assignments) == 2
        assert result.total_operations == 2
        assert result.solve_time_ms > 0

    def test_no_overlap(self):
        from app.core.ortools_solver import ORToolsSolver

        solver = ORToolsSolver()
        result = solver.solve(_make_simple_context())
        if result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            a1 = next(a for a in result.assignments if a.operation_id == "op1")
            a2 = next(a for a in result.assignments if a.operation_id == "op2")
            assert a1.end_minute <= a2.start_minute or a2.end_minute <= a1.start_minute

    def test_precedence_within_mo(self):
        from app.core.ortools_solver import ORToolsSolver

        solver = ORToolsSolver()
        result = solver.solve(_make_simple_context())
        if result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            a1 = next(a for a in result.assignments if a.operation_id == "op1")
            a2 = next(a for a in result.assignments if a.operation_id == "op2")
            assert a1.end_minute <= a2.start_minute

    def test_frozen_ops(self):
        from app.core.ortools_solver import ORToolsSolver
        from ipe_shared.solver.interface import FrozenOp

        ctx = _make_simple_context()
        ctx.frozen_ops = [FrozenOp(operation_id="op1", fixed_start=0, fixed_end=60)]
        solver = ORToolsSolver()
        result = solver.solve(ctx)
        if result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            a1 = next(a for a in result.assignments if a.operation_id == "op1")
            assert a1.start_minute == 0
            assert a1.end_minute == 60

    def test_worker_constraints(self):
        from app.core.ortools_solver import ORToolsSolver

        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1", name="Lathe")],
            operations=[
                OperationInput(
                    id="op1", mo_id="mo1", sequence=1, work_center_id="wc1",
                    duration_planned_mins=60, required_skill_id="welding",
                    requires_operator=True,
                ),
                OperationInput(
                    id="op2", mo_id="mo2", sequence=1, work_center_id="wc1",
                    duration_planned_mins=30, due_date_minutes=120,
                ),
            ],
            workers=[
                WorkerInput(
                    id="w1", skill_ids=["welding", "machining"], skill_tags=["heavy-equipment"],
                    shift_rules=[{"days_of_week": [0, 1, 2, 3, 4], "start_hour": 8, "end_hour": 16, "break_minutes": 30}],
                ),
            ],
            horizon=10080,
        )
        solver = ORToolsSolver()
        result = solver.solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.SKILL_RELAXED)
        assert len(result.assignments) >= 1

    def test_name(self):
        from app.core.ortools_solver import ORToolsSolver

        solver = ORToolsSolver()
        assert solver.name() == "ortools"

    def test_supports_constraint(self):
        from app.core.ortools_solver import ORToolsSolver

        solver = ORToolsSolver()
        assert solver.supports_constraint("no_overlap") is True
        assert solver.supports_constraint("precedence") is True
        assert solver.supports_constraint("carbon") is True
        assert solver.supports_constraint("energy_cost") is True
        assert solver.supports_constraint("unknown_constraint") is False

    def test_empty_operations(self):
        from app.core.ortools_solver import ORToolsSolver

        ctx = SolverContext(
            work_centers=[WorkCenterInput(id="wc1", name="Lathe")],
            operations=[],
            horizon=10080,
        )
        solver = ORToolsSolver()
        result = solver.solve(ctx)
        assert result.total_operations == 0


class TestGurobiSolverFallback:
    def test_fallback_to_ortools(self):
        from app.core.gurobi_solver import GurobiSolver
        from app.core.ortools_solver import ORToolsSolver

        ortools = ORToolsSolver()
        gurobi = GurobiSolver(fallback_solver=ortools)
        gurobi._license_valid = False

        result = gurobi.solve(_make_simple_context())
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert result.total_operations == 2

    def test_name(self):
        from app.core.gurobi_solver import GurobiSolver

        solver = GurobiSolver()
        assert solver.name() == "gurobi"

    def test_supports_constraint(self):
        from app.core.gurobi_solver import GurobiSolver

        solver = GurobiSolver()
        assert solver.supports_constraint("no_overlap") is True
        assert solver.supports_constraint("precedence") is True
        assert solver.supports_constraint("skill") is False
        assert solver.supports_constraint("energy_cost") is False

    def test_not_solved_without_fallback(self):
        from app.core.gurobi_solver import GurobiSolver

        solver = GurobiSolver()
        solver._license_valid = False
        result = solver.solve(_make_simple_context())
        assert result.solver_status == SolverStatus.NOT_SOLVED
        assert result.total_operations == 0


class TestSolverFactoryIntegration:
    def setup_method(self):
        from app.core.ortools_solver import ORToolsSolver
        from app.core.gurobi_solver import GurobiSolver
        register_solver("ortools", ORToolsSolver)
        register_solver("gurobi", GurobiSolver)

    def test_create_ortools_via_factory(self):
        factory = SolverFactory()
        solver = factory.create_solver("ortools")
        assert solver.name() == "ortools"

        ctx = _make_simple_context()
        result = solver.solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert result.total_operations == 2

    def test_create_gurobi_with_fallback_via_factory(self):
        factory = SolverFactory()
        solver = factory.create_solver("gurobi")
        assert solver.name() == "gurobi"

    def test_solver_context_with_cost(self):
        from app.core.ortools_solver import ORToolsSolver

        ctx = _make_simple_context()
        ctx.config.tariffs = [
            {"day_of_week": 0, "hour_start": 0, "hour_end": 6, "rate_per_kwh": 0.05},
            {"day_of_week": 0, "hour_start": 6, "hour_end": 18, "rate_per_kwh": 0.12},
            {"day_of_week": 0, "hour_start": 18, "hour_end": 24, "rate_per_kwh": 0.08},
        ]
        ctx.config.alpha = 0.7

        solver = ORToolsSolver()
        result = solver.solve(ctx)
        if result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            assert result.cost_summary is not None or result.total_operations > 0

    def test_solver_context_with_green(self):
        from app.core.ortools_solver import ORToolsSolver

        ctx = _make_simple_context()
        ctx.config.green = GreenScheduleConfig(
            emission_factors=[{"energy_source": "grid", "region": "US", "factor_kg_co2_per_kwh": 0.5}],
            beta=0.3,
        )
        ctx.work_centers[0].energy_kwh_per_hour = 15.0

        solver = ORToolsSolver()
        result = solver.solve(ctx)
        assert result.solver_status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert result.total_carbon_kg >= 0