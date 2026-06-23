from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class SolverStatus(StrEnum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    NOT_SOLVED = "NOT_SOLVED"
    TIMEOUT = "TIMEOUT"
    SKILL_RELAXED = "SKILL_RELAXED"
    MODEL_INVALID = "MODEL_INVALID"
    UNKNOWN = "UNKNOWN"


class ConstraintType(StrEnum):
    NO_OVERLAP = "no_overlap"
    PRECEDENCE = "precedence"
    BOM_PRECEDENCE = "bom_precedence"
    FROZEN = "frozen"
    SKILL = "skill"
    WORKER_AVAILABILITY = "worker_availability"
    TARDINESS = "tardiness"
    MAKESPAN = "makespan"
    ENERGY_COST = "energy_cost"
    LABOR_COST = "labor_cost"
    CARBON = "carbon"
    MULTI_OBJECTIVE = "multi_objective"


@dataclass
class WorkCenterInput:
    id: str
    name: str = ""
    capacity_per_hour: float = 1.0
    energy_kwh_per_hour: float = 0.0
    cost_per_hour: float = 0.0
    overtime_cost_multiplier: float = 1.5
    energy_source: str = "grid"


@dataclass
class OperationInput:
    id: str
    mo_id: str = ""
    sequence: int = 0
    work_center_id: str = ""
    duration_planned_mins: int = 60
    priority_score: float = 0.5
    due_date_minutes: int | None = None
    bom_level: int = 0
    parent_operation_id: str | None = None
    is_phantom: bool = False
    transfer_time_mins: int = 0
    required_skill_id: str | None = None
    required_skill_tags: list[str] = field(default_factory=list)
    requires_operator: bool = True
    operation_name: str = ""
    material_score: float = 1.0


@dataclass
class WorkerInput:
    id: str
    skill_ids: list[str] = field(default_factory=list)
    skill_tags: list[str] = field(default_factory=list)
    shift_rules: list[dict] = field(default_factory=list)
    cost_per_hour: float = 0.0
    overtime_eligible: bool = False


@dataclass
class FrozenOp:
    operation_id: str
    fixed_start: int
    fixed_end: int


@dataclass
class WarmStart:
    operation_id: str
    start_minute: int


@dataclass
class Constraint:
    type: ConstraintType | str
    parameters: dict = field(default_factory=dict)


@dataclass
class GreenScheduleConfig:
    emission_factors: list[dict] = field(default_factory=list)
    material_carbons: list[dict] = field(default_factory=list)
    transport_emissions: list[dict] = field(default_factory=list)
    beta: float = 0.3


@dataclass
class SolverConfig:
    alpha: float = 0.5
    tariffs: list[dict] = field(default_factory=list)
    green: GreenScheduleConfig | None = None
    solver_timeout_seconds: int = 30
    max_bom_depth: int = 5
    enforce_skills: bool = True


@dataclass
class SolverContext:
    work_centers: list[WorkCenterInput]
    operations: list[OperationInput]
    workers: list[WorkerInput] = field(default_factory=list)
    horizon: int = 168
    frozen_ops: list[FrozenOp] = field(default_factory=list)
    warm_start: list[WarmStart] = field(default_factory=list)
    config: SolverConfig = field(default_factory=SolverConfig)
    tenant_id: str | None = None
    mos: list[dict] = field(default_factory=list)
    operators: list[dict] = field(default_factory=list)
    shifts: list[dict] = field(default_factory=list)
    horizon_hours: int = 0
    alpha: float = 0.5
    beta: float = 0.3

    def __post_init__(self) -> None:
        if self.horizon_hours and not self.horizon:
            self.horizon = self.horizon_hours * 60
        elif self.horizon and not self.horizon_hours:
            self.horizon_hours = self.horizon // 60
        if self.alpha != self.config.alpha and self.alpha != 0.5:
            self.config.alpha = self.alpha
        if self.beta != 0.3 and self.config.green:
            self.config.green.beta = self.beta


@dataclass
class Assignment:
    operation_id: str
    work_center_id: str
    start_minute: int
    end_minute: int
    duration: int
    on_time: bool = True
    mo_id: str = ""
    sequence: int = 0
    bom_level: int = 0
    parent_operation_id: str | None = None
    operation_name: str = ""
    worker_id: str | None = None


@dataclass
class MOTardiness:
    mo_id: str
    due_date_minute: int
    completion_minute: int
    tardiness_minutes: int
    on_time: bool


@dataclass
class ScheduleResult:
    solver_status: SolverStatus
    assignments: list[Assignment] = field(default_factory=list)
    mo_tardiness: list[MOTardiness] = field(default_factory=list)
    skill_relaxed: bool = False
    solve_time_ms: float = 0.0
    total_operations: int = 0
    cost_summary: dict | None = None
    cost_breakdown: list[dict] | None = None
    carbon_breakdown: dict | None = None
    carbon_per_unit: float = 0.0
    total_carbon_kg: float = 0.0
    total_make_cost: float = 0.0
    requires_manual_skill_verification: bool = False


SolverResult = ScheduleResult


class ISolver(ABC):
    @abstractmethod
    def solve(
        self,
        context: SolverContext,
        constraints: list[Constraint] | None = None,
    ) -> ScheduleResult:
        ...

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def supports_constraint(self, constraint_type: str) -> bool:
        ...
