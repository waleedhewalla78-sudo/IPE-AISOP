from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SupplyOrderResponse(BaseModel):
    id: UUID
    product_id: UUID
    supplier_id: UUID | None
    quantity_ordered: float
    quantity_received: float
    expected_date: datetime
    status: str
    reliability_adjusted_date: datetime | None
