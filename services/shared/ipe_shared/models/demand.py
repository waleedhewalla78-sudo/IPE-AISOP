from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class DemandLine(Base, TenantScopedMixin):
    __tablename__ = "cdm_demand_line"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_source_id = Column(String(128), nullable=False)
    erp_source_type = Column(String(32), nullable=False)
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False)
    revenue = Column(Numeric(18, 2))
    uom = Column(String(16), nullable=False, server_default="unit")
    required_date = Column(DateTime(timezone=True), nullable=False)
    demand_type = Column(String(16), nullable=False)
    customer_id = Column(UUID, ForeignKey("cdm_customer.id"))
    customer_tier = Column(Numeric(2, 0), server_default="3")
    margin_pct = Column(Numeric(6, 2))
    penalty_cost = Column(Numeric(14, 2), server_default="0")
    priority_score = Column(Numeric(8, 4))
    status = Column(String(24), nullable=False, server_default="new")
    mo_id = Column(UUID, ForeignKey("cdm_manufacturing_order.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("demand_type IN ('MTO','MTS','CTO','ETO')", name="ck_demand_type"),
    )
