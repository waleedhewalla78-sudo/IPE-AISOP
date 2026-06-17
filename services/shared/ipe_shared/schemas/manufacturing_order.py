from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ManufacturingOrderResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: float
    planned_start: datetime | None
    planned_end: datetime | None
    feasibility_score: float | None
    material_score: float | None
    capacity_score: float | None
    labor_score: float | None
    primary_constraint: str | None
    status: str
    created_at: datetime
