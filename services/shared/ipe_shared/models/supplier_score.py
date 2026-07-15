from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class SupplierScore(Base, TenantScopedMixin):
    __tablename__ = "cdm_supplier_score"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    supplier_id = Column(UUID, ForeignKey("cdm_supplier.id"), nullable=False)
    reliability_score = Column(Numeric(5, 4), nullable=False)
    risk_tier = Column(String(16), nullable=False, server_default="medium")
    on_time_pct = Column(Numeric(5, 2))
    avg_delay_days = Column(Numeric(6, 2))
    sample_size = Column(Integer, nullable=False, server_default="0")
    contributing_factors = Column(JSONB, nullable=False, server_default="{}")
    # Ops Phase 3 columns (migration 055 ALTER)
    quality_rejection_pct = Column(Numeric(5, 2), nullable=True)
    concentration_pct = Column(Numeric(5, 2), nullable=True)
    lead_time_trend = Column(String(20), nullable=True)
    overall_score = Column(Numeric(6, 2), nullable=True)
    recommendation = Column(String, nullable=True)
    scored_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
