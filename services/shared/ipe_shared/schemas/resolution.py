from uuid import UUID

from pydantic import BaseModel


class ScenarioProposeRequest(BaseModel):
    mo_id: UUID


class ScenarioResponse(BaseModel):
    id: UUID
    mo_id: UUID
    strategy: str
    description: str
    delivery_impact_days: float | None
    cost_impact: float | None
    business_score: float | None
    status: str


class ApproveRequest(BaseModel):
    scenario_id: UUID
