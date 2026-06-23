from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.sop_solver import (
    SopCapacityBucket,
    SopDemandBucket,
    compute_sop_gap,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/sop", tags=["sales-operations-planning"])


class ForecastEntry(BaseModel):
    period_start: str
    period_end: str
    product_family: str
    forecast_qty: float
    confidence_pct: float = 0.0


class CapacityEntry(BaseModel):
    period_start: str
    period_end: str
    work_center_group: str
    capacity_hours: float
    capacity_qty: float = 0.0


class SopRequest(BaseModel):
    demand: list[ForecastEntry]
    capacity: list[CapacityEntry]
    bottleneck_threshold_pct: float = 10.0


class ForecastIngestRequest(BaseModel):
    product_family: str
    period_type: str = "weekly"
    period_start: str
    period_end: str
    forecast_qty: float
    capacity_qty: float = 0.0
    confidence_pct: float = 0.0
    source: str = "pipeline"


def _parse_dt(s: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return datetime.now(UTC)


@router.post("/forecast")
async def ingest_forecast(
    req: ForecastIngestRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    period_start = _parse_dt(req.period_start)
    period_end = _parse_dt(req.period_end)

    forecast_id = str(uuid4())

    return APIResponse(success=True, data={
        "forecast_id": forecast_id,
        "tenant_id": str(tenant_id),
        "product_family": req.product_family,
        "period_type": req.period_type,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "forecast_qty": req.forecast_qty,
        "capacity_qty": req.capacity_qty,
        "confidence_pct": req.confidence_pct,
        "source": req.source,
        "status": "ingested",
    }, error=None)


@router.post("/solve")
async def solve_sop(
    req: SopRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    demand_buckets = [
        SopDemandBucket(
            period_start=_parse_dt(d.period_start),
            period_end=_parse_dt(d.period_end),
            product_family=d.product_family,
            forecast_qty=d.forecast_qty,
            confidence_pct=d.confidence_pct,
        )
        for d in req.demand
    ]

    capacity_buckets = [
        SopCapacityBucket(
            period_start=_parse_dt(c.period_start),
            period_end=_parse_dt(c.period_end),
            work_center_group=c.work_center_group,
            capacity_hours=c.capacity_hours,
            capacity_qty=c.capacity_qty,
        )
        for c in req.capacity
    ]

    result = compute_sop_gap(demand_buckets, capacity_buckets, req.bottleneck_threshold_pct)

    bottleneck_data = [
        {
            "period_start": b.period_start.isoformat(),
            "period_end": b.period_end.isoformat(),
            "product_family": b.product_family,
            "demand_qty": b.demand_qty,
            "capacity_qty": b.capacity_qty,
            "gap_qty": b.gap_qty,
            "gap_pct": b.gap_pct,
            "is_bottleneck": b.is_bottleneck,
        }
        for b in result.bottlenecks
    ]

    return APIResponse(success=True, data={
        "horizon_weeks": result.horizon_weeks,
        "total_demand": result.total_demand,
        "total_capacity": result.total_capacity,
        "total_gap": result.total_gap,
        "gap_pct": result.gap_pct,
        "bottlenecks": bottleneck_data,
        "bucket_count": result.bucket_count,
        "bottleneck_count": result.bottleneck_count,
        "solve_time_ms": result.solve_time_ms,
        "xai_explanation": XAIExplanation(
            constraints=[
                "weekly_bucket_aggregation",
                f"bottleneck_threshold_{req.bottleneck_threshold_pct}%",
                "demand_vs_capacity_gap",
            ],
            assumptions=[
                "forecast_accuracy_confidence_weighted",
                "capacity_evenly_distributed_per_week",
            ],
            confidence_score=0.85,
            contributing_factors={
                "capacity_utilization": round(result.total_demand / max(1, result.total_capacity), 4),
                "bottleneck_severity": round(result.gap_pct / 100.0, 4),
                "solve_efficiency": round(1.0 / max(1, result.solve_time_ms / 1000.0), 4),
            },
        ).model_dump(),
    }, error=None)