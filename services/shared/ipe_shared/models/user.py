from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class User(Base, TenantScopedMixin):
    __tablename__ = "cdm_user"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    email = Column(String(256), nullable=False)
    password_hash = Column(String(256))
    full_name = Column(String(256))
    role = Column(String(32), nullable=False, server_default="planner")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
