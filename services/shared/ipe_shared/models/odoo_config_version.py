from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base


class OdooConfigVersion(Base):
    __tablename__ = "cdm_odoo_config_version"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID, nullable=False)
    entity_key = Column(String(64), nullable=False, server_default="primary")
    version = Column(Integer, nullable=False)
    is_current = Column(Boolean, nullable=False, server_default="false")
    name = Column(String(128), nullable=False, server_default="")
    odoo_url = Column(String(512), nullable=False)
    odoo_db = Column(String(128), nullable=False)
    odoo_username = Column(String(256), nullable=False)
    odoo_password_enc = Column(Text)
    enabled = Column(Boolean, nullable=False, server_default="true")
    sync_interval_minutes = Column(Integer, nullable=False, server_default="900")
    field_mappings = Column(JSONB, nullable=False, server_default="{}")
    config_meta = Column(JSONB, nullable=False, server_default="{}")
    change_summary = Column(Text)
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "entity_key", "version", name="uq_odoo_config_tenant_entity_version"),
    )
