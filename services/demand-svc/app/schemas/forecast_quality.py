from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ForecastSnapshotCreateRequest(BaseModel):
    product_id: UUID
    location_id: UUID | None = None
    snapshot_date: date = Field(default_factory=date.today)
    target_period_start: date
    target_period_type: str = Field(default="month", pattern="^(day|week|month)$")
    forecast_qty: float
    forecast_source: str = Field(default="statistical", min_length=1, max_length=50)
    model_id: str | None = None
    model_version: str | None = None


class ForecastErrorCalculateRequest(BaseModel):
    product_id: UUID
    location_id: UUID | None = None
    period_start: date
    period_type: str = Field(default="month", pattern="^(day|week|month)$")
    lag_periods: int = Field(default=1, ge=0)
    forecast_source: str = Field(default="statistical", min_length=1, max_length=50)
    forecast_qty: float | None = None
    actuals_qty: float | None = None
    history: list[float] | None = None


class ForecastQualityMetricResponse(BaseModel):
    metric: str
    value: float | None = None
    sample_size: int | None = None
