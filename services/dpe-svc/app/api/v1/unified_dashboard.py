"""Unified dashboard aggregation (Sprint 7 Tier 1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.activity.store import list_activity_feed
from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.database.session import get_session
from ipe_shared.models.delay_event import DelayEvent
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard-unified"])


class UnifiedKpiCard(BaseModel):
    label: str
    value: str
    source_tool: str
    link_path: str | None = None


class UnifiedActivityItem(BaseModel):
    id: str
    summary: str
    source_tool: str
    severity: str
    occurred_at: str


class UnifiedDashboardPayload(BaseModel):
    role: str
    kpis: list[UnifiedKpiCard]
    recent_activity: list[UnifiedActivityItem]
    pending_actions: list[str] = Field(default_factory=list)


@router.get("/unified", response_model=APIResponse[UnifiedDashboardPayload])
async def unified_dashboard(
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[UnifiedDashboardPayload]:
    tenant_id = UUID(str(current_user.tenant_id))
    role = (current_user.role or "planner").lower()

    mo_count = await session.scalar(
        select(func.count()).select_from(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id
        )
    )
    at_risk = await session.scalar(
        select(func.count()).select_from(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id,
            ManufacturingOrder.feasibility_score.isnot(None),
            ManufacturingOrder.feasibility_score < 70,
        )
    )
    alert_count = await session.scalar(
        select(func.count()).select_from(DelayEvent).where(
            DelayEvent.tenant_id == tenant_id
        )
    )

    kpis: list[UnifiedKpiCard] = [
        UnifiedKpiCard(
            label="Manufacturing orders",
            value=str(mo_count or 0),
            source_tool="planning",
            link_path="/planning/control-tower",
        ),
        UnifiedKpiCard(
            label="Orders at risk",
            value=str(at_risk or 0),
            source_tool="fea",
            link_path="/planning/resolution",
        ),
        UnifiedKpiCard(
            label="Active delay alerts",
            value=str(alert_count or 0),
            source_tool="command",
            link_path="/command/war-room",
        ),
    ]

    if role in ("admin", "executive", "manager"):
        kpis.append(
            UnifiedKpiCard(
                label="Cross-tool events (24h)",
                value=str(len(await list_activity_feed(session, tenant_id, limit=100))),
                source_tool="eib",
                link_path="/workspace",
            )
        )

    activity_rows = await list_activity_feed(session, tenant_id, limit=15)
    recent = [
        UnifiedActivityItem(
            id=str(r.id),
            summary=r.summary,
            source_tool=r.source_tool,
            severity=r.severity,
            occurred_at=r.occurred_at.isoformat(),
        )
        for r in activity_rows
    ]

    pending: list[str] = []
    if (at_risk or 0) > 0:
        pending.append(f"Review {at_risk} at-risk manufacturing orders")
    if (alert_count or 0) > 0:
        pending.append(f"Triage {alert_count} delay alerts in War Room")

    return APIResponse(
        data=UnifiedDashboardPayload(
            role=role,
            kpis=kpis,
            recent_activity=recent,
            pending_actions=pending,
        ),
        error=None,
    )
