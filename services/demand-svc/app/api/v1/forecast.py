from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.forecaster import STANDARD_HORIZONS, forecast_dates, mape, simple_exponential_smoothing
from app.core.forecaster_factory import forecast_with_factory
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.v8_planning import DemandForecast, DemandSignal
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/demand", tags=["demand-forecast"])


class SignalIngestItem(BaseModel):
    source_type: str
    source_id: str | None = None
    product_id: UUID | None = None
    signal_ts: datetime
    value: float
    quality_score: float = 1.0


class SignalIngestRequest(BaseModel):
    signals: list[SignalIngestItem]


class ForecastAdjustRequest(BaseModel):
    value: float
    reason_code: str = Field(min_length=3, max_length=256)


class SenseRequest(BaseModel):
    product_ids: list[UUID] | None = None
    horizon: str = "short"
    periods: int | None = Field(default=None, ge=1, le=90)
    days: int | None = Field(default=None, description="Forecast horizon in days (7, 14, or 30)")


def _normalize_days(days: int | None, periods: int | None = None) -> int:
    if days is not None:
        if days not in STANDARD_HORIZONS:
            return settings.DEMAND_FORECAST_HORIZON_DAYS
        return days
    if periods is not None and periods in STANDARD_HORIZONS:
        return periods
    return settings.DEMAND_FORECAST_HORIZON_DAYS


async def _history_for_product(session: AsyncSession, tenant_id: str, product_id: UUID) -> list[float]:
    result = await session.execute(
        select(DemandLine.quantity)
        .where(DemandLine.tenant_id == tenant_id, DemandLine.product_id == product_id)
        .order_by(DemandLine.required_date.asc())
        .limit(52)
    )
    rows = result.scalars().all()
    return [float(q) for q in rows if q is not None]


def _serialize_forecast_point(
    *,
    product_id: UUID,
    fdate: datetime,
    point: dict[str, float],
    model_version: str,
    horizon_days: int,
    forecast_id: str | None = None,
) -> dict:
    return {
        "id": forecast_id,
        "product_id": str(product_id),
        "horizon_days": horizon_days,
        "forecast_date": fdate.isoformat(),
        "value": point["value"],
        "lower_bound": point["lower"],
        "upper_bound": point["upper"],
        "model_version": model_version,
    }


async def _compute_live_forecast(
    session: AsyncSession,
    tenant_id: str,
    product_id: UUID,
    days: int,
) -> list[dict]:
    history = await _history_for_product(session, tenant_id, product_id)
    if not history:
        history = [10.0, 12.0, 11.0, 13.0, 12.0]
    points, model_version = forecast_with_factory(
        history,
        days,
        model=settings.DEMAND_FORECAST_MODEL,
    )
    start = datetime.now(UTC)
    dates = forecast_dates(start, days, horizon="short")
    return [
        _serialize_forecast_point(
            product_id=product_id,
            fdate=fdate,
            point=point,
            model_version=model_version,
            horizon_days=days,
        )
        for point, fdate in zip(points, dates, strict=True)
    ]


@router.get("/forecast")
async def get_forecast(
    product_id: UUID | None = Query(default=None),
    horizon: str = Query(default="short", pattern="^(short|medium)$"),
    days: int | None = Query(default=None, description="7, 14, or 30 day horizon"),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    horizon_days = _normalize_days(days)

    if product_id:
        live = await _compute_live_forecast(session, tenant_id, product_id, horizon_days)
        return APIResponse(
            success=True,
            data={"forecasts": live, "source": "cdm_demand_line", "horizon_days": horizon_days},
            error=None,
        )

    stmt = select(DemandForecast).where(
        DemandForecast.tenant_id == tenant_id,
        DemandForecast.horizon_type == horizon,
    )
    stmt = stmt.order_by(DemandForecast.forecast_date.asc()).limit(500)
    result = await session.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        pid_result = await session.execute(
            select(DemandLine.product_id)
            .where(DemandLine.tenant_id == tenant_id)
            .group_by(DemandLine.product_id)
            .limit(5)
        )
        product_ids = [row[0] for row in pid_result.all()]
        live_all: list[dict] = []
        for pid in product_ids:
            live_all.extend(await _compute_live_forecast(session, tenant_id, pid, horizon_days))
        return APIResponse(
            success=True,
            data={
                "forecasts": live_all,
                "source": "cdm_demand_line",
                "horizon_days": horizon_days,
            },
            error=None,
        )

    return APIResponse(
        success=True,
        data={
            "forecasts": [
                {
                    "id": str(r.id),
                    "product_id": str(r.product_id),
                    "horizon_type": r.horizon_type,
                    "horizon_days": horizon_days,
                    "forecast_date": r.forecast_date.isoformat(),
                    "value": float(r.value),
                    "lower_bound": float(r.lower_bound) if r.lower_bound is not None else None,
                    "upper_bound": float(r.upper_bound) if r.upper_bound is not None else None,
                    "model_version": r.model_version,
                }
                for r in rows
            ],
            "source": "cdm_demand_forecast",
            "horizon_days": horizon_days,
        },
        error=None,
    )


@router.post("/sense")
async def run_demand_sense(
    req: SenseRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    product_ids = req.product_ids
    if not product_ids:
        pid_result = await session.execute(
            select(DemandLine.product_id)
            .where(DemandLine.tenant_id == tenant_id)
            .group_by(DemandLine.product_id)
            .limit(50)
        )
        product_ids = [row[0] for row in pid_result.all()]

    horizon_days = _normalize_days(req.days, req.periods)
    created = 0
    start = datetime.now(UTC)
    for pid in product_ids:
        history = await _history_for_product(session, tenant_id, pid)
        if not history:
            history = [10.0, 12.0, 11.0, 13.0]
        points, model_version = forecast_with_factory(
            history,
            horizon_days,
            model=settings.DEMAND_FORECAST_MODEL,
        )
        dates = forecast_dates(start, horizon_days, horizon=req.horizon)
        for point, fdate in zip(points, dates, strict=True):
            session.add(
                DemandForecast(
                    tenant_id=tenant_id,
                    product_id=pid,
                    horizon_type=req.horizon,
                    forecast_date=fdate,
                    value=point["value"],
                    lower_bound=point["lower"],
                    upper_bound=point["upper"],
                    model_version=model_version,
                )
            )
            created += 1
    await session.commit()
    return APIResponse(
        success=True,
        data={
            "products_processed": len(product_ids),
            "forecasts_created": created,
            "horizon_days": horizon_days,
            "model": settings.DEMAND_FORECAST_MODEL,
        },
        error=None,
    )


@router.post("/signal/ingest")
async def ingest_signals(
    req: SignalIngestRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    for item in req.signals:
        session.add(
            DemandSignal(
                tenant_id=tenant_id,
                source_type=item.source_type,
                source_id=item.source_id,
                product_id=item.product_id,
                signal_ts=item.signal_ts,
                value=item.value,
                quality_score=item.quality_score,
            )
        )
    await session.commit()
    return APIResponse(success=True, data={"ingested": len(req.signals)}, error=None)


@router.put("/forecast/{forecast_id}/adjust")
async def adjust_forecast(
    forecast_id: UUID,
    req: ForecastAdjustRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    row = await session.get(DemandForecast, forecast_id)
    if not row or str(row.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Forecast not found"})
    row.value = req.value
    row.model_version = f"manual:{req.reason_code[:32]}"
    await session.commit()
    return APIResponse(success=True, data={"forecast_id": str(forecast_id), "value": req.value}, error=None)


@router.get("/accuracy")
async def forecast_accuracy(
    product_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    if product_id:
        history = await _history_for_product(session, tenant_id, product_id)
        predicted = [simple_exponential_smoothing(history[: i + 1]) for i in range(len(history))]
        score = mape(history[1:], predicted[1:]) if len(history) > 1 else None
        return APIResponse(
            success=True,
            data={
                "product_id": str(product_id),
                "mape_pct": score,
                "sample_size": len(history),
                "model": settings.DEMAND_FORECAST_MODEL,
            },
            error=None,
        )

    count_result = await session.execute(
        select(func.count(DemandForecast.id)).where(DemandForecast.tenant_id == tenant_id)
    )
    total = count_result.scalar() or 0
    return APIResponse(
        success=True,
        data={
            "tenant_mape_pct": None,
            "forecast_rows": total,
            "model": settings.DEMAND_FORECAST_MODEL,
            "note": "Provide product_id for MAPE",
        },
        error=None,
    )
