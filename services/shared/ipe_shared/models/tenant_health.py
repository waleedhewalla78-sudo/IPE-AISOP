from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class TenantHealth(Base, TenantScopedMixin):
    __tablename__ = "cdm_tenant_health"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    health_status = Column(String(16), nullable=False, server_default="unknown")
    sync_status = Column(String(16), nullable=False, server_default="unknown")
    last_sync_at = Column(DateTime(timezone=True))
    failed_sync_count_24h = Column(Integer, nullable=False, server_default="0")
    mdr_passed = Column(Boolean)
    mdr_score_pct = Column(Numeric(5, 2))
    active_mo_count = Column(Integer, nullable=False, server_default="0")
    open_alert_count = Column(Integer, nullable=False, server_default="0")
    snapshot_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
