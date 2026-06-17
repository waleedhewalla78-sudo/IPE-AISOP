from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.reconciliation import analyze_mo_completion
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.work_order import WorkOrder
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


class AnalyzeRequest(BaseModel):
    mo_id: UUID


@router.post("/analyze")
async def analyze(
    req: AnalyzeRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == UUID(tenant_id),
            ManufacturingOrder.id == req.mo_id,
        )
    )
    mo = result.scalar_one_or_none()
    if not mo:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "MO not found"},
        )

    wo_result = await session.execute(
        sa_select(WorkOrder).where(
            WorkOrder.tenant_id == UUID(tenant_id),
            WorkOrder.mo_id == req.mo_id,
        )
    )
    work_orders = list(wo_result.scalars().all())

    analysis = analyze_mo_completion(mo, work_orders)

    await kafka_producer.send_event(
        "reconciliation", "completed",
        key=str(req.mo_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.reconciliation.completed",
            source="rec-svc",
            tenant_id=UUID(tenant_id),
            timestamp=datetime.now(UTC),
            data={
                "mo_id": str(req.mo_id),
                "yield_variance_pct": analysis["yield_variance_pct"],
                "time_variance_pct": analysis["time_variance_pct"],
                "scrap_delta": analysis["scrap_delta"],
                "planned_duration_days": analysis["planned_duration_days"],
                "actual_duration_days": analysis["actual_duration_days"],
                "completed_work_orders": analysis["completed_work_orders"],
                "total_work_orders": analysis["total_work_orders"],
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data=analysis, error=None)
