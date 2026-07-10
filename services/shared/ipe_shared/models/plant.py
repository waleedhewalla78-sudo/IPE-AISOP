from sqlalchemy import Column, String, Float, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ipe_shared.database.base import Base


class Plant(Base):
    __tablename__ = "cdm_plant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=False, default="UTC")
    capacity_hours_per_day = Column(Float, nullable=False, default=8.0)
    cost_per_hour = Column(Float, nullable=False, default=0.0)
    energy_kwh_per_hour = Column(Float, nullable=True, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    capabilities = Column(JSON, nullable=True, default=list)
    metadata_json = Column("metadata", JSON, nullable=True, default=dict)
