from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class LandedCostProfile(Base, TenantScopedMixin):
    __tablename__ = "cdm_landed_cost_profiles"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    supplier_id = Column(UUID, ForeignKey("cdm_supplier.id"), nullable=True)
    region = Column(String(64), nullable=False)
    base_cost_usd = Column(Numeric(12, 4), nullable=False, server_default="0")
    freight_usd = Column(Numeric(12, 4), nullable=False, server_default="0")
    tariff_pct = Column(Numeric(8, 4), nullable=False, server_default="0")
    risk_premium_pct = Column(Numeric(8, 4), nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
