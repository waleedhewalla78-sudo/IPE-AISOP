from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class BillOfMaterial(Base, TenantScopedMixin):
    __tablename__ = "cdm_bill_of_material"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    product_id = Column(UUID, ForeignKey("cdm_product.id", ondelete="CASCADE"), nullable=False)
    parent_bom_id = Column(UUID, ForeignKey("cdm_bill_of_material.id"))
    bom_level = Column(Integer, server_default="0")
    is_phantom = Column(Boolean, server_default="false")
    version = Column(String(16), nullable=False, server_default="1.0")
    is_active = Column(Boolean, nullable=False, server_default="true")
    erp_source_id = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BomLine(Base, TenantScopedMixin):
    __tablename__ = "cdm_bom_line"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    bom_id = Column(
        UUID, ForeignKey("cdm_bill_of_material.id", ondelete="CASCADE"), nullable=False
    )
    component_id = Column(UUID, ForeignKey("cdm_product.id", ondelete="CASCADE"), nullable=False)
    quantity_per = Column(Numeric(14, 6), nullable=False)
    uom = Column(String(16), nullable=False, server_default="unit")
    scrap_rate_pct = Column(Numeric(5, 2), server_default="0")
    is_critical = Column(Boolean, server_default="false")
    substitute_ids = Column(ARRAY(UUID), server_default="{}")
