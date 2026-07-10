from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class DurationPrediction(Base):
    __tablename__ = "cdm_duration_prediction"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    tenant_id = Column(UUID, ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False)
    mo_id = Column(UUID, ForeignKey("cdm_manufacturing_order.id"))
    work_order_id = Column(UUID)
    actual_duration_mins = Column(Numeric(10, 2))
    predicted_duration_mins = Column(Numeric(10, 2), nullable=False)
    model_version = Column(String(50), nullable=False)
    confidence = Column(Numeric(5, 4))
    fallback_used = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
