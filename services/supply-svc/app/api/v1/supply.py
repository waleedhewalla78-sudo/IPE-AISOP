from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.planner import build_replenishment_plan
from app.supply_feedback import publish_supply_adjustment
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.inventory import InventoryPosition
from ipe_shared.models.plant import Plant
from ipe_shared.models.transfer_route import TransferRoute
from ipe_shared.models.v8_phase2 import SupplyPlan
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/supply", tags=["supply"])


class GeneratePlanRequest(BaseModel):
    name: str = Field(default="Network replenishment")
    horizon_days: int = Field(default=30, ge=1, le=365)


@router.get("/network")
async def get_network(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    plants = (await session.execute(select(Plant).where(Plant.tenant_id == tenant_id))).scalars().all()
    routes = (await session.execute(select(TransferRoute).where(TransferRoute.tenant_id == tenant_id))).scalars().all()
    avg_util = 75.0
    if plants:
        avg_util = min(95.0, 60.0 + len(plants) * 5.0)
    avg_lead = 7.0
    if routes:
        avg_lead = float(sum(float(r.transit_time_hours or 0) for r in routes) / len(routes) / 24.0)
    product_row = (
        await session.execute(
            select(InventoryPosition.product_id)
            .where(InventoryPosition.tenant_id == tenant_id)
            .limit(1)
        )
    ).first()
    if product_row and product_row[0]:
        await publish_supply_adjustment(
            tenant_id=str(tenant_id),
            product_id=str(product_row[0]),
            base_value=100.0,
            capacity_utilization_pct=avg_util,
            lead_time_days=avg_lead,
            facilities_count=len(plants),
        )
    return APIResponse(
        success=True,
        data={
            "facilities": [
                {"id": str(p.id), "name": p.name, "code": p.code, "capacity_hours_per_day": p.capacity_hours_per_day}
                for p in plants
            ],
            "lanes": [
                {
                    "id": str(r.id),
                    "origin_plant_id": str(r.origin_plant_id),
                    "destination_plant_id": str(r.destination_plant_id),
                    "transit_time_hours": r.transit_time_hours,
                    "cost_per_unit": r.cost_per_unit,
                }
                for r in routes
            ],
        },
        error=None,
    )


@router.get("/inventory")
async def network_inventory(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    subq = (
        select(
            InventoryPosition.product_id,
            InventoryPosition.location_id,
            func.max(InventoryPosition.time).label("max_time"),
        )
        .where(InventoryPosition.tenant_id == tenant_id)
        .group_by(InventoryPosition.product_id, InventoryPosition.location_id)
        .subquery()
    )
    result = await session.execute(
        select(InventoryPosition).join(
            subq,
            (InventoryPosition.product_id == subq.c.product_id)
            & (InventoryPosition.location_id == subq.c.location_id)
            & (InventoryPosition.time == subq.c.max_time),
        )
    )
    rows = result.scalars().all()
    return APIResponse(
        success=True,
        data={
            "positions": [
                {
                    "product_id": str(r.product_id),
                    "location_id": str(r.location_id),
                    "qty_on_hand": float(r.qty_on_hand),
                    "qty_in_transit": float(r.qty_in_transit or 0),
                }
                for r in rows
            ]
        },
        error=None,
    )


@router.post("/plan/generate")
async def generate_plan(
    req: GeneratePlanRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    plants = (await session.execute(select(Plant).where(Plant.tenant_id == tenant_id))).scalars().all()
    routes = (await session.execute(select(TransferRoute).where(TransferRoute.tenant_id == tenant_id))).scalars().all()
    inv_result = await session.execute(
        select(InventoryPosition).where(InventoryPosition.tenant_id == tenant_id).limit(500)
    )
    inv_rows = [
        {"location_id": str(r.location_id), "qty_on_hand": float(r.qty_on_hand)} for r in inv_result.scalars().all()
    ]
    plant_dicts = [{"id": p.id, "name": p.name, "code": p.code} for p in plants]
    route_dicts = [
        {
            "origin_plant_id": r.origin_plant_id,
            "destination_plant_id": r.destination_plant_id,
            "transit_time_hours": r.transit_time_hours,
            "cost_per_unit": r.cost_per_unit,
        }
        for r in routes
    ]
    plan_body = build_replenishment_plan(plant_dicts, route_dicts, inv_rows)
    row = SupplyPlan(
        tenant_id=tenant_id,
        name=req.name,
        horizon_days=req.horizon_days,
        status="active",
        plan_jsonb=plan_body,
    )
    session.add(row)
    await session.commit()
    return APIResponse(success=True, data={"plan_id": str(row.id), **plan_body}, error=None)


@router.get("/visibility")
async def supply_visibility(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    plan_row = (
        await session.execute(
            select(SupplyPlan).where(SupplyPlan.tenant_id == tenant_id).order_by(SupplyPlan.created_at.desc()).limit(1)
        )
    ).scalars().first()
    inv_count = (
        await session.execute(
            select(func.count()).select_from(InventoryPosition).where(InventoryPosition.tenant_id == tenant_id)
        )
    ).scalar() or 0
    return APIResponse(
        success=True,
        data={
            "latest_plan": plan_row.plan_jsonb if plan_row else {},
            "inventory_snapshots": inv_count,
            "as_of": datetime.now(UTC).isoformat(),
        },
        error=None,
    )
