"""Phase 3 contextual intelligence + meeting prep APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.core.contextual_intelligence import ContextualIntelligence, MeetingPreparator
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/copilot", tags=["copilot-phase3"])
_intel = ContextualIntelligence()
_meeting = MeetingPreparator()


class MorningBriefRequest(BaseModel):
    planner_name: str = "Ahmed"
    data: dict[str, Any] = Field(default_factory=dict)


class MeetingPrepRequest(BaseModel):
    meeting_type: str = "production_meeting"
    live_data: dict[str, Any] = Field(default_factory=dict)


@router.post("/morning-brief")
async def morning_brief(
    req: MorningBriefRequest | None = None,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    req = req or MorningBriefRequest()
    data = await _intel.generate_morning_brief(
        x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        req.planner_name,
        req.data
        or {
            "exceptions": [
                {"severity": "high", "title": "Copper wire stockout in 5 days", "entity_type": "mo"}
            ],
            "predictions": [{"trend": "crisis_approaching", "recommended_action": "Act on MO-ST-006"}],
            "otd": {"current_pct": 89, "trend_direction": "stable", "total_mos": 47},
            "stockout_risks": ["RM-CW25 days of stock 3 < lead time 7"],
        },
    )
    return APIResponse(success=True, data=data, error=None)


@router.post("/meeting-prep")
async def meeting_prep(req: MeetingPrepRequest):
    data = _meeting.prepare(req.meeting_type, req.live_data)
    return APIResponse(success=True, data=data, error=None)


@router.get("/meeting/{meeting_type}")
async def meeting_get(meeting_type: str):
    data = _meeting.prepare(meeting_type)
    return APIResponse(success=True, data=data, error=None)
