"""ERP connection models (W1-03 Sprint 4)."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base


class ErpConnection(Base):
    __tablename__ = "cdm_erp_connection"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID, nullable=False, index=True)
    erp_type = Column(String(20), nullable=False, server_default="odoo")
    display_name = Column(String(100), nullable=False)
    host_url = Column(String(500), nullable=False)
    database_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    api_protocol = Column(String(20), server_default="xmlrpc")
    is_active = Column(Boolean, server_default="true")
    is_production = Column(Boolean, server_default="false")
    last_test_at = Column(DateTime(timezone=True), nullable=True)
    last_test_result = Column(String(20), nullable=True)
    last_test_message = Column(Text, nullable=True)
    sync_interval_seconds = Column(Integer, server_default="900")
    sync_enabled = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID, nullable=True)


class ErpConnectionLog(Base):
    __tablename__ = "cdm_erp_connection_log"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID, nullable=False, index=True)
    connection_id = Column(
        UUID,
        ForeignKey("cdm_erp_connection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(String(50), nullable=False)
    result = Column(String(20), nullable=True)
    details = Column(JSONB, nullable=True)
    performed_by = Column(UUID, nullable=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
