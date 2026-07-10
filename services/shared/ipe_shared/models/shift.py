from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class Shift(Base, TenantScopedMixin):
    __tablename__ = "cdm_shift"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    days_of_week = Column(JSONB, nullable=False, server_default="[0,1,2,3,4]")
    start_hour = Column(Integer, nullable=False, server_default="8")
    start_minute = Column(Integer, nullable=False, server_default="0")
    end_hour = Column(Integer, nullable=False, server_default="16")
    end_minute = Column(Integer, nullable=False, server_default="0")
    break_minutes = Column(Integer, server_default="30")
    overtime_multiplier = Column(Numeric(4, 2), server_default="1.5")
    timezone = Column(String(64), server_default="UTC")
    is_active = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
