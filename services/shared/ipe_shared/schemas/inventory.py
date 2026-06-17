from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InventoryPositionResponse(BaseModel):
    time: datetime
    product_id: UUID
    location_id: UUID
    qty_on_hand: float
    qty_reserved: float
    qty_in_transit: float
