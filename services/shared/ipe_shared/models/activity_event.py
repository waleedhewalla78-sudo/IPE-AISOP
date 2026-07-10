"""Cross-tool activity event model (Sprint 7 EIB activity store)."""

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ActivityEvent(Base, TenantScopedMixin):
    __tablename__ = "cdm_activity_event"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    source_tool = Column(String(64), nullable=False)
    event_type = Column(String(128), nullable=False)
    actor_id = Column(String(128))
    entity_type = Column(String(64))
    entity_id = Column(UUID)
    summary = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")
    severity = Column(String(16), nullable=False, server_default="info")
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    idempotency_key = Column(String(256))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
