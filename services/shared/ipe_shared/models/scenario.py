from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class Scenario(Base, TenantScopedMixin):
    __tablename__ = "cdm_scenario"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    base_scenario_id = Column(UUID)
    status = Column(String(24), server_default="active")
    created_by = Column(String(128))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class ScenarioDemand(Base):
    __tablename__ = "cdm_scenario_demand"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    scenario_id = Column(UUID, ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False)
    original_demand_id = Column(UUID, nullable=False)
    data = Column(JSONB, nullable=False)


class ScenarioSupply(Base):
    __tablename__ = "cdm_scenario_supply"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    scenario_id = Column(UUID, ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False)
    original_supply_id = Column(UUID, nullable=False)
    data = Column(JSONB, nullable=False)


class ScenarioResource(Base):
    __tablename__ = "cdm_scenario_resource"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    scenario_id = Column(UUID, ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False)
    original_resource_id = Column(UUID, nullable=False)
    data = Column(JSONB, nullable=False)