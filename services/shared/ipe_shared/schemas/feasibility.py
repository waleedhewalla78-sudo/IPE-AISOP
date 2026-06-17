from uuid import UUID

from pydantic import BaseModel


class FeasibilityScoreRequest(BaseModel):
    mo_id: UUID


class FeasibilityScoreResponse(BaseModel):
    mo_id: UUID
    feasibility_score: float
    material_score: float | None
    capacity_score: float | None
    labor_score: float | None
    primary_constraint: str | None
