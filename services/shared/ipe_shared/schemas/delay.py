from uuid import UUID

from pydantic import BaseModel


class DelayClassifyRequest(BaseModel):
    source_text: str
    mo_id: UUID | None = None


class DelayClassifyResponse(BaseModel):
    cause_category: str
    confidence: float
    delay_minutes: int | None
