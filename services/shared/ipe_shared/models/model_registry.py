from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base


class ModelRegistry(Base):
    __tablename__ = "cdm_model_registry"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    tenant_id = Column(UUID, ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=False)
    model_type = Column(String(32), nullable=False)
    metrics = Column(JSONB, nullable=False)
    baseline_metrics = Column(JSONB)
    is_production = Column(Boolean, nullable=False, server_default="false")
    is_better_than_baseline = Column(Boolean)
    artifact_path = Column(String(512))
    training_rows = Column(Integer)
    training_duration_seconds = Column(Numeric(10, 2))
    trained_by = Column(String(64))
    promoted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
