"""Pydantic schemas for the safety stock API layer."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class SafetyStockCalculateRequest(BaseModel):
    product_id: UUID | None = None
    service_level_pct: float | None = Field(default=None, gt=0, le=100)
    period_days: int = Field(default=7, ge=1, le=31)
    history_days: int = Field(default=365, ge=7, le=1825)


class SafetyStockResultItem(BaseModel):
    product_id: UUID | str
    product_name: str | None = None
    calculation_date: date | str | None = None
    service_level_target_pct: float
    z_score: float | None = None
    avg_demand_per_period: float | None = None
    demand_stddev: float | None = None
    demand_cv: float | None = None
    avg_lead_time_periods: float | None = None
    lead_time_stddev: float | None = None
    lead_time_cv: float | None = None
    safety_stock_qty: float
    safety_stock_demand_component: float | None = None
    safety_stock_leadtime_component: float | None = None
    reorder_point_qty: float
    current_stock_qty: float | None = None
    delta_qty: float | None = None
    delta_pct: float | None = None
    safety_stock_value: float | None = None
    delta_value: float | None = None


class SafetyStockCalculateResponse(BaseModel):
    calculation_date: date | str
    total_products: int
    records: list[SafetyStockResultItem]


class LeadTimeSummaryItem(BaseModel):
    product_id: UUID | str
    sample_size: int
    avg_lead_time_days: float
    lead_time_stddev_days: float
    lead_time_cv: float
