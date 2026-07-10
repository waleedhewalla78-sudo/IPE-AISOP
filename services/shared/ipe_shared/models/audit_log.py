from sqlalchemy import BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base


class AuditLog(Base):
    __tablename__ = "cdm_audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(UUID, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actor_type = Column(String(16), nullable=False)
    actor_id = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(UUID, nullable=False)
    before_state = Column(JSONB)
    after_state = Column(JSONB)
    rationale = Column(Text)
