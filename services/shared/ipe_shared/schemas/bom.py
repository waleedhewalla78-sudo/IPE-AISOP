from uuid import UUID

from pydantic import BaseModel


class BomLineSchema(BaseModel):
    component_id: UUID
    quantity_per: float
    uom: str = "unit"
    is_critical: bool = False


class BillOfMaterialResponse(BaseModel):
    id: UUID
    product_id: UUID
    version: str
    is_active: bool
