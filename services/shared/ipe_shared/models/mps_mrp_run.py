"""MPS/MRP durable run snapshots (Spec 029 / migration 069)."""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class MpsRun(Base, TenantScopedMixin):
    __tablename__ = "cdm_mps_run"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    product_id = Column(String(64), nullable=False)
    run_payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MrpRun(Base, TenantScopedMixin):
    __tablename__ = "cdm_mrp_run"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    root_product_id = Column(String(64), nullable=False)
    run_payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
