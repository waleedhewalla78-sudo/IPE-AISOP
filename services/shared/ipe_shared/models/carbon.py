from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class EmissionFactor(Base, TenantScopedMixin):
    __tablename__ = "cdm_emission_factor"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    energy_source = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False, default="global")
    factor_kg_co2_per_kwh = Column(Float, nullable=False, default=0.0)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MaterialCarbon(Base, TenantScopedMixin):
    __tablename__ = "cdm_material_carbon"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    product_id = Column(UUID, nullable=False, index=True)
    kg_co2_per_unit = Column(Float, nullable=False, default=0.0)
    kg_co2_per_kg = Column(Float, nullable=True)
    recycled_content_pct = Column(Float, nullable=True, default=0.0)
    end_of_life_recyclable_pct = Column(Float, nullable=True, default=0.0)
    source = Column(String(50), nullable=True, default="estimated")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TransportEmission(Base, TenantScopedMixin):
    __tablename__ = "cdm_transport_emission"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    route_id = Column(UUID, nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False)
    kg_co2_per_unit_per_km = Column(Float, nullable=False, default=0.0)
    kg_co2_per_trip = Column(Float, nullable=True)
    load_factor_avg = Column(Float, nullable=True, default=0.8)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
