"""Demo portal endpoints for Shop Floor and SCN views."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.database.session import get_session
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.operator import Operator
from ipe_shared.models.product import Product
from ipe_shared.models.supplier import Supplier
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.models.work_order import WorkOrder

router_shop = APIRouter(prefix="/shop-floor", tags=["shop-floor"])
router_scn = APIRouter(prefix="/supply-chain", tags=["supply-chain"])


@router_shop.get("/items")
async def shop_floor_items(
    tenant_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    tid = tenant_id or UUID(str(current_user.tenant_id))
    stmt = (
        select(WorkOrder, ManufacturingOrder, Product, WorkCenter, Operator)
        .join(ManufacturingOrder, WorkOrder.mo_id == ManufacturingOrder.id)
        .join(Product, ManufacturingOrder.product_id == Product.id)
        .join(WorkCenter, WorkOrder.work_center_id == WorkCenter.id)
        .outerjoin(Operator, WorkOrder.operator_id == Operator.id)
        .where(WorkOrder.tenant_id == tid, WorkOrder.status.in_(["in_progress", "pending"]))
        .order_by(WorkOrder.sequence)
    )
    result = await session.execute(stmt)
    items = []
    for wo, mo, product, wc, op in result.all():
        progress = 65 if wo.status == "in_progress" else 10
        items.append(
            {
                "id": str(wo.id),
                "mo_id": mo.erp_mo_id or str(mo.id),
                "workcenter": wc.name,
                "status": wo.status,
                "progress": progress,
                "operator": op.name if op else "Unassigned",
                "start_time": mo.planned_start.isoformat() if mo.planned_start else "",
            }
        )
    return {"items": items}


@router_scn.get("/suppliers")
async def supply_chain_suppliers(
    tenant_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    tid = tenant_id or UUID(str(current_user.tenant_id))
    result = await session.execute(
        select(Supplier).where(Supplier.tenant_id == tid).order_by(Supplier.name)
    )
    suppliers = []
    for s in result.scalars().all():
        score = round(float(s.reliability_score or 0.8) * 100, 1)
        delay = float(s.avg_delay_days or 2)
        suppliers.append(
            {
                "id": str(s.id),
                "name": s.name,
                "score": score,
                "leadTimeDays": round(delay, 1),
                "defectRate": round(max(0.5, 5 - score / 20), 1),
                "status": "warning" if score < 80 else "active",
                "tier": 1 if score >= 90 else (2 if score >= 75 else 3),
            }
        )
    return {"suppliers": suppliers}
