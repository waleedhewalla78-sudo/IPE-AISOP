from sqlalchemy import Column, String, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ipe_shared.database.base import Base


class TransportFleet(Base):
    __tablename__ = "cdm_transport_fleet"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    route_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False, default="truck")
    capacity_units = Column(Integer, nullable=False, default=1000)
    cost_per_trip = Column(Float, nullable=False, default=0.0)
    cost_per_unit = Column(Float, nullable=True, default=0.0)
    max_trips_per_day = Column(Integer, nullable=False, default=5)
    available_units = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    speed_kmh = Column(Float, nullable=True, default=60.0)
