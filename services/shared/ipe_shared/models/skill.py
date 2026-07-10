from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class Skill(Base, TenantScopedMixin):
    __tablename__ = "cdm_skill"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(128), nullable=False, unique=True)
    description = Column(String(512))
    category = Column(String(64), nullable=False, server_default="general")
    certification_required = Column(Boolean, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
