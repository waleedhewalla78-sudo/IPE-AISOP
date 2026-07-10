from sqlalchemy import Column, DateTime, ForeignKey, SmallInteger, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ipe_shared.database.base import Base


worker_skill_link = Table(
    "cdm_worker_skill_link",
    Base.metadata,
    Column("worker_id", UUID, ForeignKey("cdm_worker.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID, ForeignKey("cdm_skill.id", ondelete="CASCADE"), primary_key=True),
    Column("proficiency_level", SmallInteger, server_default="1"),
    Column("certified_at", DateTime(timezone=True)),
)
