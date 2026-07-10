from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class MaterialAttribute(Base, TenantScopedMixin):
    __tablename__ = "cdm_material_attributes"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    material_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    attributes = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
