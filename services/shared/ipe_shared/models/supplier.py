from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class Supplier(Base, TenantScopedMixin):
    __tablename__ = "cdm_supplier"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_source_id = Column(String(128), nullable=False)
    name = Column(String(256), nullable=False)
    reliability_score = Column(Numeric(5, 4))
    avg_delay_days = Column(Numeric(6, 2))
    delay_std_dev_days = Column(Numeric(6, 2))
    delay_distribution_type = Column(String(16), server_default="normal")
    delay_distribution_params = Column(JSONB)
    sample_size = Column(Integer, server_default="0")
    last_model_update = Column(DateTime(timezone=True))
    esg_score = Column(Numeric(5, 2), server_default="70")
    risk_tier = Column(String(16), server_default="medium")
    category = Column(String(64))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
