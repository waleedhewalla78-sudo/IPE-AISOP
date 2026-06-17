from uuid import UUID

from pydantic import BaseModel


class WorkCenterResponse(BaseModel):
    id: UUID
    name: str
    capacity_hours_per_day: float
    oee: float
    cost_per_hour: float | None
    status: str
