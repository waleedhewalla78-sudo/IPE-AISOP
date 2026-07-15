"""Phase 3 auto-generated S&OP executive brief."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.executive_brief import SopExecutiveBrief
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/sop", tags=["sop-phase3"])
_brief = SopExecutiveBrief()


class BriefRequest(BaseModel):
    demand: dict[str, Any] | None = None
    supply: dict[str, Any] | None = None
    finance: dict[str, Any] | None = None
    decisions: list[dict[str, Any]] | None = None


@router.post("/executive-brief")
async def executive_brief(req: BriefRequest | None = None):
    req = req or BriefRequest()
    data = _brief.generate(req.model_dump(exclude_none=True) or None)
    return APIResponse(success=True, data=data, error=None)


@router.get("/executive-brief")
async def executive_brief_get():
    data = _brief.generate()
    return APIResponse(success=True, data=data, error=None)
