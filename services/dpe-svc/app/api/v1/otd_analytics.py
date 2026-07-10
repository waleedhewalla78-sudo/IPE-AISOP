"""Nested OTD analytics routes (W1-07 / Sprint S6)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chaos_cost import aggregate_chaos_cost
from app.core.otd_aggregation import (
    compute_baseline_comparison,
    compute_otd_kpis,
    compute_otd_trend,
    compute_root_cause,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/otd", tags=["otd-analytics"])


def _parse_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _tenant_or_error():
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return None, APIResponse(
            success=False,
            data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )
    return UUID(tenant_id), None


@router.get("/kpis")
async def get_otd_kpis(
    range: str = Query(default="30d", alias="range"),
    supplier_id: str | None = Query(default=None),
    line_id: str | None = Query(default=None),
    region_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive"])),
):
    """W1-07: Five KPI aggregation with optional dimensional filters."""
    tid, err = _tenant_or_error()
    if err:
        return err

    from app.core.otd_aggregation import _parse_range_days

    data = await compute_otd_kpis(
        session,
        tid,
        lookback_days=_parse_range_days(range),
        supplier_id=_parse_uuid(supplier_id),
        line_id=_parse_uuid(line_id),
        region_id=_parse_uuid(region_id),
    )
    return APIResponse(success=True, data=data, error=None)


@router.get("/trend")
async def get_otd_trend(
    period: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
    range: str = Query(default="30d", alias="range"),
    supplier_id: str | None = Query(default=None),
    line_id: str | None = Query(default=None),
    region_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err

    points = await compute_otd_trend(
        session,
        tid,
        period=period,
        range_param=range,
        supplier_id=_parse_uuid(supplier_id),
        line_id=_parse_uuid(line_id),
        region_id=_parse_uuid(region_id),
    )
    return APIResponse(
        success=True,
        data={"period": period, "range": range, "points": points},
        error=None,
    )


@router.get("/root-cause")
async def get_otd_root_cause(
    range: str = Query(default="30d", alias="range"),
    supplier_id: str | None = Query(default=None),
    line_id: str | None = Query(default=None),
    region_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err

    data = await compute_root_cause(
        session,
        tid,
        range_param=range,
        supplier_id=_parse_uuid(supplier_id),
        line_id=_parse_uuid(line_id),
        region_id=_parse_uuid(region_id),
    )
    return APIResponse(success=True, data=data, error=None)


@router.get("/cost-of-chaos")
async def get_otd_cost_of_chaos(
    range: str = Query(default="30d", alias="range"),
    category: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive", "cfo"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err

    from app.core.otd_aggregation import _parse_range_days

    period_days = _parse_range_days(range)
    period_key = "7d" if period_days <= 7 else "30d"
    data = await aggregate_chaos_cost(session, tid, period_days=period_days, category_filter=category)
    data["period"] = period_key
    data["range"] = range
    return APIResponse(success=True, data=data, error=None)


@router.get("/baseline")
async def get_otd_baseline(
    lookback_days: int = Query(default=30, ge=7, le=365),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err

    data = await compute_baseline_comparison(session, tid, lookback_days=lookback_days)
    return APIResponse(success=True, data=data, error=None)
