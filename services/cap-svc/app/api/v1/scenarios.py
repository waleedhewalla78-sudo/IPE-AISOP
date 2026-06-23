from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from dateutil.parser import isoparse
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.scheduler import solve_schedule
from ipe_shared.audit.service import log_audit_event
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.routing import RoutingOperation
from ipe_shared.models.scenario import Scenario, ScenarioDemand, ScenarioResource, ScenarioSupply
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class CloneRequest(BaseModel):
    mo_ids: list[UUID]
    name: str
    description: str | None = None


class DisruptionInjection(BaseModel):
    mo_id: UUID
    delay_days: int = 0
    capacity_multiplier: float | None = None
    supply_blocked: bool = False


class DisruptionRequest(BaseModel):
    disruptions: list[DisruptionInjection]


@router.post("/clone")
async def clone_scenario(
    req: CloneRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    scenario = Scenario(
        tenant_id=tid,
        name=req.name,
        description=req.description,
        status="active",
        created_by="api",
    )
    session.add(scenario)
    await session.flush()

    mo_result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tid,
            ManufacturingOrder.id.in_(req.mo_ids),
        )
    )
    mos = mo_result.scalars().all()

    for mo in mos:
        demand_data = {
            "mo_id": str(mo.id),
            "product_id": str(mo.product_id) if mo.product_id else None,
            "quantity": float(mo.quantity or 0),
            "planned_start": mo.planned_start.isoformat() if mo.planned_start else None,
            "planned_end": mo.planned_end.isoformat() if mo.planned_end else None,
            "status": mo.status,
            "feasibility_score": float(mo.feasibility_score or 0),
            "material_score": float(mo.material_score or 0),
        }
        session.add(ScenarioDemand(
            scenario_id=scenario.id,
            original_demand_id=mo.id,
            data=demand_data,
        ))

    for mo in mos:
        routing_result = await session.execute(
            sa_select(RoutingOperation).where(
                RoutingOperation.tenant_id == tid,
                RoutingOperation.bom_id == mo.bom_id,
            )
        )
        for r in routing_result.scalars().all():
            supply_data = {
                "routing_id": str(r.id),
                "mo_id": str(mo.id),
                "work_center_id": str(r.work_center_id),
                "sequence": int(r.sequence),
                "duration_planned_mins": float(r.duration_planned_mins or 0),
                "setup_time_mins": float(r.setup_time_mins or 0),
                "operation_name": r.operation_name,
                "parent_operation_id": str(r.parent_operation_id) if r.parent_operation_id else None,
                "bom_level": int(r.bom_level or 0) if r.bom_level is not None else 0,
                "transfer_time_mins": int(r.transfer_time_mins or 0) if r.transfer_time_mins is not None else 0,
            }
            session.add(ScenarioSupply(
                scenario_id=scenario.id,
                original_supply_id=r.id,
                data=supply_data,
            ))

    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tid)
    )
    for wc in wc_result.scalars().all():
        resource_data = {
            "work_center_id": str(wc.id),
            "name": wc.name,
            "capacity_hours_per_day": float(wc.capacity_hours_per_day or 8),
            "oee": float(wc.oee or 0.85),
            "status": wc.status or "operational",
        }
        session.add(ScenarioResource(
            scenario_id=scenario.id,
            original_resource_id=wc.id,
            data=resource_data,
        ))

    await session.commit()

    return APIResponse(
        success=True,
        data={
            "scenario_id": str(scenario.id),
            "name": scenario.name,
            "demand_count": len(mos),
            "status": scenario.status,
        },
        error=None,
    )


@router.post("/{scenario_id}/disruption")
async def inject_disruption(
    scenario_id: UUID,
    req: DisruptionRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    scenario_result = await session.execute(
        sa_select(Scenario).where(
            Scenario.id == scenario_id,
            Scenario.tenant_id == tid,
        )
    )
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Scenario not found"},
        )

    demand_result = await session.execute(
        sa_select(ScenarioDemand).where(ScenarioDemand.scenario_id == scenario_id)
    )
    demands = {str(d.original_demand_id): d for d in demand_result.scalars().all()}

    supply_result = await session.execute(
        sa_select(ScenarioSupply).where(ScenarioSupply.scenario_id == scenario_id)
    )
    supplies = {str(s.data.get("mo_id")): s for s in supply_result.scalars().all()}

    resource_result = await session.execute(
        sa_select(ScenarioResource).where(ScenarioResource.scenario_id == scenario_id)
    )
    resources = {str(r.data.get("work_center_id")): r for r in resource_result.scalars().all()}

    applied = []
    for disruption in req.disruptions:
        mo_id_str = str(disruption.mo_id)

        if mo_id_str in demands:
            d = demands[mo_id_str]
            if disruption.delay_days > 0:
                d.data["delay_days"] = disruption.delay_days
                if d.data.get("planned_end"):
                    end = isoparse(d.data["planned_end"])
                    d.data["disrupted_end"] = (end + timedelta(days=disruption.delay_days)).isoformat()
            if disruption.supply_blocked:
                d.data["supply_blocked"] = True
                d.data["material_score"] = 0.0
            applied.append({"mo_id": mo_id_str, "type": "demand"})

        if mo_id_str in supplies:
            s = supplies[mo_id_str]
            if disruption.capacity_multiplier is not None:
                s.data["capacity_multiplier"] = disruption.capacity_multiplier
                original_duration = s.data.get("duration_planned_mins", 60)
                s.data["disrupted_duration"] = original_duration / disruption.capacity_multiplier
            applied.append({"mo_id": mo_id_str, "type": "supply"})

        if disruption.capacity_multiplier is not None:
            for _wc_id, r in resources.items():
                r.data["capacity_multiplier"] = disruption.capacity_multiplier

    await session.commit()

    return APIResponse(
        success=True,
        data={
            "scenario_id": str(scenario_id),
            "disruptions_applied": applied,
        },
        error=None,
    )


@router.post("/{scenario_id}/solve")
async def solve_scenario(
    scenario_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    scenario_result = await session.execute(
        sa_select(Scenario).where(
            Scenario.id == scenario_id,
            Scenario.tenant_id == tid,
        )
    )
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Scenario not found"},
        )

    demand_result = await session.execute(
        sa_select(ScenarioDemand).where(ScenarioDemand.scenario_id == scenario_id)
    )
    demands = demand_result.scalars().all()

    supply_result = await session.execute(
        sa_select(ScenarioSupply).where(ScenarioSupply.scenario_id == scenario_id)
    )
    supplies = {str(s.data.get("mo_id")): s for s in supply_result.scalars().all()}

    resource_result = await session.execute(
        sa_select(ScenarioResource).where(ScenarioResource.scenario_id == scenario_id)
    )
    resources = {str(r.data.get("work_center_id")): r for r in resource_result.scalars().all()}

    wc_list = []
    for r in resources.values():
        cap = float(r.data.get("capacity_hours_per_day", 8))
        mult = r.data.get("capacity_multiplier")
        if mult:
            cap *= mult
        wc_list.append({
            "id": r.data["work_center_id"],
            "name": r.data.get("name", ""),
            "capacity_hours_per_day": cap,
            "oee": r.data.get("oee", 0.85),
        })

    ops = []
    now = datetime.now(UTC)
    for demand in demands:
        mo_data = demand.data
        mo_id = mo_data.get("mo_id", str(demand.original_demand_id))
        supply = supplies.get(mo_id)
        if not supply:
            continue

        s_data = supply.data
        duration = int(s_data.get("duration_planned_mins", 60))
        disrupted_dur = s_data.get("disrupted_duration")
        if disrupted_dur:
            duration = int(disrupted_dur)

        due = None
        disrupted_end = mo_data.get("disrupted_end")
        if disrupted_end:
            end_dt = isoparse(disrupted_end)
            due = max(0, int((end_dt - now).total_seconds() / 60))
        elif mo_data.get("planned_end"):
            end_dt = isoparse(mo_data["planned_end"])
            delay = mo_data.get("delay_days", 0)
            if delay:
                end_dt = end_dt + timedelta(days=delay)
            due = max(0, int((end_dt - now).total_seconds() / 60))

        material_score = mo_data.get("material_score", 1.0)
        if mo_data.get("supply_blocked"):
            material_score = 0.0

        ops.append({
            "id": s_data.get("routing_id", str(uuid4())),
            "mo_id": mo_id,
            "sequence": s_data.get("sequence", 0),
            "work_center_id": s_data.get("work_center_id", ""),
            "duration_planned_mins": duration,
            "operation_name": s_data.get("operation_name", ""),
            "due_date_minutes": due,
            "priority_score": mo_data.get("feasibility_score", 0.5),
            "material_score": material_score,
            "parent_operation_id": s_data.get("parent_operation_id"),
            "bom_level": s_data.get("bom_level", 0),
            "transfer_time_mins": s_data.get("transfer_time_mins", 0),
        })

    if not ops:
        return APIResponse(
            success=True,
            data={"scenario_id": str(scenario_id), "schedule": {"status": "NO_DATA"}},
            error=None,
        )

    horizon = 14 * 24 * 60
    schedule = solve_schedule(
        wc_list, ops, horizon=horizon,
        solver_timeout_seconds=30,
        max_bom_depth=settings.MAX_BOM_DEPTH,
    )

    await log_audit_event(
        tenant_id=tid,
        actor_type="user",
        actor_id=str(current_user.sub),
        action="RUN_SCENARIO",
        entity_type="scenario",
        entity_id=scenario_id,
        after_state={
            "solver_status": schedule.get("solver_status"),
            "total_operations": len(ops),
        },
        rationale=f"Scenario solve for {len(ops)} operations",
    )

    return APIResponse(
        success=True,
        data={
            "scenario_id": str(scenario_id),
            "schedule": schedule,
            "total_operations": len(ops),
            "xai_explanation": XAIExplanation(
                constraints=["no_overlap_per_work_center", "precedence_within_mo_groups"],
                assumptions=["30s_solver_timeout", "scenario_baseline_from_clone"],
                confidence_score=round(1.0 if schedule.get("solver_status") == "OPTIMAL" else (0.5 if schedule.get("solver_status") == "FEASIBLE" else 0.0), 4),
                contributing_factors={"solver_status": round(1.0 if schedule.get("solver_status") == "OPTIMAL" else 0.5, 4), "operations": float(len(ops))},
            ).model_dump(),
        },
        error=None,
    )


@router.get("/{scenario_id}/diff")
async def scenario_diff(
    scenario_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    scenario_result = await session.execute(
        sa_select(Scenario).where(
            Scenario.id == scenario_id,
            Scenario.tenant_id == tid,
        )
    )
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Scenario not found"},
        )

    demand_result = await session.execute(
        sa_select(ScenarioDemand).where(ScenarioDemand.scenario_id == scenario_id)
    )
    demands = demand_result.scalars().all()

    supply_result = await session.execute(
        sa_select(ScenarioSupply).where(ScenarioSupply.scenario_id == scenario_id)
    )
    supplies = supply_result.scalars().all()

    baseline_items = []
    scenario_items = []
    for d in demands:
        original = {
            "mo_id": str(d.original_demand_id),
            "quantity": d.data.get("quantity", 0),
            "planned_end": d.data.get("planned_end"),
            "material_score": d.data.get("feasibility_score", 0),
        }
        disrupted = dict(original)
        disrupted["quantity"] = d.data.get("quantity", 0)
        disrupted["planned_end"] = d.data.get("disrupted_end") or d.data.get("planned_end")
        disrupted["material_score"] = d.data.get("material_score", d.data.get("feasibility_score", 0))
        disrupted["delay_days"] = d.data.get("delay_days", 0)
        disrupted["supply_blocked"] = d.data.get("supply_blocked", False)

        baseline_items.append(original)
        scenario_items.append(disrupted)

    baseline_total = sum(i["quantity"] for i in baseline_items)
    scenario_total = sum(i["quantity"] for i in scenario_items)

    blocked_count = sum(1 for i in scenario_items if i.get("supply_blocked"))
    delayed_count = sum(1 for i in scenario_items if i.get("delay_days", 0) > 0)

    return APIResponse(
        success=True,
        data={
            "scenario_id": str(scenario_id),
            "scenario_name": scenario.name,
            "baseline": {
                "total_demand": baseline_total,
                "items": baseline_items,
            },
            "scenario": {
                "total_demand": scenario_total,
                "items": scenario_items,
            },
            "impact": {
                "blocked_count": blocked_count,
                "delayed_count": delayed_count,
                "total_items": len(demands),
            },
        },
        error=None,
    )
