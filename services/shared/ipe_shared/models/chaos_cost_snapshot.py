from sqlalchemy import Column, Date, DateTime, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ChaosCostSnapshot(Base, TenantScopedMixin):
    __tablename__ = "cdm_chaos_cost_snapshot"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    snapshot_date = Column(Date, nullable=False)
    total_chaos_usd = Column(Numeric(14, 2), nullable=False, server_default="0")
    categories = Column(JSONB, nullable=False, server_default="[]")
    top_mos = Column(JSONB, nullable=False, server_default="[]")
    war_room_links = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
