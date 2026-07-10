"""ABC/XYZ segmentation API."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.segmentation import SegmentationEngine
from app.schemas.segmentation import SegmentationConfigUpdate, SegmentationRunRequest
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.planning_intelligence import ProductSegment
from ipe_shared.models.product import Product
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/material/segmentation", tags=["material-segmentation"])


def _no_tenant_response() -> APIResponse:
    return APIResponse(
        success=False,
        data=None,
        error={"code": "NO_TENANT", "message": "No tenant context"},
    )


def _segment_to_dict(segment: ProductSegment, product: Product | None = None) -> dict:
    return {
        "product_id": str(segment.product_id),
        "product_name": product.name if product else None,
        "internal_ref": product.internal_ref if product else None,
        "segmentation_date": segment.segmentation_date.isoformat(),
        "abc_class": segment.abc_class,
        "xyz_class": segment.xyz_class,
        "combined_segment": segment.combined_segment,
        "target_service_level_pct": float(segment.target_service_level_pct or 0),
        "forecast_model_recommendation": segment.forecast_model_recommendation,
        "review_frequency": segment.review_frequency,
        "revenue_total": float(segment.revenue_total or 0),
        "revenue_share_pct": float(segment.revenue_share_pct or 0),
        "cumulative_revenue_pct": float(segment.cumulative_revenue_pct or 0),
        "demand_mean": float(segment.demand_mean or 0),
        "demand_stddev": float(segment.demand_stddev or 0),
        "demand_cv": float(segment.demand_cv) if segment.demand_cv is not None else None,
    }


@router.post("/run")
async def run_segmentation(
    req: SegmentationRunRequest | None = None,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    overrides = (
        req.config_overrides.model_dump(exclude_none=True)
        if req and req.config_overrides
        else None
    )
    result = await SegmentationEngine().run_segmentation(session, UUID(tenant_id), overrides)
    return APIResponse(success=True, data=result, error=None)


@router.get("/results")
async def get_segmentation_results(
    product_id: UUID | None = Query(default=None),
    abc_class: str | None = Query(default=None, min_length=1, max_length=1),
    xyz_class: str | None = Query(default=None, min_length=1, max_length=1),
    current_user=Depends(require_roles(["admin", "planner", "manager", "auditor"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    latest_date_subquery = (
        select(func.max(ProductSegment.segmentation_date))
        .where(ProductSegment.tenant_id == UUID(tenant_id))
        .scalar_subquery()
    )
    stmt = (
        select(ProductSegment, Product)
        .outerjoin(Product, Product.id == ProductSegment.product_id)
        .where(
            ProductSegment.tenant_id == UUID(tenant_id),
            ProductSegment.segmentation_date == latest_date_subquery,
        )
        .order_by(ProductSegment.abc_class, ProductSegment.xyz_class, Product.name)
    )
    if product_id:
        stmt = stmt.where(ProductSegment.product_id == product_id)
    if abc_class:
        stmt = stmt.where(ProductSegment.abc_class == abc_class.upper())
    if xyz_class:
        stmt = stmt.where(ProductSegment.xyz_class == xyz_class.upper())

    rows = (await session.execute(stmt)).all()
    items = [_segment_to_dict(segment, product) for segment, product in rows]
    return APIResponse(success=True, data={"count": len(items), "items": items}, error=None)


@router.get("/summary")
async def get_segmentation_summary(
    current_user=Depends(require_roles(["admin", "planner", "manager", "auditor"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    latest_date = (
        await session.execute(
            select(func.max(ProductSegment.segmentation_date)).where(
                ProductSegment.tenant_id == UUID(tenant_id)
            )
        )
    ).scalar_one_or_none()
    if latest_date is None:
        return APIResponse(
            success=True,
            data={
                "segmentation_date": None,
                "total_products": 0,
                "abc": {},
                "xyz": {},
                "segments": {},
            },
            error=None,
        )

    rows = (
        await session.execute(
            select(ProductSegment).where(
                ProductSegment.tenant_id == UUID(tenant_id),
                ProductSegment.segmentation_date == latest_date,
            )
        )
    ).scalars().all()
    abc_counts = {"A": 0, "B": 0, "C": 0}
    xyz_counts = {"X": 0, "Y": 0, "Z": 0}
    segment_counts: dict[str, int] = {}
    for row in rows:
        abc_counts[row.abc_class] = abc_counts.get(row.abc_class, 0) + 1
        xyz_counts[row.xyz_class] = xyz_counts.get(row.xyz_class, 0) + 1
        segment_counts[row.combined_segment] = segment_counts.get(row.combined_segment, 0) + 1

    return APIResponse(
        success=True,
        data={
            "segmentation_date": latest_date.isoformat(),
            "total_products": len(rows),
            "abc": abc_counts,
            "xyz": xyz_counts,
            "segments": segment_counts,
        },
        error=None,
    )


@router.get("/config")
async def get_segmentation_config(
    current_user=Depends(require_roles(["admin", "planner", "manager", "auditor"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    config = await SegmentationEngine().get_config(session, UUID(tenant_id))
    return APIResponse(success=True, data=config, error=None)


@router.put("/config")
async def update_segmentation_config(
    req: SegmentationConfigUpdate,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    config = await SegmentationEngine().update_config(
        session,
        UUID(tenant_id),
        req.model_dump(exclude_none=True),
    )
    return APIResponse(success=True, data=config, error=None)
