from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.database.session import get_session
from ipe_shared.models.delay_event import DelayEvent
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.product import Product
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DemandSummary(BaseModel):
    id: str
    product_name: str
    quantity: float
    required_date: str
    demand_type: str
    priority_score: float | None
    status: str


class CapacitySummary(BaseModel):
    work_center: str
    total_hours: float
    utilized_hours: float
    utilization_pct: float
    status: str


class DelayAlert(BaseModel):
    id: str
    mo_ref: str
    cause: str
    delay_minutes: int
    created_at: str
    severity: str


class DemandsPayload(BaseModel):
    demands: list[DemandSummary]


class CapacityPayload(BaseModel):
    capacity: list[CapacitySummary]


class AlertsPayload(BaseModel):
    alerts: list[DelayAlert]


def _tenant_id(current_user: TokenPayload) -> UUID:
    return UUID(str(current_user.tenant_id))


@router.get("/demands", response_model=APIResponse[DemandsPayload])
async def dashboard_demands(
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[DemandsPayload]:
    tenant_id = _tenant_id(current_user)
    stmt = (
        select(DemandLine, Product)
        .join(Product, DemandLine.product_id == Product.id)
        .where(DemandLine.tenant_id == tenant_id)
        .order_by(DemandLine.required_date.asc())
        .limit(50)
    )
    result = await session.execute(stmt)
    demands = [
        DemandSummary(
            id=str(demand.id),
            product_name=product.name,
            quantity=float(demand.quantity),
            required_date=demand.required_date.isoformat(),
            demand_type=demand.demand_type,
            priority_score=float(demand.priority_score) if demand.priority_score is not None else None,
            status=demand.status,
        )
        for demand, product in result.all()
    ]
    return APIResponse(data=DemandsPayload(demands=demands))


@router.get("/capacity", response_model=APIResponse[CapacityPayload])
async def dashboard_capacity(
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[CapacityPayload]:
    tenant_id = _tenant_id(current_user)
    result = await session.execute(
        select(WorkCenter).where(WorkCenter.tenant_id == tenant_id).order_by(WorkCenter.name)
    )
    capacity: list[CapacitySummary] = []
    for wc in result.scalars().all():
        total_hours = float(wc.capacity_hours_per_day or 0)
        oee = float(wc.oee or 0.85)
        utilized_hours = round(total_hours * oee, 2)
        utilization_pct = round(oee * 100, 1)
        capacity.append(
            CapacitySummary(
                work_center=wc.name,
                total_hours=total_hours,
                utilized_hours=utilized_hours,
                utilization_pct=utilization_pct,
                status=wc.status or "operational",
            )
        )
    return APIResponse(data=CapacityPayload(capacity=capacity))


@router.get("/alerts", response_model=APIResponse[AlertsPayload])
async def dashboard_alerts(
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[AlertsPayload]:
    tenant_id = _tenant_id(current_user)
    stmt = (
        select(DelayEvent, ManufacturingOrder)
        .join(ManufacturingOrder, DelayEvent.mo_id == ManufacturingOrder.id)
        .where(DelayEvent.tenant_id == tenant_id)
        .order_by(DelayEvent.created_at.desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    alerts: list[DelayAlert] = []
    for event, mo in result.all():
        delay_minutes = int(event.delay_minutes or 0)
        if delay_minutes >= 240:
            severity = "high"
        elif delay_minutes >= 60:
            severity = "medium"
        else:
            severity = "low"
        alerts.append(
            DelayAlert(
                id=str(event.id),
                mo_ref=str(mo.erp_mo_id or mo.id),
                cause=event.cause_category,
                delay_minutes=delay_minutes,
                created_at=event.created_at.isoformat(),
                severity=severity,
            )
        )
    return APIResponse(data=AlertsPayload(alerts=alerts))
