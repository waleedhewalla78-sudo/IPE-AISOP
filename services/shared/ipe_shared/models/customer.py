from sqlalchemy import Column, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class Customer(Base, TenantScopedMixin):
    __tablename__ = "cdm_customer"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_source_id = Column(String(128), nullable=False)
    name = Column(String(256), nullable=False)
    tier = Column(Numeric(2, 0), server_default="3")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "erp_source_id", name="uq_customer_tenant_erp"),
    )
