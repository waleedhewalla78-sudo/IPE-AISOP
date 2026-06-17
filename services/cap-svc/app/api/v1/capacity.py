from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

import copy

from app.core.bottleneck import detect_bottlenecks
from app.core.scheduler import solve_schedule
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.operator import Operator
from ipe_shared.models.routing import RoutingOperation
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/capacity", tags=["capacity"])


class ScheduleRequest(BaseModel):
    mo_ids: list[UUID] | None = None
    horizon_hours: int = 168


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
):
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
            priority = float(mo.feasibility_score or 0.5)
            ops.append({
                "id": str(r.id),
                "mo_id": str(mo.id),
                "sequence": int(r.sequence),
                "work_center_id": str(r.work_center_id),
                "duration_planned_mins": int(r.duration_planned_mins or 60) + int(r.setup_time_mins or 0),
                "operation_name": r.operation_name or f"Op {r.sequence}",
                "due_date_minutes": due_date_minutes,
                "priority_score": priority,
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
    schedule = solve_schedule(wc_list, ops, horizon=horizon)

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

    return APIResponse(success=True, data={
        "schedule": schedule,
        "bottlenecks": bottlenecks,
        "labor_gaps": labor_gaps[:5],
        "total_operations": len(ops),
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
