from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin
from ipe_shared.models.product import Product  # noqa: F401 — FK target for demand models
from ipe_shared.models.user import User  # noqa: F401 — FK target for copilot sessions


class CopilotSession(Base, TenantScopedMixin):
    __tablename__ = "cdm_copilot_session"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID, ForeignKey("cdm_user.id"), nullable=False)
    role = Column(String(32), nullable=False)
    context_jsonb = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DemandSignal(Base, TenantScopedMixin):
    __tablename__ = "cdm_demand_signal"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    source_type = Column(String(32), nullable=False)
    source_id = Column(String(128))
    product_id = Column(UUID, ForeignKey("cdm_product.id"))
    location_id = Column(UUID)
    signal_ts = Column(DateTime(timezone=True), nullable=False)
    value = Column(Numeric(14, 4), nullable=False)
    quality_score = Column(Numeric(5, 4), server_default="1.0")
    metadata_jsonb = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DemandForecast(Base, TenantScopedMixin):
    __tablename__ = "cdm_demand_forecast"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    location_id = Column(UUID)
    horizon_type = Column(String(16), nullable=False, server_default="short")
    forecast_date = Column(DateTime(timezone=True), nullable=False)
    value = Column(Numeric(14, 4), nullable=False)
    lower_bound = Column(Numeric(14, 4))
    upper_bound = Column(Numeric(14, 4))
    model_version = Column(String(32), server_default="ses-v1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PlanningScenario(Base, TenantScopedMixin):
    __tablename__ = "cdm_scenario"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(128), nullable=False)
    description = Column(Text)
    base_scenario_id = Column(UUID)
    status = Column(String(24), server_default="active")
    created_by = Column(String(128))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class ScenarioParameter(Base, TenantScopedMixin):
    __tablename__ = "cdm_scenario_parameter"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    scenario_id = Column(UUID, ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False)
    parameter_key = Column(String(64), nullable=False)
    parameter_value = Column(String(256), nullable=False)
    data_type = Column(String(16), server_default="string")
    description = Column(Text)


class ScenarioResult(Base, TenantScopedMixin):
    __tablename__ = "cdm_scenario_result"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    scenario_id = Column(UUID, ForeignKey("cdm_scenario.id", ondelete="CASCADE"), nullable=False)
    kpi_key = Column(String(64), nullable=False)
    kpi_value = Column(Numeric(14, 4), nullable=False)
    unit = Column(String(16), server_default="count")
    computed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
