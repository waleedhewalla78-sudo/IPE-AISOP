from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ResourceCalendar(Base, TenantScopedMixin):
    __tablename__ = "cdm_resource_calendar"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(128), nullable=False)
    timezone = Column(String(64), nullable=False, server_default="UTC")
    entries = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
