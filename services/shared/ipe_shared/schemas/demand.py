from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DemandLineCreate(BaseModel):
    erp_source_id: str
    erp_source_type: str
    product_id: UUID
    quantity: float
    uom: str = "unit"
    required_date: datetime
    demand_type: str
    customer_id: UUID | None = None
    penalty_cost: float = 0


class DemandLineResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: float
    required_date: datetime
    demand_type: str
    priority_score: float | None
    status: str
    created_at: datetime


class ClassifyRequest(BaseModel):
    demand_line_ids: list[UUID]


class ClassifyResponse(BaseModel):
    demand_line_id: UUID
    priority_score: float
    demand_type: str
    confidence: float
