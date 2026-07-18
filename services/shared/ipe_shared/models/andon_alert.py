"""Phase 7 §5.3 — Andon alert ORM (migration 067)."""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class AndonAlert(Base, TenantScopedMixin):
    __tablename__ = "cdm_andon_alert"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    alert_ref = Column(String(40), nullable=True)
    color = Column(String(10), nullable=False)
    work_centre = Column(String(40), nullable=True)
    reported_by = Column(String(80), nullable=True)
    message = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    status = Column(String(20), server_default="active")
    response_minutes = Column(Integer, nullable=True)
    escalate_after_minutes = Column(Integer, nullable=True)
    resolution = Column(Text, nullable=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
