from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin
from ipe_shared.models.worker_skill_link import worker_skill_link


class Worker(Base, TenantScopedMixin):
    __tablename__ = "cdm_worker"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_source_id = Column(String(128), nullable=False)
    name = Column(String(256), nullable=False)
    shift_calendar_id = Column(UUID, ForeignKey("cdm_resource_calendar.id"))
    max_consecutive_hours = Column(Numeric(4, 2), server_default="10")
    cost_per_hour = Column(Numeric(10, 2))
    overtime_eligible = Column(Boolean, server_default="true")
    predicted_absence_probability = Column(Numeric(5, 4))
    is_active = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    skills = relationship("Skill", secondary=worker_skill_link, backref="workers")
