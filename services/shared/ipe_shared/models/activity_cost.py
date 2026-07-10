from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ActivityCostDriver(Base, TenantScopedMixin):
    __tablename__ = "cdm_activity_cost_drivers"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=True)
    setup_mins = Column(Numeric(10, 2), nullable=False, server_default="15")
    overtime_rate_usd_per_hr = Column(Numeric(12, 4), nullable=False, server_default="95")
    expedite_cost_per_unit = Column(Numeric(12, 4), nullable=False, server_default="0")
    overhead_pct = Column(Numeric(6, 4), nullable=False, server_default="0.12")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
