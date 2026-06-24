from uuid import UUID
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.priority import compute_priority_score
from app.core.margin_priority import compute_margin_priorities_for_mos
from app.core.tariff_shock import get_tariff_exposure, run_tariff_shock
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


class TariffShockRequest(BaseModel):
    region: str
    tariff_delta_pct: float
    margin_threshold_pct: float = 15.0


class SubstituteDraftRequest(BaseModel):
    mo_id: UUID
    from_material_id: UUID
    to_material_id: UUID


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


@router.get("/priority/margin-aware")
async def get_margin_aware_priority(
    session: AsyncSession = Depends(get_db_session),
    mo_ids: str | None = None,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"}
        )

    parsed_mo_ids: list[UUID] | None = None
    if mo_ids:
        parsed_mo_ids = [UUID(x.strip()) for x in mo_ids.split(",") if x.strip()]

    priorities, warnings = await compute_margin_priorities_for_mos(
        session, UUID(tenant_id), parsed_mo_ids
    )

    return APIResponse(
        success=True,
        data={
            "priorities": [
                {
                    "mo_id": p.mo_id,
                    "base_priority_score": p.base_priority_score,
                    "margin_adjusted_score": p.margin_adjusted_score,
                    "net_margin_usd": p.net_margin_usd,
                    "activity_overhead_usd": p.activity_overhead_usd,
                    "data_quality": p.data_quality,
                }
                for p in priorities
            ],
            "warnings": warnings,
        },
        error=None,
    )


@router.post("/tariff/shock")
async def post_tariff_shock(
    req: TariffShockRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles(["admin", "planner"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"}
        )

    result = await run_tariff_shock(
        session,
        UUID(tenant_id),
        region=req.region,
        tariff_delta_pct=req.tariff_delta_pct,
        margin_threshold_pct=req.margin_threshold_pct,
    )

    envelope = kafka_producer.build_envelope(
        event_type="ipe.tariff.shock",
        tenant_id=tenant_id,
        payload={
            "region": req.region,
            "delta_pct": req.tariff_delta_pct,
            "affected_mo_ids": result.get("affected_mo_ids", []),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
    await kafka_producer.send_avro(
        topic="ipe.tariff.shock",
        key=tenant_id,
        envelope=envelope,
    )
    await session.commit()

    return APIResponse(success=True, data=result, error=None)


@router.get("/tariff/exposure")
async def get_tariff_exposure_endpoint(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"}
        )

    rows = await get_tariff_exposure(session, UUID(tenant_id))
    return APIResponse(
        success=True,
        data={
            "exposure": [
                {
                    "region": r.region,
                    "material_count": r.material_count,
                    "mo_count": r.mo_count,
                    "total_exposure_usd": r.total_exposure_usd,
                }
                for r in rows
            ]
        },
        error=None,
    )


@router.post("/tariff/substitute-draft")
async def post_substitute_draft(
    req: SubstituteDraftRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles(["admin", "planner"])),
):
    """Enqueue BOM substitution draft for connector — no autonomous ERP write."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"}
        )

    payload = {
        "mo_id": str(req.mo_id),
        "from_material_id": str(req.from_material_id),
        "to_material_id": str(req.to_material_id),
        "status": "pending_approval",
        "requested_by": getattr(current_user, "sub", "planner"),
    }
    await session.execute(
        text("""
            INSERT INTO cdm_export_queue
                (tenant_id, payload, event_type, status, retry_count)
            VALUES
                (:tid, :payload, :evt, 'pending', 0)
        """),
        {
            "tid": UUID(tenant_id),
            "payload": payload,
            "evt": "ipe.tariff.substitute_draft",
        },
    )
    await session.commit()

    return APIResponse(
        success=True,
        data={"draft": payload, "status": "pending_approval"},
        error=None,
    )


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
