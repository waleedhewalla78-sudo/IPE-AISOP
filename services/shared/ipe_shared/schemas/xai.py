from typing import Optional

from pydantic import BaseModel


class XAIExplanation(BaseModel):
    constraints: list[str] = []
    assumptions: list[str] = []
    confidence_score: float = 0.0
    contributing_factors: dict[str, float] = {}