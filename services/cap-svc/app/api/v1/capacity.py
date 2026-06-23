import copy
from datetime import UTC, datetime
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.bottleneck import detect_bottlenecks
from app.core.priority_resolver import resolve_mo_priority
from app.core.schedule_persistence import (
    approve_schedule_mos,
    load_active_schedule,
    persist_schedule_proposal,
)
from app.core.scheduler import solve_schedule
from app.core.scheduler_cost import solve_cost_optimized
from app.core.network_optimizer import (
    PlantData, TransferRouteData, FleetData, NetworkDemand,
    solve_network_optimization,
)
from app.core.scheduler_green import (
    EmissionFactorData, MaterialCarbonData, TransportEmissionData,
    solve_green_schedule,
)
from app.core.solver_factory import register_cap_svc_solvers
from ipe_shared.audit.service import log_audit_event
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.bom import BillOfMaterial
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.operator import Operator
from ipe_shared.models.routing import RoutingOperation
from ipe_shared.models.worker import Worker
from ipe_shared.models.shift import Shift
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.models.plant import Plant
from ipe_shared.models.transfer_route import TransferRoute
from ipe_shared.models.transport_fleet import TransportFleet
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.carbon import EmissionFactor, MaterialCarbon, TransportEmission
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation
from ipe_shared.solver.interface import (
    Constraint,
    GreenScheduleConfig,
    OperationInput,
    SolverConfig,
    SolverContext,
    SolverStatus,
    WarmStart,
    WorkCenterInput,
    WorkerInput,
)
from ipe_shared.solver.factory import SolverFactory

try:
    register_cap_svc_solvers()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning("Failed to register cap-svc solvers: %s", e)

router = APIRouter(prefix="/capacity", tags=["capacity"])


class ScheduleRequest(BaseModel):
    mo_ids: list[UUID] | None = None
    horizon_hours: int = 168
    frozen_ops: list[dict] | None = None
    strategy: str = "hybrid"
    alpha: float = 0.5
    beta: float = 0.3
    capacity_buffer_pct: float = 0.0
    overtime_allowed: bool = True


class ScheduleApproveRequest(BaseModel):
    mo_ids: list[UUID]
    expected_versions: dict[str, float] | None = None
    approved_by: str = "planner"
    sync_odoo: bool = False


class CostOptimizedScheduleRequest(BaseModel):
    mo_ids: list[UUID] | None = None
    horizon_hours: int = 168
    frozen_ops: list[dict] | None = None
    alpha: float = 0.5
    tariffs: list[dict] | None = None


class HypotheticalChange(BaseModel):
    work_center_id: str | None = None
    capacity_multiplier: float | None = None
    supply_order_id: str | None = None
    delay_days: int | None = None
    mo_id: str | None = None
    mo_duration_shift_minutes: int | None = None


class SimulationRequest(BaseModel):
    operations: list[dict]
    work_centers: list[dict]
    horizon_hours: int = 168
    hypothetical_changes: list[HypotheticalChange] = []


@router.post("/schedule")
async def schedule_production(
    req: ScheduleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    try:
        async with httpx.AsyncClient(timeout=3.0) as mdr_client:
            mdr_resp = await mdr_client.get(
                f"{settings.DPE_SVC_URL}/api/v1/demand/mdr/dashboard",
                headers={"X-Tenant-ID": tenant_id},
            )
            if mdr_resp.status_code == 200:
                mdr_data = mdr_resp.json().get("data", {})
                if mdr_data and not mdr_data.get("ai_scheduling_allowed", True):
                    return APIResponse(
                        success=False,
                        data={"mdr": mdr_data},
                        error={
                            "code": "MDR_GATE_BLOCKED",
                            "message": "Master Data Readiness below 70%. Complete remediation before scheduling.",
                            "remediation": mdr_data.get("remediation", []),
                        },
                    )
    except Exception:
        pass

    tid = UUID(tenant_id)

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers = wc_result.scalars().all()

    mos_query = sa_select(ManufacturingOrder).where(ManufacturingOrder.tenant_id == tid)
    if req.mo_ids:
        mos_query = mos_query.where(ManufacturingOrder.id.in_(req.mo_ids))
    mo_result = await session.execute(mos_query)
    mos = mo_result.scalars().all()

    op_result = await session.execute(
        sa_select(Operator).where(Operator.tenant_id == tid)
    )
    operators = op_result.scalars().all()

    worker_result = await session.execute(
        sa_select(Worker).where(Worker.tenant_id == tid, Worker.is_active == True)
    )
    workers_db = worker_result.scalars().all()

    shift_result = await session.execute(
        sa_select(Shift).where(Shift.tenant_id == tid, Shift.is_active == True)
    )
    shifts_db = {str(s.id): s for s in shift_result.scalars().all()}

    default_shift = [{"days_of_week": [0,1,2,3,4], "start_hour": 8, "end_hour": 16, "break_minutes": 30}]

    workers = []
    for w in workers_db:
        skills = []
        if hasattr(w, 'skills') and w.skills:
            skills = [str(s.id) for s in w.skills]

        shift_rules = default_shift
        if w.shift_calendar_id and str(w.shift_calendar_id) in shifts_db:
            shift = shifts_db[str(w.shift_calendar_id)]
            shift_rules = [{
                "days_of_week": shift.days_of_week if shift.days_of_week else [0,1,2,3,4],
                "start_hour": shift.start_hour if shift.start_hour is not None else 8,
                "start_minute": shift.start_minute if shift.start_minute is not None else 0,
                "end_hour": shift.end_hour if shift.end_hour is not None else 16,
                "end_minute": shift.end_minute if shift.end_minute is not None else 0,
                "break_minutes": shift.break_minutes if shift.break_minutes is not None else 30,
            }]

        workers.append({
            "id": str(w.id),
            "name": w.name,
            "skill_ids": skills,
            "skill_tags": [],
            "shift_rules": shift_rules,
            "is_active": bool(w.is_active),
            "overtime_eligible": bool(w.overtime_eligible),
        })

    now = datetime.now(UTC)
    ops = []
    for mo in mos:
        bom_result = await session.execute(
            sa_select(BillOfMaterial).where(BillOfMaterial.tenant_id == tid, BillOfMaterial.id == mo.bom_id)
        )
        bom = bom_result.scalar_one_or_none()

        routing_result = await session.execute(
            sa_select(RoutingOperation).where(RoutingOperation.tenant_id == tid, RoutingOperation.bom_id == mo.bom_id)
        )
        for r in routing_result.scalars().all():
            due_date_minutes = None
            if mo.planned_end:
                delta = (mo.planned_end - now).total_seconds() / 60.0
                due_date_minutes = max(0, int(delta))
            priority = await resolve_mo_priority(session, tid, mo)
            material_score = float(mo.material_score or 1.0)

            duration = int(r.duration_planned_mins or 60) + int(r.setup_time_mins or 0)

            try:
                async with httpx.AsyncClient(timeout=2.0) as ml_client:
                    ml_resp = await ml_client.post(
                        f"{settings.ML_SVC_URL}/api/v1/predict/duration",
                        json={
                            "product_id": str(mo.product_id),
                            "work_center_id": str(r.work_center_id),
                            "batch_size": float(mo.quantity or 1),
                            "duration_planned_mins": duration,
                            "operator_skill_tags": [],
                        },
                    )
                    if ml_resp.status_code == 200:
                        ml_data = ml_resp.json().get("data", {})
                        if not ml_data.get("fallback_used", True):
                            duration = int(ml_data.get("predicted_duration_mins", duration))
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    "ML duration prediction failed for MO %s op %s: %s, using planned duration",
                    mo.id, r.id, e,
                )

            ops.append({
                "id": str(r.id),
                "mo_id": str(mo.id),
                "sequence": int(r.sequence),
                "work_center_id": str(r.work_center_id),
                "duration_planned_mins": duration,
                "operation_name": r.operation_name or f"Op {r.sequence}",
                "due_date_minutes": due_date_minutes,
                "priority_score": priority,
                "material_score": material_score,
                "parent_operation_id": str(r.parent_operation_id) if r.parent_operation_id else None,
                "bom_level": int(r.bom_level or 0) if r.bom_level is not None else int(bom.bom_level or 0) if bom else 0,
                "transfer_time_mins": int(r.transfer_time_mins or 0) if r.transfer_time_mins is not None else 0,
                "is_phantom": bool(bom.is_phantom) if bom else False,
                "required_skill_id": str(r.required_skill_id) if r.required_skill_id else None,
                "required_skill_tags": list(r.required_skill_tags) if r.required_skill_tags else [],
                "requires_operator": bool(r.requires_operator) if r.requires_operator is not None else True,
            })

    wc_list = [
        {
            "id": str(w.id),
            "name": w.name,
            "capacity_hours_per_day": float(w.capacity_hours_per_day or 8),
            "oee": float(w.oee or 0.85),
        }
        for w in work_centers
    ]

    horizon = req.horizon_hours * 60

    factory = SolverFactory.get_instance()
    solver = factory.create_solver("ortools")

    wc_inputs = [WorkCenterInput(
        id=str(w.id),
        name=w.name or "",
        capacity_per_hour=float(w.capacity_hours_per_day or 8) / 24.0,
    ) for w in work_centers]

    op_inputs = []
    for op in ops:
        op_inputs.append(OperationInput(
            id=op["id"],
            mo_id=op.get("mo_id", ""),
            sequence=op.get("sequence", 0),
            work_center_id=op.get("work_center_id", ""),
            duration_planned_mins=op.get("duration_planned_mins", 60),
            priority_score=op.get("priority_score", 0.5),
            due_date_minutes=op.get("due_date_minutes"),
            bom_level=op.get("bom_level", 0),
            parent_operation_id=op.get("parent_operation_id"),
            is_phantom=op.get("is_phantom", False),
            transfer_time_mins=op.get("transfer_time_mins", 0),
            required_skill_id=op.get("required_skill_id"),
            required_skill_tags=op.get("required_skill_tags", []),
            requires_operator=op.get("requires_operator", True),
            operation_name=op.get("operation_name", ""),
            material_score=op.get("material_score", 1.0),
        ))

    worker_inputs = []
    for w in workers:
        worker_inputs.append(WorkerInput(
            id=w.get("id", ""),
            skill_ids=w.get("skill_ids", []),
            skill_tags=w.get("skill_tags", []),
            shift_rules=w.get("shift_rules", []),
            cost_per_hour=w.get("cost_per_hour", 0.0),
            overtime_eligible=w.get("overtime_eligible", False),
        ))

    frozen_objs = None
    if req.frozen_ops:
        from ipe_shared.solver.interface import FrozenOp
        frozen_objs = [FrozenOp(
            operation_id=f.get("operation_id", ""),
            fixed_start=f.get("fixed_start", 0),
            fixed_end=f.get("fixed_end", 0),
        ) for f in req.frozen_ops]

    context = SolverContext(
        work_centers=wc_inputs,
        operations=op_inputs,
        workers=worker_inputs if worker_inputs else [],
        horizon=horizon,
        frozen_ops=frozen_objs or [],
        config=SolverConfig(
            solver_timeout_seconds=30,
            max_bom_depth=settings.MAX_BOM_DEPTH,
            enforce_skills=bool(workers),
        ),
        tenant_id=tenant_id,
    )

    result = solver.solve(context)
    schedule = {
        "status": result.solver_status.value,
        "assignments": [
            {
                "operation_id": a.operation_id,
                "work_center_id": a.work_center_id,
                "start_minute": a.start_minute,
                "end_minute": a.end_minute,
                "duration": a.duration,
                "on_time": a.on_time,
                "mo_id": a.mo_id,
                "sequence": a.sequence,
                "bom_level": a.bom_level,
                "parent_operation_id": a.parent_operation_id,
                "operation_name": a.operation_name,
                "worker_id": a.worker_id,
            }
            for a in result.assignments
        ],
        "mo_tardiness": [
            {
                "mo_id": t.mo_id,
                "due_date_minute": t.due_date_minute,
                "completion_minute": t.completion_minute,
                "tardiness_minutes": t.tardiness_minutes,
                "on_time": t.on_time,
            }
            for t in result.mo_tardiness
        ],
        "solver_status": result.solver_status.value,
        "skill_relaxed": result.skill_relaxed,
    }

    bottlenecks = detect_bottlenecks(schedule.get("assignments", []), wc_list, horizon)

    labor_gaps = []
    for op_entry in ops[:20]:
        wc_id = op_entry["work_center_id"]
        wc = next((w for w in work_centers if str(w.id) == wc_id), None)
        if wc:
            available_ops = [
                o for o in operators
                if not o.predicted_absence_probability or o.predicted_absence_probability < 0.5
            ]
            gap = len(available_ops) < 2
            labor_gaps.append({
                "work_center_id": wc_id,
                "work_center_name": wc.name,
                "required_count": 2,
                "available_count": len(available_ops),
                "has_gap": gap,
                "recommendation": "Assign additional operator" if gap else "Sufficient coverage",
            })

    # Publish capacity_scored for each MO
    for mo in mos:
        mo_bottlenecks = [
            b["work_center_id"] for b in bottlenecks
            if b.get("work_center_id", "") in [op["work_center_id"] for op in ops if op["mo_id"] == str(mo.id)]
        ]
        cap_score = 100.0 if schedule.get("solver_status") == "OPTIMAL" else (
            0.0 if schedule.get("solver_status") == "INFEASIBLE" else 50.0
        )
        envelope = kafka_producer.build_envelope(
            event_type="ipe.mo.capacity_scored",
            tenant_id=tid,
            payload={
                "mo_id": str(mo.id),
                "capacity_score": cap_score,
                "solver_status": schedule.get("solver_status", "UNKNOWN"),
                "bottlenecks": mo_bottlenecks,
            },
        )
        await kafka_producer.send_avro(
            topic="ipe.mo.capacity_scored",
            key=str(mo.id),
            envelope=envelope,
        )

    persist_stats = await persist_schedule_proposal(
        session,
        tid,
        schedule.get("assignments", []),
    )

    return APIResponse(success=True, data={
        "schedule": schedule,
        "bottlenecks": bottlenecks,
        "labor_gaps": labor_gaps[:5],
        "total_operations": len(ops),
        "persisted": persist_stats,
        "mo_versions": {str(mo.id): int(float(mo.version or 1)) for mo in mos},
        "xai_explanation": XAIExplanation(
            constraints=["no_overlap_per_work_center", "precedence_within_mo_groups"]
                         + ([f"bottleneck_{b['work_center_id']}" for b in bottlenecks[:3]] if bottlenecks else []),
            assumptions=["30s_solver_timeout", "oee_applied"]
                         + (["skill_relaxation_applied"] if schedule.get("skill_relaxed") else []),
            confidence_score=round(1.0 if schedule.get("solver_status") == "OPTIMAL" else (0.5 if schedule.get("solver_status") == "FEASIBLE" else 0.0), 4),
            contributing_factors={b["work_center_id"]: round(min(1.0, b.get("utilization_pct", 0) / 100.0), 4) for b in bottlenecks[:5]} if bottlenecks else {"solver": round(1.0 if schedule.get("solver_status") == "OPTIMAL" else 0.5, 4)},
        ).model_dump(),
    }, error=None)


@router.post("/cost-optimized")
async def schedule_cost_optimized(
    req: CostOptimizedScheduleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    """Multi-objective schedule: minimize tardiness + energy + labor costs.

    alpha parameter (0.1-0.9): 0.1=cost-priority, 0.9=speed-priority.
    """
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers = wc_result.scalars().all()

    mos_query = sa_select(ManufacturingOrder).where(ManufacturingOrder.tenant_id == tid)
    if req.mo_ids:
        mos_query = mos_query.where(ManufacturingOrder.id.in_(req.mo_ids))
    mo_result = await session.execute(mos_query)
    mos = mo_result.scalars().all()

    op_result = await session.execute(
        sa_select(Operator).where(Operator.tenant_id == tid)
    )
    operators = op_result.scalars().all()

    worker_result = await session.execute(
        sa_select(Worker).where(Worker.tenant_id == tid, Worker.is_active == True)
    )
    workers_db = worker_result.scalars().all()

    shift_result = await session.execute(
        sa_select(Shift).where(Shift.tenant_id == tid, Shift.is_active == True)
    )
    shifts_db = {str(s.id): s for s in shift_result.scalars().all()}

    default_shift = [{"days_of_week": [0,1,2,3,4], "start_hour": 8, "end_hour": 16, "break_minutes": 30}]

    workers = []
    for w in workers_db:
        skills = []
        if hasattr(w, 'skills') and w.skills:
            skills = [str(s.id) for s in w.skills]

        shift_rules = default_shift
        if w.shift_calendar_id and str(w.shift_calendar_id) in shifts_db:
            shift = shifts_db[str(w.shift_calendar_id)]
            shift_rules = [{
                "days_of_week": shift.days_of_week if shift.days_of_week else [0,1,2,3,4],
                "start_hour": shift.start_hour if shift.start_hour is not None else 8,
                "start_minute": shift.start_minute if shift.start_minute is not None else 0,
                "end_hour": shift.end_hour if shift.end_hour is not None else 16,
                "end_minute": shift.end_minute if shift.end_minute is not None else 0,
                "break_minutes": shift.break_minutes if shift.break_minutes is not None else 30,
            }]

        workers.append({
            "id": str(w.id),
            "name": w.name,
            "skill_ids": skills,
            "skill_tags": [],
            "shift_rules": shift_rules,
            "is_active": bool(w.is_active),
            "overtime_eligible": bool(w.overtime_eligible),
        })

    now = datetime.now(UTC)
    ops = []
    for mo in mos:
        bom_result = await session.execute(
            sa_select(BillOfMaterial).where(BillOfMaterial.tenant_id == tid, BillOfMaterial.id == mo.bom_id)
        )
        bom = bom_result.scalar_one_or_none()

        routing_result = await session.execute(
            sa_select(RoutingOperation).where(RoutingOperation.tenant_id == tid, RoutingOperation.bom_id == mo.bom_id)
        )
        for r in routing_result.scalars().all():
            due_date_minutes = None
            if mo.planned_end:
                delta = (mo.planned_end - now).total_seconds() / 60.0
                due_date_minutes = max(0, int(delta))
            priority = await resolve_mo_priority(session, tid, mo)
            material_score = float(mo.material_score or 1.0)

            duration = int(r.duration_planned_mins or 60) + int(r.setup_time_mins or 0)

            ops.append({
                "id": str(r.id),
                "mo_id": str(mo.id),
                "sequence": int(r.sequence),
                "work_center_id": str(r.work_center_id),
                "duration_planned_mins": duration,
                "operation_name": r.operation_name or f"Op {r.sequence}",
                "due_date_minutes": due_date_minutes,
                "priority_score": priority,
                "material_score": material_score,
                "parent_operation_id": str(r.parent_operation_id) if r.parent_operation_id else None,
                "bom_level": int(r.bom_level or 0) if r.bom_level is not None else int(bom.bom_level or 0) if bom else 0,
                "transfer_time_mins": int(r.transfer_time_mins or 0) if r.transfer_time_mins is not None else 0,
                "is_phantom": bool(bom.is_phantom) if bom else False,
                "required_skill_id": str(r.required_skill_id) if r.required_skill_id else None,
                "required_skill_tags": list(r.required_skill_tags) if r.required_skill_tags else [],
                "requires_operator": bool(r.requires_operator) if r.requires_operator is not None else True,
            })

    wc_list = [
        {
            "id": str(w.id),
            "name": w.name,
            "capacity_hours_per_day": float(w.capacity_hours_per_day or 8),
            "oee": float(w.oee or 0.85),
            "cost_per_hour": float(w.cost_per_hour) if w.cost_per_hour else 0.0,
            "energy_kwh_per_hour": float(w.energy_kwh_per_hour) if w.energy_kwh_per_hour else 0.0,
            "overtime_cost_multiplier": float(w.overtime_cost_multiplier) if w.overtime_cost_multiplier else 1.5,
        }
        for w in work_centers
    ]

    horizon = req.horizon_hours * 60
    alpha = max(0.1, min(0.9, req.alpha))

    schedule = solve_cost_optimized(
        wc_list, ops, horizon=horizon,
        frozen_ops=req.frozen_ops or [],
        max_bom_depth=settings.MAX_BOM_DEPTH,
        workers=workers if workers else None,
        alpha=alpha,
        tariffs=req.tariffs or [],
    )

    bottlenecks = detect_bottlenecks(schedule.get("assignments", []), wc_list, horizon)

    for mo in mos:
        cap_score = 100.0 if schedule.get("solver_status") == "OPTIMAL" else (
            0.0 if schedule.get("solver_status") == "INFEASIBLE" else 50.0
        )
        mo_bottlenecks = [
            b["work_center_id"] for b in bottlenecks
            if b.get("work_center_id", "") in [op["work_center_id"] for op in ops if op["mo_id"] == str(mo.id)]
        ]
        envelope = kafka_producer.build_envelope(
            event_type="ipe.mo.capacity_scored",
            tenant_id=tid,
            payload={
                "mo_id": str(mo.id),
                "capacity_score": cap_score,
                "solver_status": schedule.get("solver_status", "UNKNOWN"),
                "bottlenecks": mo_bottlenecks,
                "cost_summary": schedule.get("cost_summary", {}),
            },
        )
        await kafka_producer.send_avro(
            topic="ipe.mo.capacity_scored",
            key=str(mo.id),
            envelope=envelope,
        )

    await log_audit_event(
        tenant_id=tid,
        actor_type="user",
        actor_id=str(current_user.sub),
        action="COST_OPTIMIZE",
        entity_type="schedule",
        entity_id=tid,
        before_state={"mo_ids": [str(m.id) for m in mos]},
        after_state={
            "solver_status": schedule.get("solver_status"),
            "total_operations": len(ops),
            "cost_summary": schedule.get("cost_summary", {}),
        },
        rationale=f"alpha={alpha}, tariffs={len(req.tariffs or [])}",
    )

    return APIResponse(success=True, data={
        "schedule": schedule,
        "bottlenecks": bottlenecks,
        "total_operations": len(ops),
        "xai_explanation": XAIExplanation(
            constraints=["no_overlap", "precedence", f"alpha_{alpha}_tardiness_weight"]
                         + ([f"bottleneck_{b['work_center_id']}" for b in bottlenecks[:3]] if bottlenecks else []),
            assumptions=["30s_solver_timeout", "energy_cost_tariff_based", "overtime_multiplier_applied"],
            confidence_score=round(1.0 if schedule.get("solver_status") == "OPTIMAL" else (0.5 if schedule.get("solver_status") == "FEASIBLE" else 0.0), 4),
            contributing_factors={
                "tardiness_weight": round(alpha, 4),
                "cost_weight": round(1.0 - alpha, 4),
                **{b["work_center_id"]: round(min(1.0, b.get("utilization_pct", 0) / 100.0), 4) for b in bottlenecks[:3]},
            } if bottlenecks else {"tardiness_weight": round(alpha, 4), "cost_weight": round(1.0 - alpha, 4)},
        ).model_dump(),
    }, error=None)


@router.post("/analyze")
async def analyze_capacity(
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers = wc_result.scalars().all()

    op_result = await session.execute(
        sa_select(Operator).where(Operator.tenant_id == tid)
    )
    operators = op_result.scalars().all()

    wc_list = [
        {
            "id": str(w.id),
            "name": w.name,
            "capacity_hours_per_day": float(w.capacity_hours_per_day or 8),
            "status": w.status or "operational",
            "oee": float(w.oee or 0.85),
            "cost_per_hour": float(w.cost_per_hour) if w.cost_per_hour else None,
        }
        for w in work_centers
    ]

    op_list = [
        {
            "id": str(o.id),
            "name": o.name,
            "skill_tags": list(o.skill_tags) if o.skill_tags else [],
            "cost_per_hour": float(o.cost_per_hour) if o.cost_per_hour else None,
            "predicted_absence_probability": float(o.predicted_absence_probability) if o.predicted_absence_probability else None,
            "overtime_eligible": bool(o.overtime_eligible),
        }
        for o in operators
    ]

    return APIResponse(success=True, data={"work_centers": wc_list, "operators": op_list}, error=None)


@router.post("/simulate")
async def simulate_schedule(req: SimulationRequest):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    ops = copy.deepcopy(req.operations)
    wcs = copy.deepcopy(req.work_centers)
    horizon = req.horizon_hours * 60

    for change in req.hypothetical_changes:
        if change.work_center_id and change.capacity_multiplier is not None:
            for wc in wcs:
                if wc.get("id") == change.work_center_id:
                    base = float(wc.get("capacity_hours_per_day", 8))
                    wc["capacity_hours_per_day"] = base * change.capacity_multiplier
        if change.mo_id and change.mo_duration_shift_minutes is not None:
            for op in ops:
                if op.get("mo_id") == change.mo_id:
                    current = int(op.get("duration_planned_mins", 60))
                    op["duration_planned_mins"] = max(1, current + change.mo_duration_shift_minutes)
        if change.supply_order_id and change.delay_days is not None:
            for op in ops:
                if op.get("mo_id") == change.supply_order_id:
                    if op.get("due_date_minutes") is not None:
                        op["due_date_minutes"] = op["due_date_minutes"] + change.delay_days * 1440

    schedule = solve_schedule(wcs, ops, horizon=horizon)

    baseline_summary = {
        "total_operations": len(ops),
        "assignments": schedule.get("assignments", []),
        "solver_status": schedule.get("status", "UNKNOWN"),
    }

    return APIResponse(
        success=True,
        data={
            "simulation_result": schedule,
            "baseline_summary": baseline_summary,
            "changes_applied": [c.model_dump(exclude_none=True) for c in req.hypothetical_changes],
            "note": "This is a what-if simulation. No data was persisted.",
        },
        error=None,
    )


class NetworkOptimizeRequest(BaseModel):
    demand_ids: list[UUID] | None = None
    alpha: float = 0.5
    horizon_days: int = 14
    solver_timeout_seconds: int = 60


@router.post("/network-optimize")
async def network_optimize(
    req: NetworkOptimizeRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    """Multi-plant make-vs-transfer network optimization."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    plant_result = await session.execute(
        sa_select(Plant).where(Plant.tenant_id == tid, Plant.is_active == True)
    )
    plants_db = plant_result.scalars().all()

    route_result = await session.execute(
        sa_select(TransferRoute).where(TransferRoute.tenant_id == tid, TransferRoute.is_active == True)
    )
    routes_db = route_result.scalars().all()

    fleet_result = await session.execute(
        sa_select(TransportFleet).where(TransportFleet.tenant_id == tid, TransportFleet.is_active == True)
    )
    fleets_db = fleet_result.scalars().all()

    demand_query = sa_select(DemandLine).where(DemandLine.tenant_id == tid, DemandLine.status == "pending")
    if req.demand_ids:
        demand_query = demand_query.where(DemandLine.id.in_(req.demand_ids))
    demand_result = await session.execute(demand_query)
    demands_db = demand_result.scalars().all()

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers_db = wc_result.scalars().all()

    plants = [
        PlantData(
            plant_id=str(p.id),
            name=p.name,
            capacity_hours=float(p.capacity_hours_per_day or 8),
            cost_per_hour=float(p.cost_per_hour or 0),
            energy_kwh_per_hour=float(p.energy_kwh_per_hour or 0),
            capabilities=list(p.capabilities) if p.capabilities else [],
        )
        for p in plants_db
    ]

    routes = [
        TransferRouteData(
            route_id=str(r.id),
            origin_plant_id=str(r.origin_plant_id),
            destination_plant_id=str(r.destination_plant_id),
            transit_time_hours=float(r.transit_time_hours or 24),
            cost_per_unit=float(r.cost_per_unit or 0),
            capacity_units=int(r.capacity_units or 1000),
            reliability_score=float(r.reliability_score or 0.95),
        )
        for r in routes_db
    ]

    fleets = [
        FleetData(
            fleet_id=str(f.id),
            route_id=str(f.route_id),
            available_units=int(f.available_units or 1),
            max_trips_per_day=int(f.max_trips_per_day or 5),
            cost_per_trip=float(f.cost_per_trip or 0),
        )
        for f in fleets_db
    ]

    plant_ids = {str(p.id) for p in plants_db}
    demands = []
    for d in demands_db:
        capable = list(plant_ids)
        demands.append(NetworkDemand(
            demand_id=str(d.id),
            product_id=str(d.product_id),
            quantity=int(d.quantity or 1),
            required_date=str(d.required_date) if d.required_date else "",
            priority_score=float(d.priority_score or 0.5),
            penalty_cost=float(d.penalty_cost or 100),
            capable_plants=capable,
        ))

    wc_list = [
        {
            "id": str(w.id),
            "name": w.name,
            "plant_id": str(w.plant_id) if w.plant_id else None,
            "capacity_hours_per_day": float(w.capacity_hours_per_day or 8),
            "cost_per_hour": float(w.cost_per_hour or 0),
        }
        for w in work_centers_db
    ]

    alpha = max(0.1, min(0.9, req.alpha))

    result = solve_network_optimization(
        plants=plants,
        routes=routes,
        fleets=fleets,
        demands=demands,
        work_centers=wc_list,
        operations=[],
        alpha=alpha,
        horizon_days=req.horizon_days,
        solver_timeout_seconds=req.solver_timeout_seconds,
    )

    await log_audit_event(
        tenant_id=tid,
        actor_type="user",
        actor_id=str(current_user.sub),
        action="NETWORK_OPTIMIZE",
        entity_type="network",
        entity_id=tid,
        before_state={"demand_ids": [str(d.id) for d in demands_db]},
        after_state={
            "solver_status": result.solver_status,
            "assignments_count": len(result.assignments),
            "transfers_count": len(result.transfers),
            "total_make_cost": result.total_make_cost,
            "total_transfer_cost": result.total_transfer_cost,
        },
        rationale=f"alpha={alpha}, demands={len(demands)}",
    )

    return APIResponse(success=True, data={
        "assignments": result.assignments,
        "transfers": result.transfers,
        "total_make_cost": result.total_make_cost,
        "total_transfer_cost": result.total_transfer_cost,
        "total_penalty": result.total_penalty,
        "objective_value": result.objective_value,
        "solver_status": result.solver_status,
        "unsatisfied_demands": result.unsatisfied_demands,
        "xai_explanation": XAIExplanation(
            constraints=["plant_capacity_limits", "fleet_availability", "transfer_route_reliability"]
                         + ([f"unsatisfied_{d.demand_id}" for d in result.unsatisfied_demands[:3]] if result.unsatisfied_demands else []),
            assumptions=[f"alpha_{alpha}_make_preference", f"horizon_{req.horizon_days}_days", "transfer_cost_additive"],
            confidence_score=round(1.0 if result.solver_status == "OPTIMAL" else (0.5 if result.solver_status == "FEASIBLE" else 0.0), 4),
            contributing_factors={
                "total_make_cost": round(min(1.0, result.total_make_cost / max(1, result.total_make_cost + result.total_transfer_cost)), 4),
                "total_transfer_cost": round(min(1.0, result.total_transfer_cost / max(1, result.total_make_cost + result.total_transfer_cost)), 4),
                "penalty_weight": round(result.total_penalty / max(1, result.total_make_cost + result.total_transfer_cost + result.total_penalty), 4),
            },
        ).model_dump(),
    }, error=None)


class GreenScheduleRequest(BaseModel):
    mo_ids: list[UUID] | None = None
    horizon_hours: int = 168
    alpha: float = 0.5
    beta: float = 0.3


@router.post("/green-schedule")
async def green_schedule(
    req: GreenScheduleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    """Carbon-aware scheduling: minimize carbon footprint + cost."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers_db = wc_result.scalars().all()

    mos_query = sa_select(ManufacturingOrder).where(ManufacturingOrder.tenant_id == tid)
    if req.mo_ids:
        mos_query = mos_query.where(ManufacturingOrder.id.in_(req.mo_ids))
    mo_result = await session.execute(mos_query)
    mos = mo_result.scalars().all()

    ef_result = await session.execute(
        sa_select(EmissionFactor).where(EmissionFactor.tenant_id == tid)
    )
    emission_factors_db = ef_result.scalars().all()

    mc_result = await session.execute(
        sa_select(MaterialCarbon).where(MaterialCarbon.tenant_id == tid)
    )
    material_carbons_db = mc_result.scalars().all()

    te_result = await session.execute(
        sa_select(TransportEmission).where(TransportEmission.tenant_id == tid)
    )
    transport_emissions_db = te_result.scalars().all()

    now = datetime.now(UTC)
    ops = []
    for mo in mos:
        routing_result = await session.execute(
            sa_select(RoutingOperation).where(RoutingOperation.tenant_id == tid, RoutingOperation.bom_id == mo.bom_id)
        )
        for r in routing_result.scalars().all():
            due_date_minutes = None
            if mo.planned_end:
                delta = (mo.planned_end - now).total_seconds() / 60.0
                due_date_minutes = max(0, int(delta))

            ops.append({
                "id": str(r.id),
                "mo_id": str(mo.id),
                "sequence": int(r.sequence),
                "work_center_id": str(r.work_center_id),
                "duration_planned_mins": int(r.duration_planned_mins or 60) + int(r.setup_time_mins or 0),
                "due_date_minutes": due_date_minutes,
                "parent_operation_id": str(r.parent_operation_id) if r.parent_operation_id else None,
            })

    wc_list = [
        {
            "id": str(w.id),
            "name": w.name,
            "capacity_hours_per_day": float(w.capacity_hours_per_day or 8),
            "energy_kwh_per_hour": float(w.energy_kwh_per_hour or 0),
            "cost_per_hour": float(w.cost_per_hour or 0),
            "energy_source": "grid",
        }
        for w in work_centers_db
    ]

    emission_factors = [
        EmissionFactorData(
            energy_source=ef.energy_source,
            region=ef.region,
            factor_kg_co2_per_kwh=float(ef.factor_kg_co2_per_kwh),
        )
        for ef in emission_factors_db
    ]

    if not emission_factors:
        emission_factors = [
            EmissionFactorData(energy_source="grid", region="global", factor_kg_co2_per_kwh=0.5),
        ]

    material_carbons = [
        MaterialCarbonData(
            product_id=str(mc.product_id),
            kg_co2_per_unit=float(mc.kg_co2_per_unit),
            kg_co2_per_kg=float(mc.kg_co2_per_kg) if mc.kg_co2_per_kg else None,
            recycled_content_pct=float(mc.recycled_content_pct or 0),
        )
        for mc in material_carbons_db
    ]

    transport_emissions = [
        TransportEmissionData(
            route_id=str(te.route_id),
            vehicle_type=te.vehicle_type,
            kg_co2_per_unit_per_km=float(te.kg_co2_per_unit_per_km),
            load_factor_avg=float(te.load_factor_avg or 0.8),
        )
        for te in transport_emissions_db
    ]

    horizon = req.horizon_hours * 60
    alpha = max(0.1, min(0.9, req.alpha))
    beta = max(0.0, min(0.5, req.beta))

    if alpha + beta > 0.9:
        beta = 0.9 - alpha

    result = solve_green_schedule(
        work_centers=wc_list,
        operations=ops,
        emission_factors=emission_factors,
        material_carbons=material_carbons,
        transport_emissions=transport_emissions,
        horizon_mins=horizon,
        alpha=alpha,
        beta=beta,
    )

    await log_audit_event(
        tenant_id=tid,
        actor_type="user",
        actor_id=str(current_user.sub),
        action="GREEN_SCHEDULE",
        entity_type="schedule",
        entity_id=tid,
        before_state={"mo_ids": [str(m.id) for m in mos]},
        after_state={
            "solver_status": result.solver_status,
            "total_carbon_kg": result.total_carbon_kg,
            "total_make_cost": result.total_make_cost,
        },
        rationale=f"alpha={alpha}, beta={beta}",
    )

    return APIResponse(success=True, data={
        "assignments": result.assignments,
        "total_carbon_kg": result.total_carbon_kg,
        "total_make_cost": result.total_make_cost,
        "carbon_per_unit": result.carbon_per_unit,
        "carbon_breakdown": result.carbon_breakdown,
        "objective_value": result.objective_value,
        "solver_status": result.solver_status,
        "xai_explanation": XAIExplanation(
            constraints=["no_overlap_per_work_center", "precedence_within_mo_groups", "carbon_emission_bound"]
                         + ([f"bottleneck_{b}" for b in list(result.carbon_breakdown.keys())[:3]] if result.carbon_breakdown else []),
            assumptions=[f"alpha_{alpha}_tardiness_weight", f"beta_{beta}_carbon_weight", "emission_factors_per_kwh"],
            confidence_score=round(1.0 if result.solver_status == "OPTIMAL" else (0.5 if result.solver_status == "FEASIBLE" else 0.0), 4),
            contributing_factors={
                "tardiness": round(alpha, 4),
                "carbon": round(beta, 4),
                "cost": round(1.0 - alpha - beta, 4),
                "total_carbon_kg": round(min(1.0, result.total_carbon_kg / max(1, result.total_make_cost)), 4),
            },
        ).model_dump(),
    }, error=None)


class ISolverRequest(BaseModel):
    solver: str = "ortools"
    horizon_hours: int = 168
    mo_ids: list[UUID] | None = None
    frozen_ops: list[dict] | None = None
    warm_start: list[dict] | None = None
    alpha: float = 0.5
    tariffs: list[dict] | None = None
    green_config: dict | None = None
    enforce_skills: bool = True


@router.post("/solve")
async def solve_with_isolver(
    req: ISolverRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    """Unified solver endpoint using ISolver interface.

    Selects solver by name ('ortools' or 'gurobi') via SolverFactory.
    Falls back to OR-Tools if Gurobi license is unavailable.
    """
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    factory = SolverFactory.get_instance()
    solver = factory.create_solver(req.solver)

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    work_centers = wc_result.scalars().all()

    mos_query = sa_select(ManufacturingOrder).where(ManufacturingOrder.tenant_id == tid)
    if req.mo_ids:
        mos_query = mos_query.where(ManufacturingOrder.id.in_(req.mo_ids))
    mo_result = await session.execute(mos_query)
    mos = mo_result.scalars().all()

    worker_result = await session.execute(
        sa_select(Worker).where(Worker.tenant_id == tid, Worker.is_active == True)
    )
    workers_db = worker_result.scalars().all()

    shift_result = await session.execute(
        sa_select(Shift).where(Shift.tenant_id == tid, Shift.is_active == True)
    )
    shifts_db = {str(s.id): s for s in shift_result.scalars().all()}

    default_shift = [{"days_of_week": [0,1,2,3,4], "start_hour": 8, "end_hour": 16, "break_minutes": 30}]

    worker_inputs = []
    for w in workers_db:
        skills = []
        if hasattr(w, 'skills') and w.skills:
            skills = [str(s.id) for s in w.skills]
        shift_rules = default_shift
        if w.shift_calendar_id and str(w.shift_calendar_id) in shifts_db:
            shift = shifts_db[str(w.shift_calendar_id)]
            shift_rules = [{
                "days_of_week": shift.days_of_week if shift.days_of_week else [0,1,2,3,4],
                "start_hour": shift.start_hour if shift.start_hour is not None else 8,
                "start_minute": shift.start_minute if shift.start_minute is not None else 0,
                "end_hour": shift.end_hour if shift.end_hour is not None else 16,
                "end_minute": shift.end_minute if shift.end_minute is not None else 0,
                "break_minutes": shift.break_minutes if shift.break_minutes is not None else 30,
            }]
        worker_inputs.append(WorkerInput(
            id=str(w.id),
            skill_ids=skills,
            skill_tags=[],
            shift_rules=shift_rules,
            cost_per_hour=float(w.cost_per_hour) if w.cost_per_hour else 0.0,
            overtime_eligible=bool(w.overtime_eligible),
        ))

    wc_inputs = []
    for w in work_centers:
        wc_inputs.append(WorkCenterInput(
            id=str(w.id),
            name=w.name or "",
            capacity_per_hour=float(w.capacity_hours_per_day or 8) / 24.0,
            energy_kwh_per_hour=float(w.energy_kwh_per_hour) if w.energy_kwh_per_hour else 0.0,
            cost_per_hour=float(w.cost_per_hour) if w.cost_per_hour else 0.0,
            overtime_cost_multiplier=float(w.overtime_cost_multiplier) if w.overtime_cost_multiplier else 1.5,
            energy_source="grid",
        ))

    now = datetime.now(UTC)
    op_inputs = []
    for mo in mos:
        bom_result = await session.execute(
            sa_select(BillOfMaterial).where(BillOfMaterial.tenant_id == tid, BillOfMaterial.id == mo.bom_id)
        )
        bom = bom_result.scalar_one_or_none()

        routing_result = await session.execute(
            sa_select(RoutingOperation).where(RoutingOperation.tenant_id == tid, RoutingOperation.bom_id == mo.bom_id)
        )
        for r in routing_result.scalars().all():
            due_date_minutes = None
            if mo.planned_end:
                delta = (mo.planned_end - now).total_seconds() / 60.0
                due_date_minutes = max(0, int(delta))

            op_inputs.append(OperationInput(
                id=str(r.id),
                mo_id=str(mo.id),
                sequence=int(r.sequence),
                work_center_id=str(r.work_center_id),
                duration_planned_mins=int(r.duration_planned_mins or 60) + int(r.setup_time_mins or 0),
                priority_score=float(mo.feasibility_score or 0.5),
                due_date_minutes=due_date_minutes,
                bom_level=int(r.bom_level or 0) if r.bom_level is not None else int(bom.bom_level or 0) if bom else 0,
                parent_operation_id=str(r.parent_operation_id) if r.parent_operation_id else None,
                is_phantom=bool(bom.is_phantom) if bom else False,
                transfer_time_mins=int(r.transfer_time_mins or 0),
                required_skill_id=str(r.required_skill_id) if r.required_skill_id else None,
                required_skill_tags=list(r.required_skill_tags) if r.required_skill_tags else [],
                requires_operator=bool(r.requires_operator) if r.requires_operator is not None else True,
                operation_name=r.operation_name or f"Op {r.sequence}",
                material_score=float(mo.material_score or 1.0),
            ))

    frozen_ops = None
    if req.frozen_ops:
        from ipe_shared.solver.interface import FrozenOp
        frozen_ops = [
            FrozenOp(operation_id=f.get("operation_id", ""), fixed_start=f.get("fixed_start", 0), fixed_end=f.get("fixed_end", 0))
            for f in req.frozen_ops
        ]

    warm_start = None
    if req.warm_start:
        warm_start = [WarmStart(operation_id=ws.get("operation_id", ""), start_minute=ws.get("start_minute", 0)) for ws in req.warm_start]

    green_config = None
    if req.green_config:
        green_config = GreenScheduleConfig(
            beta=req.green_config.get("beta", 0.3),
            emission_factors=req.green_config.get("emission_factors", []),
            material_carbons=req.green_config.get("material_carbons", []),
            transport_emissions=req.green_config.get("transport_emissions", []),
        )

    config = SolverConfig(
        alpha=max(0.1, min(0.9, req.alpha)),
        tariffs=req.tariffs or [],
        green=green_config,
        solver_timeout_seconds=30,
        max_bom_depth=settings.MAX_BOM_DEPTH,
        enforce_skills=req.enforce_skills,
    )

    context = SolverContext(
        work_centers=wc_inputs,
        operations=op_inputs,
        workers=worker_inputs,
        horizon=req.horizon_hours * 60,
        frozen_ops=frozen_ops or [],
        warm_start=warm_start or [],
        config=config,
        tenant_id=tenant_id,
    )

    result = solver.solve(context)

    await log_audit_event(
        tenant_id=tid,
        actor_type="user",
        actor_id=str(current_user.sub),
        action="ISOLVER_SCHEDULE",
        entity_type="schedule",
        entity_id=tid,
        before_state={"mo_ids": [str(m.id) for m in mos], "solver": req.solver},
        after_state={
            "solver_name": solver.name(),
            "solver_status": result.solver_status.value,
            "total_operations": result.total_operations,
            "solve_time_ms": result.solve_time_ms,
            "skill_relaxed": result.skill_relaxed,
        },
        rationale=f"solver={req.solver}, alpha={req.alpha}, green={req.green_config is not None}",
    )

    return APIResponse(success=True, data={
        "solver_name": solver.name(),
        "solver_status": result.solver_status.value,
        "assignments": [
            {
                "operation_id": a.operation_id,
                "work_center_id": a.work_center_id,
                "start_minute": a.start_minute,
                "end_minute": a.end_minute,
                "duration": a.duration,
                "on_time": a.on_time,
                "mo_id": a.mo_id,
                "sequence": a.sequence,
                "bom_level": a.bom_level,
                "parent_operation_id": a.parent_operation_id,
                "operation_name": a.operation_name,
                "worker_id": a.worker_id,
            }
            for a in result.assignments
        ],
        "mo_tardiness": [
            {
                "mo_id": t.mo_id,
                "due_date_minute": t.due_date_minute,
                "completion_minute": t.completion_minute,
                "tardiness_minutes": t.tardiness_minutes,
                "on_time": t.on_time,
            }
            for t in result.mo_tardiness
        ],
        "total_operations": result.total_operations,
        "solve_time_ms": result.solve_time_ms,
        "skill_relaxed": result.skill_relaxed,
        "cost_summary": result.cost_summary,
        "cost_breakdown": result.cost_breakdown,
        "carbon_breakdown": result.carbon_breakdown,
        "total_carbon_kg": result.total_carbon_kg,
        "carbon_per_unit": result.carbon_per_unit,
        "xai_explanation": XAIExplanation(
            constraints=["no_overlap_per_work_center", "precedence_within_mo_groups", f"solver_{solver.name()}"]
                         + (["skill_relaxation_applied"] if result.skill_relaxed else []),
            assumptions=["30s_solver_timeout", f"solver_backend_{solver.name()}"],
            confidence_score=round(1.0 if result.solver_status == SolverStatus.OPTIMAL else (0.5 if result.solver_status in (SolverStatus.FEASIBLE, SolverStatus.SKILL_RELAXED) else 0.0), 4),
            contributing_factors={"solve_time_ms": result.solve_time_ms, "total_operations": result.total_operations},
        ).model_dump(),
    }, error=None)


@router.get("/schedule/active")
async def get_active_schedule(
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supervisor"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    rows = await load_active_schedule(session, UUID(tenant_id))
    return APIResponse(success=True, data={"rows": rows, "source": "cdm"}, error=None)


@router.post("/schedule/approve")
async def approve_production_schedule(
    req: ScheduleApproveRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    if not req.mo_ids:
        return APIResponse(success=True, data={
            "activated": [], "failed": [], "total": 0, "activated_count": 0, "failed_count": 0,
        }, error=None)

    result = await approve_schedule_mos(
        session,
        UUID(tenant_id),
        req.mo_ids,
        expected_versions=req.expected_versions,
        approved_by=req.approved_by or getattr(current_user, "sub", "planner"),
    )

    has_conflict = any(f.get("reason") == "VERSION_CONFLICT" for f in result["failed"])
    if has_conflict and not result["activated"]:
        return APIResponse(
            success=False,
            data=result,
            error={"code": "VERSION_CONFLICT", "message": "Schedule changed since last load. Refresh and retry."},
        )

    return APIResponse(success=True, data=result, error=None)


@router.post("/validate")
async def validate_schedule_inputs(
    req: ScheduleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    """Pre-solve validation: Valid / Warning / Blocked per MO."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    mos_query = sa_select(ManufacturingOrder).where(ManufacturingOrder.tenant_id == tid)
    if req.mo_ids:
        mos_query = mos_query.where(ManufacturingOrder.id.in_(req.mo_ids))
    mo_result = await session.execute(mos_query)
    mos = mo_result.scalars().all()

    results = []
    for mo in mos:
        vstatus = "valid"
        reasons: list[str] = []
        if float(mo.material_score or 1) < 0.5:
            vstatus = "blocked"
            reasons.append("Material shortage — insufficient stock")
        elif float(mo.feasibility_score or 100) < 50:
            vstatus = "warning"
            reasons.append(f"Low feasibility score ({mo.feasibility_score})")
        if mo.primary_constraint:
            reasons.append(f"Primary constraint: {mo.primary_constraint}")
        results.append({
            "mo_id": str(mo.id),
            "erp_mo_id": mo.erp_mo_id,
            "status": vstatus,
            "reasons": reasons,
            "priority_score": await resolve_mo_priority(session, tid, mo),
        })

    return APIResponse(success=True, data={"validations": results}, error=None)
