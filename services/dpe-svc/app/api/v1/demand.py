from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.classifier import classify_demand_type
from app.core.mdr_engine import build_remediation, calculate_mdr
from app.core.priority import calculate_priority
from fastapi.responses import JSONResponse
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.product import Product
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/demand", tags=["demand"])


class ClassifyRequest(BaseModel):
    demand_line_ids: list[UUID]


async def _get_tenant_config(session: AsyncSession, tenant_id: str) -> dict:
    result = await session.execute(
        sa_select(Tenant.config).where(Tenant.id == tenant_id)
    )
    row = result.fetchone()
    if row and row[0]:
        return dict(row[0])
    return {}


@router.post("/classify")
async def classify_demand(
    req: ClassifyRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    # MDR Gate Check
    mdr = await calculate_mdr(session, tenant_id)
    if not mdr["passed"]:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": {
                    "code": "MDR_GATE_FAILED",
                    "message": "Data quality below minimum threshold for Shadow Mode.",
                },
                "mdr_report": {
                    "bom_completeness_pct": mdr["bom_completeness_pct"],
                    "lead_time_accuracy_pct": mdr["lead_time_accuracy_pct"],
                    "remediation_steps": build_remediation(mdr),
                },
            },
        )

    tenant_config = await _get_tenant_config(session, tenant_id)

    results = []
    for dl_id in req.demand_line_ids:
        result = await session.execute(
            sa_select(DemandLine, Product)
            .join(Product, DemandLine.product_id == Product.id)
            .where(DemandLine.tenant_id == UUID(tenant_id), DemandLine.id == dl_id)
        )
        row = result.one_or_none()
        if not row:
            results.append({"demand_line_id": str(dl_id), "error": "NOT_FOUND"})
            continue

        demand_line, product = row
        classification = classify_demand_type(
            product_data={
                "source_type": product.source_type,
                "lead_time_days": float(product.lead_time_days) if product.lead_time_days else None,
                "safety_stock": float(product.safety_stock) if product.safety_stock else None,
                "demand_cv": float(product.demand_cv) if product.demand_cv else None,
            },
            customer_tier=int(demand_line.customer_tier) if demand_line.customer_tier else None,
        )

        priority = calculate_priority(
            {
                "required_date": demand_line.required_date,
                "customer_tier": int(demand_line.customer_tier) if demand_line.customer_tier else None,
                "penalty_cost": float(demand_line.penalty_cost) if demand_line.penalty_cost else 0,
                "margin_pct": float(demand_line.margin_pct) if demand_line.margin_pct else None,
                "quantity": float(demand_line.quantity),
                "product_id": str(product.id),
            },
            tenant_config=tenant_config,
        )

        demand_line.demand_type = classification["demand_type"]
        demand_line.priority_score = priority["priority_score"]
        await session.flush()

        await kafka_producer.send_event(
            "demand", "classified",
            key=str(dl_id),
            value=EventEnvelope(
                event_id=str(uuid4()),
                event_type="ipe.demand.classified",
                source="dpe-svc",
                tenant_id=UUID(tenant_id),
                timestamp=datetime.now(UTC),
                data={
                    "demand_line_id": str(dl_id),
                    "product_id": str(demand_line.product_id),
                    "demand_type": classification["demand_type"],
                    "priority_score": priority["priority_score"],
                    "priority_breakdown": priority.get("priority_breakdown", {}),
                    "is_urgent": priority.get("is_urgent", False),
                    "composite_score": priority.get("composite_score", 0),
                    "classifier_reason": classification.get("reason", ""),
                },
            ).model_dump(mode="json"),
        )

        results.append({
            "demand_line_id": str(dl_id),
            "demand_type": classification["demand_type"],
            "classification_confidence": classification["confidence"],
            "classification_reason": classification["reason"],
            **priority,
        })

    await session.commit()
    return APIResponse(success=True, data={"results": results}, error=None)


@router.get("/queue")
async def get_demand_queue(
    session: AsyncSession = Depends(get_db_session),
    status: str = "new",
    limit: int = 50,
    offset: int = 0,
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    result = await session.execute(
        sa_select(DemandLine)
        .where(DemandLine.tenant_id == UUID(tenant_id), DemandLine.status == status)
        .order_by(DemandLine.priority_score.desc().nulls_last(), DemandLine.required_date.asc())
        .offset(offset)
        .limit(limit)
    )
    lines = result.scalars().all()
    return APIResponse(
        success=True,
        data={
            "demands": [
                {
                    "id": str(d.id),
                    "product_id": str(d.product_id),
                    "quantity": float(d.quantity),
                    "required_date": d.required_date.isoformat(),
                    "demand_type": d.demand_type,
                    "priority_score": float(d.priority_score) if d.priority_score else None,
                    "status": d.status,
                }
                for d in lines
            ],
            "total": len(lines),
            "offset": offset,
            "limit": limit,
        },
        error=None,
    )
