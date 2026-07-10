from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ConsensusCalculateRequest(BaseModel):
    sales_forecast_qty: float | None = None
    statistical_forecast_qty: float | None = None
    marketing_forecast_qty: float | None = None
    finance_plan_qty: float | None = None
    planned_price: float | None = None
    cost_per_unit: float | None = None
    version_id: UUID | None = None
    product_id: UUID | None = None
    location_id: UUID | None = None
    customer_id: UUID | None = None
    period_start: date | None = None
    period_type: str = "month"
    persist: bool = False


class ConsensusUpdateRequest(BaseModel):
    sales_forecast_qty: float | None = None
    statistical_forecast_qty: float | None = None
    marketing_forecast_qty: float | None = None
    finance_plan_qty: float | None = None
    planned_price: float | None = None
    cost_per_unit: float | None = None
    constrained_demand_qty: float | None = None
