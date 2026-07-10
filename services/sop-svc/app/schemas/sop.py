from datetime import date, datetime

from pydantic import BaseModel


class SopCycleCreateRequest(BaseModel):
    cycle_name: str | None = None
    cycle_month: date
    demand_review_deadline: datetime | None = None
    supply_review_deadline: datetime | None = None
    reconciliation_deadline: datetime | None = None
    management_review_deadline: datetime | None = None


class SopCycleAdvanceRequest(BaseModel):
    target_status: str | None = None


class StageApprovalRequest(BaseModel):
    status: str = "approved"
    notes: str | None = None


class SopWeightsRequest(BaseModel):
    weight_sales: float = 0.30
    weight_statistical: float = 0.40
    weight_marketing: float = 0.20
    weight_finance: float = 0.10
