from sqlalchemy import CheckConstraint, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin

SYNC_RUN_STATUSES = ("running", "success", "partial", "failed")
SYNC_SOURCES = ("odoo", "manual", "api")
SYNC_TRIGGERS = ("scheduled", "manual", "startup")


class SyncRun(Base, TenantScopedMixin):
    __tablename__ = "cdm_sync_run"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    source = Column(String(32), nullable=False, server_default="odoo")
    trigger = Column(String(32), nullable=False, server_default="scheduled")
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, server_default="running")
    entity_counts = Column(JSONB, nullable=False, server_default="{}")
    error_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'success', 'partial', 'failed')",
            name="ck_sync_run_status",
        ),
    )
