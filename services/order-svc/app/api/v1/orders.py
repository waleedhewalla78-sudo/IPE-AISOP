from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.promising import compute_atp_promise
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.inventory import InventoryPosition
from ipe_shared.models.v8_phase2 import CustomerOrder, CustomerOrderLine, OrderPromise
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderLineIn(BaseModel):
    product_id: UUID
    quantity: float = Field(gt=0)
    unit_price: float = Field(default=0, ge=0)


class CreateOrderRequest(BaseModel):
    customer_id: UUID | None = None
    requested_date: datetime | None = None
    priority: int = Field(default=3, ge=1, le=5)
    lines: list[OrderLineIn]


async def _on_hand(session: AsyncSession, tenant_id: str, product_id: UUID) -> float:
    result = await session.execute(
        select(func.coalesce(func.sum(InventoryPosition.qty_on_hand), 0)).where(
            InventoryPosition.tenant_id == tenant_id,
            InventoryPosition.product_id == product_id,
        )
    )
    return float(result.scalar() or 0)


@router.post("")
async def create_order(
    req: CreateOrderRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    order_number = f"SO-{uuid4().hex[:8].upper()}"
    total = sum(l.quantity * l.unit_price for l in req.lines)
    order = CustomerOrder(
        tenant_id=tenant_id,
        customer_id=req.customer_id,
        order_number=order_number,
        requested_date=req.requested_date,
        priority=req.priority,
        total_value=total,
        status="open",
    )
    session.add(order)
    await session.flush()
    for line in req.lines:
        session.add(
            CustomerOrderLine(
                tenant_id=tenant_id,
                order_id=order.id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
            )
        )
    await session.commit()
    return APIResponse(
        success=True,
        data={"order_id": str(order.id), "order_number": order_number, "total_value": float(total)},
        error=None,
    )


@router.get("")
async def list_orders(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    rows = (
        await session.execute(
            select(CustomerOrder).where(CustomerOrder.tenant_id == tenant_id).order_by(CustomerOrder.created_at.desc()).limit(100)
        )
    ).scalars().all()
    return APIResponse(
        success=True,
        data={
            "orders": [
                {
                    "id": str(o.id),
                    "order_number": o.order_number,
                    "status": o.status,
                    "promised_date": o.promised_date.isoformat() if o.promised_date else None,
                    "total_value": float(o.total_value or 0),
                    "priority": o.priority,
                }
                for o in rows
            ]
        },
        error=None,
    )


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    order = await session.get(CustomerOrder, order_id)
    if not order or str(order.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Order not found"})
    lines = (
        await session.execute(select(CustomerOrderLine).where(CustomerOrderLine.order_id == order_id))
    ).scalars().all()
    return APIResponse(
        success=True,
        data={
            "id": str(order.id),
            "order_number": order.order_number,
            "status": order.status,
            "lines": [
                {
                    "id": str(l.id),
                    "product_id": str(l.product_id),
                    "quantity": float(l.quantity),
                    "promised_quantity": float(l.promised_quantity) if l.promised_quantity else None,
                    "unit_price": float(l.unit_price or 0),
                }
                for l in lines
            ],
        },
        error=None,
    )


@router.post("/{order_id}/promise")
async def promise_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    order = await session.get(CustomerOrder, order_id)
    if not order or str(order.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Order not found"})

    lines = (
        await session.execute(select(CustomerOrderLine).where(CustomerOrderLine.order_id == order_id))
    ).scalars().all()
    promises = []
    latest_promise: datetime | None = None
    for line in lines:
        on_hand = await _on_hand(session, tenant_id, line.product_id)
        calc = compute_atp_promise(float(line.quantity), on_hand)
        promise_dt = datetime.fromisoformat(calc["promise_date"].replace("Z", "+00:00"))
        if latest_promise is None or promise_dt > latest_promise:
            latest_promise = promise_dt
        row = OrderPromise(
            tenant_id=tenant_id,
            order_line_id=line.id,
            promise_type=calc["promise_type"],
            promise_date=promise_dt,
            confidence_score=calc["confidence_score"],
            expires_at=promise_dt + timedelta(days=7),
        )
        session.add(row)
        line.promised_quantity = calc["promised_quantity"]
        promises.append({"line_id": str(line.id), **calc})

    order.promised_date = latest_promise
    order.status = "promised"
    await session.commit()
    return APIResponse(success=True, data={"order_id": str(order_id), "promises": promises}, error=None)


@router.get("/exceptions/list")
async def order_exceptions(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    rows = (
        await session.execute(
            select(CustomerOrder).where(
                CustomerOrder.tenant_id == tenant_id,
                CustomerOrder.status.in_(["open", "exception"]),
            )
        )
    ).scalars().all()
    now = datetime.now(UTC)
    exceptions = []
    for o in rows:
        if o.requested_date and o.requested_date < now and o.status != "promised":
            exceptions.append(
                {
                    "order_id": str(o.id),
                    "order_number": o.order_number,
                    "type": "late_request_unpromised",
                    "severity": "high",
                }
            )
    return APIResponse(success=True, data={"exceptions": exceptions}, error=None)
