"""OR-Tools CP-SAT solver implementing the ISolver interface.

Delegates to the existing scheduler modules for backward compatibility
while providing a clean ISolver contract for the factory pattern.
"""
from __future__ import annotations

import logging
import time

from ipe_shared.solver.interface import (
    Assignment,
    Constraint,
    ConstraintType,
    GreenScheduleConfig,
    ISolver,
    MOTardiness,
    ScheduleResult,
    SolverConfig,
    SolverContext,
    SolverStatus,
)

logger = logging.getLogger(__name__)


class ORToolsSolver(ISolver):
    SUPPORTED_CONSTRAINTS = {
        ConstraintType.NO_OVERLAP,
        ConstraintType.PRECEDENCE,
        ConstraintType.BOM_PRECEDENCE,
        ConstraintType.FROZEN,
        ConstraintType.SKILL,
        ConstraintType.WORKER_AVAILABILITY,
        ConstraintType.TARDINESS,
        ConstraintType.MAKESPAN,
        ConstraintType.ENERGY_COST,
        ConstraintType.LABOR_COST,
        ConstraintType.CARBON,
        ConstraintType.MULTI_OBJECTIVE,
    }

    def solve(
        self,
        context: SolverContext,
        constraints: list[Constraint] | None = None,
    ) -> ScheduleResult:
        from app.core.scheduler import solve_schedule
        from app.core.scheduler_cost import solve_cost_optimized
        from app.core.scheduler_green import (
            EmissionFactorData,
            MaterialCarbonData,
            TransportEmissionData,
            solve_green_schedule,
        )

        start_time = time.time()

        constraint_map = self._build_constraint_map(constraints or [])

        wc_dicts = [
            {
                "id": wc.id,
                "name": wc.name,
                "capacity_per_hour": wc.capacity_per_hour,
                "energy_kwh_per_hour": wc.energy_kwh_per_hour,
                "cost_per_hour": wc.cost_per_hour,
                "overtime_cost_multiplier": wc.overtime_cost_multiplier,
                "energy_source": wc.energy_source,
            }
            for wc in context.work_centers
        ]
        op_dicts = [
            {
                "id": op.id,
                "mo_id": op.mo_id,
                "sequence": op.sequence,
                "work_center_id": op.work_center_id,
                "duration_planned_mins": op.duration_planned_mins,
                "priority_score": op.priority_score,
                "due_date_minutes": op.due_date_minutes,
                "bom_level": op.bom_level,
                "parent_operation_id": op.parent_operation_id,
                "is_phantom": op.is_phantom,
                "transfer_time_mins": op.transfer_time_mins,
                "required_skill_id": op.required_skill_id,
                "required_skill_tags": op.required_skill_tags,
                "requires_operator": op.requires_operator,
                "operation_name": op.operation_name,
                "material_score": op.material_score,
            }
            for op in context.operations
        ]
        worker_dicts = [
            {
                "id": w.id,
                "skill_ids": w.skill_ids,
                "skill_tags": w.skill_tags,
                "shift_rules": w.shift_rules,
                "cost_per_hour": w.cost_per_hour,
                "overtime_eligible": w.overtime_eligible,
            }
            for w in context.workers
        ]
        frozen_dicts = [
            {"operation_id": f.operation_id, "fixed_start": f.fixed_start, "fixed_end": f.fixed_end}
            for f in context.frozen_ops
        ]
        warm_start_dict = {ws.operation_id: ws.start_minute for ws in context.warm_start}

        enforce_skills = constraint_map.get("enforce_skills", context.config.enforce_skills)

        config = context.config
        has_green = config.green is not None or ConstraintType.CARBON in constraint_map
        has_tariffs = bool(config.tariffs) or ConstraintType.ENERGY_COST in constraint_map

        if has_green:
            emission_factors = [
                EmissionFactorData(
                    energy_source=ef.get("energy_source", "grid"),
                    region=ef.get("region", ""),
                    factor_kg_co2_per_kwh=ef.get("factor_kg_co2_per_kwh", 0.5),
                )
                for ef in config.green.emission_factors
            ] if config.green and config.green.emission_factors else []
            material_carbons = [
                MaterialCarbonData(
                    product_id=mc.get("product_id", ""),
                    kg_co2_per_unit=mc.get("kg_co2_per_unit", 0.0),
                )
                for mc in config.green.material_carbons
            ] if config.green and config.green.material_carbons else []
            transport_emissions = [
                TransportEmissionData(
                    route_id=te.get("route_id", ""),
                    vehicle_type=te.get("vehicle_type", "truck"),
                    kg_co2_per_unit_per_km=te.get("kg_co2_per_unit_per_km", 0.0001),
                )
                for te in config.green.transport_emissions
            ] if config.green and config.green.transport_emissions else []

            beta = config.green.beta if config.green else constraint_map.get("beta", 0.3)
            result = solve_green_schedule(
                work_centers=wc_dicts,
                operations=op_dicts,
                emission_factors=emission_factors,
                material_carbons=material_carbons,
                transport_emissions=transport_emissions,
                horizon_mins=context.horizon,
                alpha=config.alpha,
                beta=beta,
                solver_timeout_seconds=config.solver_timeout_seconds,
            )
            return _green_result_to_schedule_result(result, start_time)

        elif has_tariffs:
            tariffs = config.tariffs or constraint_map.get("tariffs", [])
            raw = solve_cost_optimized(
                work_centers=wc_dicts,
                operations=op_dicts,
                horizon=context.horizon,
                solver_timeout_seconds=config.solver_timeout_seconds,
                frozen_ops=frozen_dicts,
                warm_start=warm_start_dict,
                max_bom_depth=config.max_bom_depth,
                workers=worker_dicts if worker_dicts else None,
                alpha=config.alpha,
                tariffs=tariffs,
            )
            return _raw_dict_to_schedule_result(raw, start_time)

        else:
            raw = solve_schedule(
                work_centers=wc_dicts,
                operations=op_dicts,
                horizon=context.horizon,
                solver_timeout_seconds=config.solver_timeout_seconds,
                frozen_ops=frozen_dicts,
                warm_start=warm_start_dict,
                max_bom_depth=config.max_bom_depth,
                workers=worker_dicts if worker_dicts and enforce_skills else None,
            )
            return _raw_dict_to_schedule_result(raw, start_time)

    @staticmethod
    def _build_constraint_map(constraints: list[Constraint]) -> dict:
        """Build a lookup map from constraints for dispatch."""
        result: dict = {}
        for c in constraints:
            ct = c.type if isinstance(c.type, ConstraintType) else ConstraintType(c.type) if c.type else None
            if ct is None:
                continue
            result[ct] = c.parameters
            if ct == ConstraintType.SKILL:
                result["enforce_skills"] = True
            elif ct == ConstraintType.ENERGY_COST:
                result["tariffs"] = c.parameters.get("tariffs", [])
            elif ct == ConstraintType.CARBON:
                result["beta"] = c.parameters.get("beta", 0.3)
            elif ct == ConstraintType.MULTI_OBJECTIVE:
                result["alpha"] = c.parameters.get("alpha", 0.5)
        return result

    def name(self) -> str:
        return "ortools"

    def supports_constraint(self, constraint_type: str) -> bool:
        try:
            return ConstraintType(constraint_type) in self.SUPPORTED_CONSTRAINTS
        except ValueError:
            return False


def _raw_dict_to_schedule_result(raw: dict, start_time: float, skill_relaxed: bool = False) -> ScheduleResult:
    status_str = raw.get("solver_status", raw.get("status", "UNKNOWN"))
    try:
        solver_status = SolverStatus(status_str)
    except ValueError:
        solver_status = SolverStatus.UNKNOWN

    if skill_relaxed or raw.get("skill_relaxed", False):
        if solver_status == SolverStatus.OPTIMAL or solver_status == SolverStatus.FEASIBLE:
            solver_status = SolverStatus.SKILL_RELAXED

    assignments = []
    for a in raw.get("assignments", []):
        assignments.append(Assignment(
            operation_id=a.get("operation_id", ""),
            work_center_id=a.get("work_center_id", ""),
            start_minute=a.get("start_minute", a.get("start_mins", 0)),
            end_minute=a.get("end_minute", a.get("end_mins", 0)),
            duration=a.get("duration", a.get("duration_mins", 0)),
            on_time=a.get("on_time", True),
            mo_id=a.get("mo_id", ""),
            sequence=a.get("sequence", 0),
            bom_level=a.get("bom_level", 0),
            parent_operation_id=a.get("parent_operation_id"),
            operation_name=a.get("operation_name", ""),
            worker_id=a.get("worker_id"),
        ))

    mo_tardiness = []
    for t in raw.get("mo_tardiness", []):
        mo_tardiness.append(MOTardiness(
            mo_id=t.get("mo_id", ""),
            due_date_minute=t.get("due_date_minute", t.get("due_date_minute", 0)),
            completion_minute=t.get("completion_minute", 0),
            tardiness_minutes=t.get("tardiness_minutes", 0),
            on_time=t.get("on_time", True),
        ))

    return ScheduleResult(
        solver_status=solver_status,
        assignments=assignments,
        mo_tardiness=mo_tardiness,
        skill_relaxed=skill_relaxed or raw.get("skill_relaxed", False),
        solve_time_ms=round((time.time() - start_time) * 1000, 2),
        total_operations=len(assignments),
        cost_summary=raw.get("cost_summary"),
        cost_breakdown=raw.get("cost_breakdown"),
        carbon_breakdown=raw.get("carbon_breakdown") if isinstance(raw.get("carbon_breakdown"), dict) else None,
        carbon_per_unit=raw.get("carbon_per_unit", 0.0),
        total_carbon_kg=raw.get("total_carbon_kg", 0.0),
        total_make_cost=raw.get("total_make_cost", 0.0),
        requires_manual_skill_verification=raw.get("requires_manual_skill_verification", False),
    )


def _green_result_to_schedule_result(result, start_time: float) -> ScheduleResult:
    if result.assignments is not None:
        assignments = []
        for a in result.assignments:
            assignments.append(Assignment(
                operation_id=a.get("operation_id", ""),
                work_center_id=a.get("work_center_id", ""),
                start_minute=a.get("start_mins", a.get("start_minute", 0)),
                end_minute=a.get("end_mins", a.get("end_minute", 0)),
                duration=a.get("duration_mins", a.get("duration", 0)),
                on_time=True,
                mo_id=a.get("mo_id", ""),
            ))

        carbon_breakdown = result.carbon_breakdown if isinstance(result.carbon_breakdown, dict) else {}
    else:
        assignments = []
        carbon_breakdown = {}

    try:
        solver_status = SolverStatus(result.solver_status)
    except ValueError:
        solver_status = SolverStatus.UNKNOWN

    return ScheduleResult(
        solver_status=solver_status,
        assignments=assignments,
        mo_tardiness=[],
        skill_relaxed=False,
        solve_time_ms=round((time.time() - start_time) * 1000, 2),
        total_operations=len(assignments),
        cost_summary=None,
        cost_breakdown=None,
        carbon_breakdown=carbon_breakdown,
        carbon_per_unit=result.carbon_per_unit,
        total_carbon_kg=result.total_carbon_kg,
        total_make_cost=result.total_make_cost,
    )