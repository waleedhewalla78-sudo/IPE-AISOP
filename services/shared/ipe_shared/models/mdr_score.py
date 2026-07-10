from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class MdrScore(Base, TenantScopedMixin):
    __tablename__ = "cdm_mdr_score"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    bom_completeness_pct = Column(Numeric(5, 2), nullable=False)
    lead_time_accuracy_pct = Column(Numeric(5, 2), nullable=False)
    passed = Column(Boolean, nullable=False, server_default="false")
    evaluated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
