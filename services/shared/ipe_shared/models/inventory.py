from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID

from ipe_shared.database.base import Base


class InventoryPosition(Base):
    __tablename__ = "cdm_inventory_position"

    time = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    tenant_id = Column(UUID, nullable=False)
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    location_id = Column(UUID, ForeignKey("cdm_location.id"), nullable=False)
    qty_on_hand = Column(Numeric(14, 4), nullable=False, server_default="0")
    qty_reserved = Column(Numeric(14, 4), nullable=False, server_default="0")
    qty_in_transit = Column(Numeric(14, 4), nullable=False, server_default="0")
