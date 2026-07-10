from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class FinancialProjection(Base, TenantScopedMixin):
    __tablename__ = "cdm_financial_projection"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    mo_id = Column(UUID, nullable=True, index=True)
    product_id = Column(UUID, nullable=False, index=True)
    projection_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    unit_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    revenue = Column(Float, nullable=True, default=0.0)
    margin = Column(Float, nullable=True, default=0.0)
    margin_pct = Column(Float, nullable=True, default=0.0)
    labor_cost = Column(Float, nullable=True, default=0.0)
    material_cost = Column(Float, nullable=True, default=0.0)
    energy_cost = Column(Float, nullable=True, default=0.0)
    overhead_cost = Column(Float, nullable=True, default=0.0)
    wip_value = Column(Float, nullable=True, default=0.0)
    projection_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    version = Column(Integer, nullable=False, default=1)
