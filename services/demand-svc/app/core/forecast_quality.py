"""Forecast quality metrics and CDM persistence helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from statistics import mean
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.demand import DemandLine
from ipe_shared.models.planning_intelligence import ForecastError, ForecastSnapshot, ForecastStability


NumberOrSeries = float | int | Sequence[float | int]


def _as_float_pairs(forecast: NumberOrSeries, actuals: NumberOrSeries) -> list[tuple[float, float]]:
    if isinstance(forecast, int | float) and isinstance(actuals, int | float):
        return [(float(forecast), float(actuals))]
    if isinstance(forecast, int | float) or isinstance(actuals, int | float):
        raise TypeError("forecast and actuals must both be scalars or both be sequences")
    return [(float(f), float(a)) for f, a in zip(forecast, actuals, strict=False)]


def mape_from_pair(forecast: NumberOrSeries, actuals: NumberOrSeries) -> float | None:
    """Return MAPE percentage, skipping pairs with zero actuals."""
    components = [abs((f - a) / a) * 100 for f, a in _as_float_pairs(forecast, actuals) if a != 0]
    if not components:
        return None
    return round(mean(components), 4)


def bias_pct_from_pair(forecast: NumberOrSeries, actuals: NumberOrSeries) -> float | None:
    """Return signed forecast bias percentage, skipping pairs with zero actuals."""
    components = [((f - a) / a) * 100 for f, a in _as_float_pairs(forecast, actuals) if a != 0]
    if not components:
        return None
    return round(mean(components), 4)


def naive_mae(series: Sequence[float | int]) -> float | None:
    """Mean absolute one-step naive error for a historical demand series."""
    values = [float(value) for value in series]
    if len(values) < 2:
        return None
    return round(mean(abs(curr - prev) for prev, curr in zip(values, values[1:], strict=False)), 4)


def mase_component(abs_error: float | int, naive_mae_value: float | int | None) -> float | None:
    if naive_mae_value is None or float(naive_mae_value) == 0:
        return None
    return round(float(abs_error) / float(naive_mae_value), 4)


def value_add_pct(stat_mape: float | int | None, final_mape: float | int | None) -> float | None:
    if stat_mape is None or final_mape is None or float(stat_mape) == 0:
        return None
    return round(((float(stat_mape) - float(final_mape)) / float(stat_mape)) * 100, 4)


def stability_change_pct(prior: float | int | None, current: float | int | None) -> float | None:
    if prior is None or current is None or float(prior) == 0:
        return None
    return round(((float(current) - float(prior)) / float(prior)) * 100, 4)


def _period_bounds(period_start: date, period_type: str) -> tuple[datetime, datetime]:
    start = datetime.combine(period_start, time.min, tzinfo=UTC)
    if period_type == "week":
        end = start + timedelta(days=7)
    elif period_type == "day":
        end = start + timedelta(days=1)
    else:
        next_month = period_start.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1)
        end = datetime.combine(end_date, time.min, tzinfo=UTC)
    return start, end


class ForecastQualityEngine:
    """Calculates forecast quality metrics from memory or CDM tables."""

    def calculate_pairs(
        self,
        forecast: Sequence[float | int],
        actuals: Sequence[float | int],
        *,
        history: Sequence[float | int] | None = None,
    ) -> dict[str, Any]:
        pairs = _as_float_pairs(forecast, actuals)
        abs_errors = [abs(f - a) for f, a in pairs]
        naive = naive_mae(history or actuals)
        return {
            "mape_pct": mape_from_pair(forecast, actuals),
            "bias_pct": bias_pct_from_pair(forecast, actuals),
            "mae": round(mean(abs_errors), 4) if abs_errors else None,
            "naive_mae": naive,
            "mase": mase_component(mean(abs_errors), naive) if abs_errors else None,
            "sample_size": len([a for _, a in pairs if a != 0]),
        }

    async def create_snapshot(
        self,
        *,
        session: AsyncSession | None = None,
        tenant_id: str | UUID | None = None,
        product_id: UUID,
        snapshot_date: date,
        target_period_start: date,
        forecast_qty: float,
        forecast_source: str = "statistical",
        target_period_type: str = "month",
        location_id: UUID | None = None,
        model_id: str | None = None,
        model_version: str | None = None,
    ) -> ForecastSnapshot | dict[str, Any]:
        payload = {
            "tenant_id": tenant_id,
            "product_id": product_id,
            "location_id": location_id,
            "snapshot_date": snapshot_date,
            "target_period_start": target_period_start,
            "target_period_type": target_period_type,
            "forecast_qty": forecast_qty,
            "forecast_source": forecast_source,
            "model_id": model_id,
            "model_version": model_version,
        }
        if session is None:
            return payload
        row = ForecastSnapshot(**payload)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    async def calculate_error(
        self,
        *,
        session: AsyncSession | None = None,
        tenant_id: str | UUID | None = None,
        product_id: UUID,
        period_start: date,
        forecast_qty: float | None = None,
        actuals_qty: float | None = None,
        period_type: str = "month",
        lag_periods: int = 1,
        forecast_source: str = "statistical",
        history: Sequence[float | int] | None = None,
        location_id: UUID | None = None,
    ) -> ForecastError | dict[str, Any]:
        if session is not None:
            if forecast_qty is None:
                forecast_qty = await self._latest_snapshot_qty(
                    session=session,
                    tenant_id=tenant_id,
                    product_id=product_id,
                    period_start=period_start,
                    forecast_source=forecast_source,
                )
            if actuals_qty is None:
                actuals_qty = await self._actuals_qty(
                    session=session,
                    tenant_id=tenant_id,
                    product_id=product_id,
                    period_start=period_start,
                    period_type=period_type,
                )

        if forecast_qty is None or actuals_qty is None:
            raise ValueError("forecast_qty and actuals_qty are required when they cannot be queried")

        abs_error = abs(float(forecast_qty) - float(actuals_qty))
        naive = naive_mae(history or [])
        payload = {
            "tenant_id": tenant_id,
            "product_id": product_id,
            "location_id": location_id,
            "period_start": period_start,
            "period_type": period_type,
            "lag_periods": lag_periods,
            "forecast_source": forecast_source,
            "forecast_qty": forecast_qty,
            "actuals_qty": actuals_qty,
            "absolute_error": abs_error,
            "error_pct": mape_from_pair(forecast_qty, actuals_qty),
            "bias": float(forecast_qty) - float(actuals_qty),
            "bias_pct": bias_pct_from_pair(forecast_qty, actuals_qty),
            "mase_component": mase_component(abs_error, naive),
        }
        if session is None:
            return payload
        row = ForecastError(**payload)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    async def get_metric(
        self,
        metric: str,
        *,
        session: AsyncSession | None = None,
        rows: Sequence[ForecastError] | None = None,
        tenant_id: str | UUID | None = None,
        product_id: UUID | None = None,
        forecast_source: str | None = None,
    ) -> dict[str, Any]:
        values = await self._metric_values(
            metric,
            session=session,
            rows=rows,
            tenant_id=tenant_id,
            product_id=product_id,
            forecast_source=forecast_source,
        )
        return {
            "metric": metric,
            "value": round(mean(values), 4) if values else None,
            "sample_size": len(values),
        }

    async def get_stability(
        self,
        *,
        session: AsyncSession | None = None,
        rows: Sequence[ForecastStability] | None = None,
        tenant_id: str | UUID | None = None,
        product_id: UUID | None = None,
    ) -> dict[str, Any]:
        if rows is None:
            rows = []
            if session is not None:
                stmt = select(ForecastStability).where(ForecastStability.tenant_id == tenant_id)
                if product_id is not None:
                    stmt = stmt.where(ForecastStability.product_id == product_id)
                result = await session.execute(stmt)
                rows = result.scalars().all()
        values = [float(row.change_pct) for row in rows if row.change_pct is not None]
        return {"metric": "stability", "value": round(mean(values), 4) if values else None, "sample_size": len(values)}

    async def get_value_add(
        self,
        *,
        session: AsyncSession | None = None,
        tenant_id: str | UUID | None = None,
        product_id: UUID | None = None,
    ) -> dict[str, Any]:
        stat = await self.get_metric(
            "mape",
            session=session,
            tenant_id=tenant_id,
            product_id=product_id,
            forecast_source="statistical",
        )
        final = await self.get_metric(
            "mape",
            session=session,
            tenant_id=tenant_id,
            product_id=product_id,
            forecast_source="final",
        )
        return {
            "metric": "value_add",
            "value": value_add_pct(stat["value"], final["value"]),
            "stat_mape": stat["value"],
            "final_mape": final["value"],
        }

    async def _metric_values(
        self,
        metric: str,
        *,
        session: AsyncSession | None,
        rows: Sequence[ForecastError] | None,
        tenant_id: str | UUID | None,
        product_id: UUID | None,
        forecast_source: str | None,
    ) -> list[float]:
        column_by_metric = {
            "mape": ForecastError.error_pct,
            "bias": ForecastError.bias_pct,
            "mase": ForecastError.mase_component,
        }
        if metric not in column_by_metric:
            raise ValueError(f"Unsupported metric: {metric}")
        if rows is None:
            rows = []
            if session is not None:
                stmt = select(ForecastError).where(ForecastError.tenant_id == tenant_id)
                if product_id is not None:
                    stmt = stmt.where(ForecastError.product_id == product_id)
                if forecast_source is not None:
                    stmt = stmt.where(ForecastError.forecast_source == forecast_source)
                result = await session.execute(stmt)
                rows = result.scalars().all()
        attr_by_metric = {"mape": "error_pct", "bias": "bias_pct", "mase": "mase_component"}
        return [float(value) for row in rows if (value := getattr(row, attr_by_metric[metric])) is not None]

    async def _latest_snapshot_qty(
        self,
        *,
        session: AsyncSession,
        tenant_id: str | UUID | None,
        product_id: UUID,
        period_start: date,
        forecast_source: str,
    ) -> float | None:
        stmt = (
            select(ForecastSnapshot.forecast_qty)
            .where(
                ForecastSnapshot.tenant_id == tenant_id,
                ForecastSnapshot.product_id == product_id,
                ForecastSnapshot.target_period_start == period_start,
                ForecastSnapshot.forecast_source == forecast_source,
            )
            .order_by(ForecastSnapshot.snapshot_date.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        value = result.scalar_one_or_none()
        return float(value) if value is not None else None

    async def _actuals_qty(
        self,
        *,
        session: AsyncSession,
        tenant_id: str | UUID | None,
        product_id: UUID,
        period_start: date,
        period_type: str,
    ) -> float:
        start, end = _period_bounds(period_start, period_type)
        stmt = select(func.coalesce(func.sum(DemandLine.quantity), 0)).where(
            DemandLine.tenant_id == tenant_id,
            DemandLine.product_id == product_id,
            DemandLine.required_date >= start,
            DemandLine.required_date < end,
        )
        result = await session.execute(stmt)
        return float(result.scalar() or 0)
