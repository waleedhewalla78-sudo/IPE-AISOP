from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: UUID
    erp_source_id: str
    name: str
    internal_ref: str | None
    source_type: str
    uom: str
    standard_cost: float | None
    lead_time_days: float | None
    safety_stock: float
    created_at: datetime
