from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.atp import probabilistic_atp, rule_based_atp, simulate_atp
from app.core.netting import cumulative_netting, priority_weighted_netting
from app.core.supplier_model import predict_delay
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/material", tags=["material"])


class AvailabilityRequest(BaseModel):
    product_id: UUID
    quantity: float
    required_date: str


class NettingRequest(BaseModel):
    product_id: UUID
    quantity: float
    required_date: str | None = None


class PriorityNettingRequest(BaseModel):
    product_id: UUID
    demands: list[dict]
    time_bucket_days: int = 30


class RuleBasedAtpRequest(BaseModel):
    product_id: UUID
    quantity: float
    required_date: str
    delay_buffer_days: float = 1.5


class ProbabilisticAtpRequest(BaseModel):
    mo: dict
    components: list[dict]
    priority_queue: list[dict] = []
    required_start: str
    num_simulations: int = 5000


class SupplierPredictRequest(BaseModel):
    supplier_id: UUID | None = None


@router.post("/check-availability")
async def check_material_availability(
    req: AvailabilityRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        required_date = datetime.fromisoformat(req.required_date)
    except ValueError:
        return APIResponse(success=False, data=None, error={"code": "INVALID_DATE", "message": "Invalid date format"})
    result = await simulate_atp(
        session, UUID(tenant_id), req.product_id, req.quantity, required_date
    )

    await kafka_producer.send_event(
        "inventory", "changed",
        key=str(req.product_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.inventory.changed",
            source="mat-svc",
            tenant_id=UUID(tenant_id),
            timestamp=datetime.now(UTC),
            data={
                "product_id": str(req.product_id),
                "quantity": req.quantity,
                "required_date": req.required_date,
                "availability_p90": result.get("availability_p90"),
                "is_available": result.get("is_available", False),
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data=result, error=None)


@router.post("/netting")
async def material_netting(
    req: NettingRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    required_date = datetime.fromisoformat(req.required_date) if req.required_date else None
    result = await cumulative_netting(
        session, UUID(tenant_id), req.product_id, req.quantity, required_date
    )
    return APIResponse(success=True, data=result, error=None)


@router.post("/priority-netting")
async def material_priority_netting(
    req: PriorityNettingRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    result = await priority_weighted_netting(
        session,
        UUID(tenant_id),
        req.product_id,
        req.demands,
        time_bucket_days=req.time_bucket_days,
    )
    return APIResponse(success=True, data=result, error=None)


@router.post("/check-availability-rule")
async def check_material_availability_rule(
    req: RuleBasedAtpRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        required_date = datetime.fromisoformat(req.required_date)
    except ValueError:
        return APIResponse(success=False, data=None, error={"code": "INVALID_DATE", "message": "Invalid date format"})
    result = await rule_based_atp(
        session,
        UUID(tenant_id),
        req.product_id,
        req.quantity,
        required_date,
        delay_buffer_days=req.delay_buffer_days,
    )
    return APIResponse(success=True, data=result, error=None)


@router.post("/probabilistic-atp")
async def check_probabilistic_atp(
    req: ProbabilisticAtpRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        required_start = datetime.fromisoformat(req.required_start)
    except ValueError:
        return APIResponse(success=False, data=None, error={"code": "INVALID_DATE", "message": "Invalid date format"})
    result = await probabilistic_atp(
        session,
        UUID(tenant_id),
        req.mo,
        req.components,
        req.priority_queue,
        required_start,
        num_simulations=req.num_simulations,
    )
    return APIResponse(success=True, data=result, error=None)


@router.post("/supplier-predict")
async def supplier_delay_prediction(
    req: SupplierPredictRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    from sqlalchemy import select as sa_select

    from ipe_shared.models.supplier import Supplier

    if req.supplier_id:
        result = await session.execute(
            sa_select(Supplier).where(
                Supplier.tenant_id == UUID(tenant_id),
                Supplier.id == req.supplier_id,
            )
        )
        supplier = result.scalar_one_or_none()
        if not supplier:
            return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Supplier not found"})
        suppliers = [supplier]
    else:
        result = await session.execute(
            sa_select(Supplier).where(Supplier.tenant_id == UUID(tenant_id))
        )
        suppliers = list(result.scalars().all())

    predictions = []
    for s in suppliers:
        pred = predict_delay(
            avg_delay_days=s.avg_delay_days,
            delay_std_dev_days=s.delay_std_dev_days,
            reliability_score=s.reliability_score,
            distribution_type=s.delay_distribution_type or "normal",
            distribution_params=s.delay_distribution_params,
        )
        predictions.append({
            "supplier_id": str(s.id),
            "supplier_name": s.name,
            "reliability_score": float(s.reliability_score) if s.reliability_score else None,
            **pred,
        })

    return APIResponse(success=True, data={"predictions": predictions}, error=None)
