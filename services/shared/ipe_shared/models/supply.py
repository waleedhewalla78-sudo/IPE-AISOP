from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class SupplyOrder(Base, TenantScopedMixin):
    __tablename__ = "cdm_supply_order"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_source_id = Column(String(128), nullable=False)
    erp_source_type = Column(String(32), nullable=False)
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    supplier_id = Column(UUID, ForeignKey("cdm_supplier.id"))
    quantity_ordered = Column(Numeric(14, 4), nullable=False)
    quantity_received = Column(Numeric(14, 4), server_default="0")
    expected_date = Column(DateTime(timezone=True), nullable=False)
    actual_date = Column(DateTime(timezone=True))
    status = Column(String(24), nullable=False, server_default="confirmed")
    reliability_adjusted_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
