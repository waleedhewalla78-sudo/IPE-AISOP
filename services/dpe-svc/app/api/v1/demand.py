from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.priority import compute_priority_score
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.product import Product
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/demand", tags=["demand"])


class ClassifyRequest(BaseModel):
    demand_line_ids: list[UUID] | None = None


async def _get_tenant_config(session: AsyncSession, tenant_id: str) -> dict:
    result = await session.execute(sa_select(Tenant.config).where(Tenant.id == tenant_id))
    row = result.fetchone()
    if row and row[0]:
        return dict(row[0])
    return {}


async def _classify_demand_line(session: AsyncSession, dl_id: UUID, tenant_config: dict) -> dict:
    result = await session.execute(
        sa_select(DemandLine, Product)
        .join(Product, DemandLine.product_id == Product.id)
        .where(DemandLine.id == dl_id)
    )
    row = result.one_or_none()
    if not row:
        return {"demand_line_id": str(dl_id), "error": "NOT_FOUND"}

    demand_line, product = row

    dl_dict = {
        "customer_tier": int(demand_line.customer_tier) if demand_line.customer_tier else 3,
        "margin_pct": float(demand_line.margin_pct) if demand_line.margin_pct else 0,
        "required_date": demand_line.required_date,
        "penalty_cost": float(demand_line.penalty_cost) if demand_line.penalty_cost else 0,
        "tags": product.category_tags or [],
    }

    priority = compute_priority_score(dl_dict, tenant_config=tenant_config)

    demand_line.priority_score = priority["priority_score"]
    await session.flush()

    envelope = kafka_producer.build_envelope(
        event_type="ipe.demand.classified",
        tenant_id=str(tenant_ctx.get()),
        payload={
            "demand_line_id": str(dl_id),
            "mo_id": str(demand_line.mo_id) if demand_line.mo_id else "",
            "priority_score": priority["priority_score"],
        },
    )

    await kafka_producer.send_avro(
        topic="ipe.demand.classified",
        key=str(dl_id),
        envelope=envelope,
    )

    return {
        "demand_line_id": str(dl_id),
        "priority_score": priority["priority_score"],
        "priority_breakdown": priority["priority_breakdown"],
    }


@router.post("/classify")
async def classify_demand(
    req: ClassifyRequest = None,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"}
        )

    tenant_config = await _get_tenant_config(session, tenant_id)

    if req and req.demand_line_ids:
        dl_ids = req.demand_line_ids
    else:
        result = await session.execute(
            sa_select(DemandLine.id)
            .where(DemandLine.tenant_id == UUID(tenant_id), DemandLine.status == "new")
            .order_by(DemandLine.created_at.asc())
        )
        dl_ids = [row[0] for row in result.fetchall()]

    results = []
    for dl_id in dl_ids:
        result = await _classify_demand_line(session, dl_id, tenant_config)
        results.append(result)

    await session.commit()

    avg_score = sum(r.get("priority_score", 0) for r in results) / max(1, len(results)) if results else 0.0
    weights_used = tenant_config.get("priority_weights", {}) if tenant_config else {}

    xai = XAIExplanation(
        constraints=["priority_weight_normalization"] + ([k for k, v in weights_used.items() if v > 0.5] if weights_used else []),
        assumptions=["default_weights_applied" if not weights_used else "tenant_weights_applied"],
        confidence_score=round(avg_score / 100.0, 4),
        contributing_factors={r.get("demand_line_id", f"line_{i}"): round(r.get("priority_score", 0) / 100.0, 4) for i, r in enumerate(results[:5])} if results else {},
    ).model_dump()

    return APIResponse(success=True, data={"results": results, "xai_explanation": xai}, error=None)


@router.get("/queue")
async def get_demand_queue(
    session: AsyncSession = Depends(get_db_session),
    status: str = "new",
    limit: int = 50,
    offset: int = 0,
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"}
        )

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
