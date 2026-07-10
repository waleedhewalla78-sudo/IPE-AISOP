from sqlalchemy import Column, String, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ipe_shared.database.base import Base


class TransferRoute(Base):
    __tablename__ = "cdm_transfer_route"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    origin_plant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    destination_plant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    transport_mode = Column(String(50), nullable=False, default="truck")
    transit_time_hours = Column(Float, nullable=False, default=24.0)
    transit_time_std_dev_hours = Column(Float, nullable=True, default=0.0)
    cost_per_unit = Column(Float, nullable=False, default=0.0)
    capacity_units = Column(Integer, nullable=True, default=1000)
    min_batch_size = Column(Integer, nullable=True, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    reliability_score = Column(Float, nullable=True, default=0.95)
