from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class DelayRootCause(Base, TenantScopedMixin):
    __tablename__ = "cdm_delay_root_cause"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    delay_event_id = Column(UUID, ForeignKey("cdm_delay_event.id"))
    source_text = Column(String(2048), nullable=False)
    primary_category = Column(String(50), nullable=False)
    secondary_categories = Column(JSONB)
    confidence = Column(Numeric(5, 4))
    extracted_by = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())