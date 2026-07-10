from uuid import UUID

from pydantic import BaseModel


class SopVersionCreateRequest(BaseModel):
    cycle_id: UUID
    version_type: str = "baseline"
    version_name: str | None = None
    description: str | None = None
    is_active: bool = True
