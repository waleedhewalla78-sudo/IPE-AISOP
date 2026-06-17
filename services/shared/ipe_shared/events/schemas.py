from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    source: str
    tenant_id: UUID
    timestamp: datetime
    data: dict
    correlation_id: str | None = None


class DemandCreatedEvent(BaseModel):
    demand_line_id: UUID
    product_id: UUID
    quantity: float
    required_date: datetime
    demand_type: str


class DemandClassifiedEvent(BaseModel):
    demand_line_id: UUID
    priority_score: float
    demand_type: str


class MaterialCheckRequest(BaseModel):
    product_id: UUID
    quantity: float
    required_date: datetime
    demand_line_id: UUID


class SupplyUpdatedEvent(BaseModel):
    supply_order_id: UUID
    product_id: UUID
    quantity: float
    expected_date: datetime
    status: str
    supplier_id: UUID | None = None


class FeasibilityScoredEvent(BaseModel):
    mo_id: UUID
    overall_score: float
    is_feasible: bool
    primary_constraint: str | None = None
    autonomy_mode: str = "shadow"


class ResolutionProposedEvent(BaseModel):
    mo_id: UUID
    constraint_type: str
    scenario_count: int
    recommended_strategy: str | None = None


class DelayLoggedEvent(BaseModel):
    mo_id: UUID
    source_text: str
    cause_category: str
    confidence: float
