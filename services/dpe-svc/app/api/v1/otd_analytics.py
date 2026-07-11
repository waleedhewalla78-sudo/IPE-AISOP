"""Nested OTD analytics routes (W1-07 Sprint 4 / Sprint S6)."""

from __future__ import annotations

from datetime import date as Date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chaos_cost import aggregate_chaos_cost
from app.core.otd_aggregation import (
    compute_baseline_comparison,
    compute_otd_kpis,
    compute_otd_trend,
    compute_root_cause,
)
from app.core.otd_aggregator import otd_aggregator
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/otd", tags=["otd-analytics"])


class SnapshotRequest(BaseModel):
    # Field name `date` must not shadow datetime.date in annotations
    date: Optional[Date] = None


class BackfillRequest(BaseModel):
    months_back: int = Field(default=6, ge=1, le=24)


def _parse_uuid(value: Optional[str]) -> Optional[UUID]:
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


def _range_days(range_param: str | int) -> int:
    if isinstance(range_param, int):
        return max(1, min(365, range_param))
    from app.core.otd_aggregation import _parse_range_days

    return _parse_range_days(str(range_param))


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

    data = await compute_otd_kpis(
        session,
        tid,
        lookback_days=_range_days(range),
        supplier_id=_parse_uuid(supplier_id),
        line_id=_parse_uuid(line_id),
        region_id=_parse_uuid(region_id),
    )
    return APIResponse(success=True, data=data, error=None)


@router.get("/trend")
async def get_otd_trend(
    period: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
    range: str = Query(default="90", alias="range"),
    supplier_id: str | None = Query(default=None),
    line_id: str | None = Query(default=None),
    region_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err

    range_days = _range_days(range if range.endswith("d") else f"{range}d")
    points = await compute_otd_trend(
        session,
        tid,
        period=period,
        range_param=f"{range_days}d",
        supplier_id=_parse_uuid(supplier_id),
        line_id=_parse_uuid(line_id),
        region_id=_parse_uuid(region_id),
    )
    baseline = await compute_baseline_comparison(session, tid, lookback_days=range_days)
    current_otd = None
    if points:
        current_otd = points[-1].get("otd_pct")
    baseline_pct = None
    if isinstance(baseline.get("baseline"), dict):
        baseline_pct = baseline["baseline"].get("otd_pct")
    improvement = baseline.get("improvement_pct")
    data_points = [
        {
            "date": p.get("period_start"),
            "otd_pct": p.get("otd_pct"),
            "total": p.get("completed_mos", 0),
            "on_time": p.get("on_time_mos", 0),
            "late": max(0, int(p.get("completed_mos") or 0) - int(p.get("on_time_mos") or 0)),
            **p,
        }
        for p in points
    ]
    return APIResponse(
        success=True,
        data={
            "period": period,
            "range": range,
            "current_otd_pct": current_otd,
            "baseline_otd_pct": baseline_pct,
            "improvement_pct": improvement,
            "data": data_points,
            "points": points,
        },
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
    """Legacy list shape used by existing dashboard UI."""
    tid, err = _tenant_or_error()
    if err:
        return err

    range_days = _range_days(range if str(range).endswith("d") else f"{range}d")
    data = await compute_root_cause(
        session,
        tid,
        range_param=f"{range_days}d",
        supplier_id=_parse_uuid(supplier_id),
        line_id=_parse_uuid(line_id),
        region_id=_parse_uuid(region_id),
    )
    return APIResponse(success=True, data=data, error=None)


@router.get("/root-causes")
async def get_otd_root_causes(
    range: str = Query(default="30", alias="range"),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive"])),
):
    """Sprint 4 Wave 1 shape: { total_late, causes: [...] }."""
    tid, err = _tenant_or_error()
    if err:
        return err

    range_days = _range_days(range if str(range).endswith("d") else f"{range}d")
    causes = await otd_aggregator.get_root_causes(session, tid, range_days=range_days)
    total_late = sum(int(c.get("count") or 0) for c in causes)
    return APIResponse(
        success=True,
        data={"total_late": total_late, "causes": causes},
        error=None,
    )


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

    period_days = _range_days(range)
    period_key = "7d" if period_days <= 7 else "30d"
    data = await aggregate_chaos_cost(session, tid, period_days=period_days, category_filter=category)
    shaped = await otd_aggregator.get_cost_of_chaos(session, tid, range_days=period_days)
    data["period"] = period_key
    data["range"] = range
    data.update(shaped)
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


@router.get("/summary")
async def get_otd_summary(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err
    data = await otd_aggregator.get_summary(session, tid)
    return APIResponse(success=True, data=data, error=None)


@router.post("/snapshot")
async def post_otd_snapshot(
    body: Optional[SnapshotRequest] = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err
    payload = body or SnapshotRequest()
    data = await otd_aggregator.capture_daily_snapshot(session, tid, payload.date)
    return APIResponse(success=True, data=data, error=None)


@router.post("/backfill")
async def post_otd_backfill(
    body: Optional[BackfillRequest] = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin"])),
):
    tid, err = _tenant_or_error()
    if err:
        return err
    payload = body or BackfillRequest()
    data = await otd_aggregator.capture_historical(session, tid, months_back=payload.months_back)
    return APIResponse(success=True, data=data, error=None)
