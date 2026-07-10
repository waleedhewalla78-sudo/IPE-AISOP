from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base


class Tenant(Base):
    __tablename__ = "cdm_tenant"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(256), nullable=False)
    tier = Column(String(16), nullable=False, server_default="starter")
    erp_type = Column(String(16), nullable=False)
    erp_version = Column(String(32))
    erp_base_url = Column(String(512))
    autonomy_mode = Column(String(16), nullable=False, server_default="shadow")
    config = Column(JSONB, server_default="{}")
    api_secret = Column(String(128))
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "tier IN ('starter', 'professional', 'enterprise')", name="ck_tenant_tier"
        ),
        CheckConstraint(
            "erp_type IN ('odoo', 'sap', 'd365', 'oracle', 'generic')", name="ck_tenant_erp"
        ),
        CheckConstraint(
            "autonomy_mode IN ('shadow', 'suggest', 'autonomous')", name="ck_tenant_autonomy"
        ),
    )
