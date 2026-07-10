from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.forecast_quality import ForecastQualityEngine
from app.schemas.forecast_quality import ForecastErrorCalculateRequest, ForecastSnapshotCreateRequest
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse


router = APIRouter(prefix="/demand", tags=["forecast-quality"])
engine = ForecastQualityEngine()


def _serialize_row(row) -> dict:
    return {
        column.name: (str(value) if isinstance(value, UUID) else value.isoformat() if hasattr(value, "isoformat") else value)
        for column in row.__table__.columns
        if (value := getattr(row, column.name)) is not None
    }


@router.post("/snapshot/create")
async def create_snapshot(
    req: ForecastSnapshotCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    row = await engine.create_snapshot(
        session=session,
        tenant_id=tenant_ctx.get(),
        product_id=req.product_id,
        location_id=req.location_id,
        snapshot_date=req.snapshot_date,
        target_period_start=req.target_period_start,
        target_period_type=req.target_period_type,
        forecast_qty=req.forecast_qty,
        forecast_source=req.forecast_source,
        model_id=req.model_id,
        model_version=req.model_version,
    )
    return APIResponse(success=True, data={"snapshot": _serialize_row(row)}, error=None)


@router.post("/error/calculate")
async def calculate_error(
    req: ForecastErrorCalculateRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    row = await engine.calculate_error(
        session=session,
        tenant_id=tenant_ctx.get(),
        product_id=req.product_id,
        location_id=req.location_id,
        period_start=req.period_start,
        period_type=req.period_type,
        lag_periods=req.lag_periods,
        forecast_source=req.forecast_source,
        forecast_qty=req.forecast_qty,
        actuals_qty=req.actuals_qty,
        history=req.history,
    )
    return APIResponse(success=True, data={"error": _serialize_row(row)}, error=None)


@router.get("/error/mape")
async def get_mape(
    product_id: UUID | None = Query(default=None),
    forecast_source: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    metric = await engine.get_metric(
        "mape",
        session=session,
        tenant_id=tenant_ctx.get(),
        product_id=product_id,
        forecast_source=forecast_source,
    )
    return APIResponse(success=True, data=metric, error=None)


@router.get("/error/bias")
async def get_bias(
    product_id: UUID | None = Query(default=None),
    forecast_source: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    metric = await engine.get_metric(
        "bias",
        session=session,
        tenant_id=tenant_ctx.get(),
        product_id=product_id,
        forecast_source=forecast_source,
    )
    return APIResponse(success=True, data=metric, error=None)


@router.get("/error/mase")
async def get_mase(
    product_id: UUID | None = Query(default=None),
    forecast_source: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    metric = await engine.get_metric(
        "mase",
        session=session,
        tenant_id=tenant_ctx.get(),
        product_id=product_id,
        forecast_source=forecast_source,
    )
    return APIResponse(success=True, data=metric, error=None)


@router.get("/error/stability")
async def get_stability(
    product_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    metric = await engine.get_stability(session=session, tenant_id=tenant_ctx.get(), product_id=product_id)
    return APIResponse(success=True, data=metric, error=None)


@router.get("/error/value-add")
async def get_value_add(
    product_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    metric = await engine.get_value_add(session=session, tenant_id=tenant_ctx.get(), product_id=product_id)
    return APIResponse(success=True, data=metric, error=None)
