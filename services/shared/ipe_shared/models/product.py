from sqlalchemy import CheckConstraint, Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class Product(Base, TenantScopedMixin):
    __tablename__ = "cdm_product"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_source_id = Column(String(128), nullable=False)
    erp_source_type = Column(String(32), nullable=False)
    name = Column(String(256), nullable=False)
    internal_ref = Column(String(64))
    source_type = Column(String(16), nullable=False)
    uom = Column(String(16), nullable=False, server_default="unit")
    standard_cost = Column(Numeric(14, 4))
    unit_cost = Column(Numeric(18, 4))
    list_price = Column(Numeric(18, 4))
    weight = Column(Numeric(10, 4))
    lead_time_days = Column(Numeric(6, 2))
    safety_stock = Column(Numeric(14, 4), server_default="0")
    category_tags = Column(JSONB, server_default="[]")
    demand_cv = Column(Numeric(6, 4))
    avg_monthly_demand = Column(Numeric(14, 4))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('manufactured', 'purchased', 'subcontracted')",
            name="ck_product_source",
        ),
    )
