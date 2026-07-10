from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class SopForecast(Base, TenantScopedMixin):
    __tablename__ = "cdm_sop_forecast"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    product_family = Column(String(100), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, default="weekly")
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    forecast_qty = Column(Float, nullable=False, default=0.0)
    actual_qty = Column(Float, nullable=True, default=0.0)
    capacity_qty = Column(Float, nullable=True, default=0.0)
    unit = Column(String(20), nullable=False, default="units")
    source = Column(String(50), nullable=False, default="pipeline")
    confidence_pct = Column(Float, nullable=True, default=0.0)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SopPlan(Base, TenantScopedMixin):
    __tablename__ = "cdm_sop_plan"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    plan_name = Column(String(200), nullable=False)
    horizon_weeks = Column(Integer, nullable=False, default=52)
    status = Column(String(20), nullable=False, default="draft")
    alpha = Column(Float, nullable=False, default=1.0)
    plan_data = Column(JSON, nullable=True)
    gap_analysis = Column(JSON, nullable=True)
    created_by = Column(UUID, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    version = Column(Integer, nullable=False, default=1)