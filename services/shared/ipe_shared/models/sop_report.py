from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class SopReport(Base, TenantScopedMixin):
    __tablename__ = "cdm_sop_report"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    report_name = Column(String(256), nullable=False)
    horizon_weeks = Column(Integer, nullable=False, server_default="12")
    status = Column(String(20), nullable=False, server_default="draft")
    summary = Column(JSONB, nullable=False, server_default="{}")
    gap_analysis = Column(JSONB, nullable=False, server_default="{}")
    recommendations = Column(JSONB, nullable=False, server_default="[]")
    generated_by = Column(String(128))
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
