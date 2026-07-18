"""Phase 8 — Odoo write-back log ORM (migration 070)."""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class WriteBackLog(Base, TenantScopedMixin):
    __tablename__ = "cdm_write_back_log"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(128), nullable=False)
    field_name = Column(String(128), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    action = Column(String(64), nullable=False, server_default="update")
    status = Column(
        String(32), nullable=False, server_default="pending_approval"
    )  # dry_run | pending_approval | executed | failed | rolled_back | queued
    dry_run = Column(Boolean, nullable=False, server_default="true")
    approved_by = Column(String(128), nullable=True)
    requested_by = Column(String(128), nullable=True)
    financial_impact = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    attempt_count = Column(Integer, nullable=False, server_default="0")
    payload = Column(JSONB, nullable=True)
    is_live = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    rollback_deadline = Column(DateTime(timezone=True), nullable=True)
