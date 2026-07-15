"""Phase 5 Planning Center + Command Center APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.core.phase5 import (
    ActionTracker,
    build_mps,
    build_ops_dashboard,
    build_performance_cockpit,
    build_planning_cockpit,
    build_predictive_command,
    build_shift_handover,
    build_war_room,
    explode_mrp,
    level_production,
    promise_order,
    run_crp,
    run_rccp,
    run_scenario_cascade,
)
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/planning-command", tags=["phase5-planning-command"])
_tracker = ActionTracker()


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


class MPSRequest(BaseModel):
    product_id: str = "FG-DT100"
    lot_size: int = 5
    safety_stock: float = 15
    opening_inventory: float = 45
    weeks: list[dict[str, Any]] | None = None


class MRPRequest(BaseModel):
    product_id: str = "FG-DT100"
    mo_qty: float = 20
    bom: list[dict[str, Any]] | None = None
    inventory: dict[str, dict[str, float]] | None = None
    scrap_pct: float = 0.0


class PromiseRequest(BaseModel):
    order_id: str = "SO-2026-0200"
    product_id: str = "FG-DT100"
    qty: float = 5
    requested_date: str = "2026-08-10"
    inventory_available: float = 12
    capacity_available_hrs: float = 40
    hours_per_unit: float = 2.5
    unit_cost: float = 8500
    unit_price: float = 12000
    material_lead_days: int = 0
    reserved_inventory: float = 0.0
    production_lead_days: int = 7
    opportunity_cost: float = 0.0


class LevelRequest(BaseModel):
    weekly_demand: list[dict[str, Any]] = Field(default_factory=list)
    capacity_per_week: float = 30


class RCCPRequest(BaseModel):
    week: str = "W31"
    loads: list[dict[str, Any]] | None = None


class CRPRequest(BaseModel):
    work_centre: str = "Winding"
    week: str = "W31"
    days: list[dict[str, Any]] | None = None
    hours_per_shift: float = 7.5
    shifts_per_day: int = 2


class ScenarioRequest(BaseModel):
    name: str = "Q4 demand +20%"
    demand_uplift_pct: float = 20.0
    baseline_revenue: float = 2_400_000.0
    winding_util_pct: float = 84.0
    copper_weeks_cover: float = 4.0
    otd_pct: float = 89.0


class WarRoomRequest(BaseModel):
    incident_id: str = "INC-WND-002"
    title: str = "Winding Machine #2 Breakdown"
    affected_mos: list[str] = Field(default_factory=lambda: ["MO-ST-003", "MO-ST-004", "MO-ST-008"])
    revenue_at_risk: float = 340_000
    customers: list[str] = Field(default_factory=lambda: ["Saudi Electricity", "Dubai Water"])
    downtime_hours_so_far: float = 2.25


class HandoverRequest(BaseModel):
    from_shift: str = "A"
    to_shift: str = "B"
    completed_mos: list[str] = Field(default_factory=list)
    in_progress: list[dict[str, Any]] = Field(default_factory=list)
    open_issues: list[str] = Field(default_factory=list)
    quality_holds: list[str] = Field(default_factory=list)
    notes: str | None = None


class ActionCreate(BaseModel):
    title: str
    owner: str
    source: str = "planner"
    due: str | None = None
    mo_id: str | None = None


class ActionComplete(BaseModel):
    outcome: str


@router.get("/cockpit")
async def planning_cockpit(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    return APIResponse(
        success=True,
        data=build_planning_cockpit(tenant_id=_tenant(x_tenant_id)),
        error=None,
    )


@router.post("/mps")
async def mps_update(req: MPSRequest):
    return APIResponse(success=True, data=build_mps(**req.model_dump()), error=None)


@router.post("/mrp/explode")
async def mrp_explode(req: MRPRequest):
    return APIResponse(success=True, data=explode_mrp(**req.model_dump()), error=None)


@router.post("/promise")
async def order_promise(req: PromiseRequest):
    return APIResponse(success=True, data=promise_order(**req.model_dump()), error=None)


@router.post("/level")
async def production_level(req: LevelRequest):
    return APIResponse(
        success=True,
        data=level_production(
            weekly_demand=req.weekly_demand
            or [
                {"week": "W29", "demand": 42},
                {"week": "W30", "demand": 18},
                {"week": "W31", "demand": 35},
                {"week": "W32", "demand": 12},
            ],
            capacity_per_week=req.capacity_per_week,
        ),
        error=None,
    )


@router.post("/capacity/rccp")
async def capacity_rccp(req: RCCPRequest):
    return APIResponse(success=True, data=run_rccp(**req.model_dump()), error=None)


@router.post("/capacity/crp")
async def capacity_crp(req: CRPRequest):
    return APIResponse(success=True, data=run_crp(**req.model_dump()), error=None)


@router.post("/scenarios/cascade")
async def scenario_cascade(req: ScenarioRequest):
    return APIResponse(success=True, data=run_scenario_cascade(**req.model_dump()), error=None)


@router.get("/ops/dashboard")
async def ops_dashboard(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    return APIResponse(
        success=True,
        data=build_ops_dashboard(tenant_id=_tenant(x_tenant_id)),
        error=None,
    )


@router.post("/ops/war-room")
async def ops_war_room(req: WarRoomRequest):
    return APIResponse(success=True, data=build_war_room(**req.model_dump()), error=None)


@router.post("/ops/shift-handover")
async def ops_shift_handover(req: HandoverRequest):
    return APIResponse(success=True, data=build_shift_handover(**req.model_dump()), error=None)


@router.get("/ops/performance")
async def ops_performance():
    return APIResponse(success=True, data=build_performance_cockpit(), error=None)


@router.get("/ops/predictive")
async def ops_predictive():
    return APIResponse(success=True, data=build_predictive_command(), error=None)


@router.get("/actions")
async def list_actions(status: str | None = None):
    return APIResponse(success=True, data={"actions": _tracker.list(status=status)}, error=None)


@router.post("/actions")
async def create_action(req: ActionCreate):
    return APIResponse(success=True, data=_tracker.create(**req.model_dump()), error=None)


@router.post("/actions/{action_id}/complete")
async def complete_action(action_id: str, req: ActionComplete):
    item = _tracker.complete(action_id, req.outcome)
    if not item:
        return APIResponse(success=False, data=None, error="action_not_found")
    return APIResponse(success=True, data=item, error=None)
