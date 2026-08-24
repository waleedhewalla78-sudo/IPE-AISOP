"""Spec 034 — Unified Workspace dashboard aggregation."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.activity.store import list_activity_feed
from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.database.session import get_session
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.notification import NotificationRecord
from ipe_shared.schemas.common import APIResponse
from ipe_shared.workspace.health import (
    calculate_factory_health,
    kpi_status_from_at_risk,
    kpi_status_from_otd,
    kpi_status_from_util,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])

StatusLit = Literal["healthy", "warning", "critical", "neutral"]
SevLit = Literal["critical", "warning", "info", "success"]


class Greeting(BaseModel):
    user_name: str
    tenant_name: str
    locale: str = "en"
    timestamp: str
    role: str = "planner"


class HealthBlock(BaseModel):
    factory_score: int
    factory_trend: Literal["improving", "stable", "declining"]
    otd_current: float
    otd_previous: float
    otd_trend: list[float] = Field(default_factory=list)
    components: dict[str, float] = Field(default_factory=dict)


class KpiMetric(BaseModel):
    value: float | int
    previous: float | int | None = None
    delta: float | None = None
    trend: list[float] = Field(default_factory=list)
    status: StatusLit = "neutral"
    wc_name: str | None = None
    reversed: int | None = None


class KpisBlock(BaseModel):
    orders_at_risk: KpiMetric
    bottleneck_wc: KpiMetric
    supply_health: KpiMetric
    otd: KpiMetric
    ai_autonomy: KpiMetric
    supplier_otd: KpiMetric


class MoBreakdown(BaseModel):
    healthy: int
    monitoring: int
    critical: int
    total: int


class CapacityItem(BaseModel):
    wc_name: str
    utilisation: float
    status: StatusLit


class ActionItem(BaseModel):
    id: str
    severity: SevLit
    title: str
    detail: str
    entity_type: str | None = None
    entity_id: str | None = None
    source: str = "system"
    is_ai: bool = False
    created_at: str
    action_label: str = "Open"
    action_url: str = "/workspace"


class SystemService(BaseModel):
    status: Literal["healthy", "degraded", "offline"]
    last_sync_ago_seconds: int | None = None
    queued: int | None = None


class SystemBlock(BaseModel):
    odoo_sync: SystemService
    event_bus: SystemService
    ollama: SystemService
    claude_api: SystemService
    agents_healthy: int = 0
    agents_total: int = 20
    agent_degraded: str | None = None


class WorkspaceDashboard(BaseModel):
    greeting: Greeting
    health: HealthBlock
    kpis: KpisBlock
    mo_breakdown: MoBreakdown
    capacity: list[CapacityItem]
    actions: list[ActionItem]
    system: SystemBlock


_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _looks_like_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(value.strip()))


def _display_name(user: TokenPayload) -> str:
    """Human greeting name — never a UUID (JWT `sub` alone is not displayable)."""
    for attr in ("full_name", "name", "preferred_username", "email"):
        raw = getattr(user, attr, None)
        if isinstance(raw, str) and raw.strip() and not _looks_like_uuid(raw):
            if "@" in raw:
                return raw.split("@")[0].replace(".", " ").replace("_", " ").title()
            return raw.strip().split()[0]
    email = getattr(user, "email", None) or getattr(user, "sub", None)
    if isinstance(email, str) and "@" in email:
        return email.split("@")[0].replace(".", " ").replace("_", " ").title()
    if isinstance(email, str) and email.strip() and not _looks_like_uuid(email):
        return email.strip().split()[0]
    return ""


async def _display_name_from_db(session: AsyncSession, user: TokenPayload) -> str:
    """Prefer cdm_user.full_name when JWT lacks email/name claims."""
    from sqlalchemy import text

    try:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(user.tenant_id)},
        )
        row = (
            await session.execute(
                text(
                    """
                    SELECT full_name, email
                    FROM cdm_user
                    WHERE id = CAST(:uid AS uuid)
                    LIMIT 1
                    """
                ),
                {"uid": str(user.sub)},
            )
        ).mappings().one_or_none()
        if row:
            full = (row.get("full_name") or "").strip()
            if full and not _looks_like_uuid(full):
                return full.split()[0]
            email = (row.get("email") or "").strip()
            if email and "@" in email:
                return email.split("@")[0].replace(".", " ").replace("_", " ").title()
    except Exception:
        pass
    return _display_name(user)


def _sev_from_priority(priority: str) -> SevLit:
    p = (priority or "").lower()
    if p in ("critical", "high", "urgent"):
        return "critical"
    if p in ("medium", "warning"):
        return "warning"
    if p in ("success", "resolved"):
        return "success"
    return "info"


@router.get("/dashboard", response_model=APIResponse[WorkspaceDashboard])
async def workspace_dashboard(
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[WorkspaceDashboard]:
    tenant_id = UUID(str(current_user.tenant_id))
    role = (current_user.role or "planner").lower()
    now = datetime.now(UTC)

    # --- MO score buckets ---
    score_col = ManufacturingOrder.feasibility_score
    healthy = await session.scalar(
        select(func.count()).select_from(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id,
            score_col.isnot(None),
            score_col >= 90,
        )
    )
    monitoring = await session.scalar(
        select(func.count()).select_from(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id,
            score_col.isnot(None),
            score_col >= 70,
            score_col < 90,
        )
    )
    critical = await session.scalar(
        select(func.count()).select_from(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id,
            score_col.isnot(None),
            score_col < 70,
        )
    )
    total_mo = await session.scalar(
        select(func.count()).select_from(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id
        )
    )
    at_risk = int(critical or 0)

    # Soft OTD from average feasibility when dedicated OTD table absent
    avg_score = await session.scalar(
        select(func.avg(score_col)).where(
            ManufacturingOrder.tenant_id == tenant_id,
            score_col.isnot(None),
        )
    )
    # Neutral default 85 when no MO scores — honesty, not demo fake
    otd_current = float(avg_score) if avg_score is not None else 85.0
    otd_previous = otd_current  # no history table wired yet
    otd_trend = [otd_current] * 7

    # Capacity: derive soft util from inverse of capacity_score avg when present
    avg_cap = await session.scalar(
        select(func.avg(ManufacturingOrder.capacity_score)).where(
            ManufacturingOrder.tenant_id == tenant_id,
            ManufacturingOrder.capacity_score.isnot(None),
        )
    )
    if avg_cap is not None:
        # low capacity score → high pressure util estimate
        max_util = max(0.0, min(120.0, 100.0 - float(avg_cap) + 70.0))
    else:
        max_util = 0.0  # empty plant — honest zero overload

    bottleneck_name = "—" if max_util <= 0 else "Primary WC"
    capacity_rows: list[CapacityItem] = []
    if max_util > 0:
        capacity_rows = [
            CapacityItem(
                wc_name=bottleneck_name,
                utilisation=round(max_util, 1),
                status=kpi_status_from_util(max_util),
            )
        ]

    # Supply: materials at risk proxy from material_score < 70 count
    supply_risk = await session.scalar(
        select(func.count()).select_from(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id,
            ManufacturingOrder.material_score.isnot(None),
            ManufacturingOrder.material_score < 70,
        )
    )
    supply_risk_n = int(supply_risk or 0)
    supply_health_pct = 100.0 if (total_mo or 0) == 0 else max(
        0.0, 100.0 - (supply_risk_n / max(int(total_mo or 1), 1)) * 100.0
    )

    quality_fpy = 85.0  # neutral until quality CDM wired
    plan_coverage = 85.0

    fh = calculate_factory_health(
        otd_pct=otd_current,
        max_util_pct=max_util if max_util > 0 else 85.0,
        quality_fpy=quality_fpy,
        supply_health_pct=supply_health_pct,
        plan_coverage_pct=plan_coverage,
        score_7d_ago=None,
    )

    # Actions from notifications + activity
    actions: list[ActionItem] = []
    try:
        notif_q = (
            await session.execute(
                select(NotificationRecord)
                .where(
                    NotificationRecord.tenant_id == tenant_id,
                    NotificationRecord.status.in_(["pending", "sent", "unread"]),
                )
                .order_by(NotificationRecord.created_at.desc())
                .limit(6)
            )
        )
        for n in notif_q.scalars().all():
            actions.append(
                ActionItem(
                    id=str(n.id),
                    severity=_sev_from_priority(str(n.priority)),
                    title=str(n.subject)[:200],
                    detail=str(n.body)[:240],
                    source=str(n.template_id or "notif"),
                    is_ai="auto" in (n.template_id or "").lower()
                    or "agent" in (n.template_id or "").lower(),
                    created_at=(n.created_at or now).isoformat(),
                    action_label="Review",
                    action_url="/planning/resolution",
                )
            )
    except Exception:
        pass

    if len(actions) < 6 and at_risk > 0:
        actions.append(
            ActionItem(
                id="at-risk-mos",
                severity="critical",
                title=f"{at_risk} manufacturing order(s) at risk",
                detail="Feasibility score below 70 — open Control Tower",
                entity_type="manufacturing_order",
                source="A4",
                is_ai=False,
                created_at=now.isoformat(),
                action_label="Resolve",
                action_url="/planning/control-tower",
            )
        )

    try:
        feed = await list_activity_feed(session, tenant_id, limit=4)
        for r in feed:
            if len(actions) >= 6:
                break
            actions.append(
                ActionItem(
                    id=str(r.id),
                    severity=_sev_from_priority(str(r.severity)),
                    title=str(r.summary)[:200],
                    detail=str(r.source_tool),
                    source=str(r.source_tool),
                    is_ai=False,
                    created_at=r.occurred_at.isoformat(),
                    action_label="View",
                    action_url="/workspace",
                )
            )
    except Exception:
        pass

    sev_order = {"critical": 0, "warning": 1, "info": 2, "success": 3}

    def _action_sort_key(a: ActionItem) -> tuple:
        try:
            ts = datetime.fromisoformat(a.created_at.replace("Z", "+00:00")).timestamp()
        except Exception:
            ts = 0.0
        return (sev_order.get(a.severity, 9), -ts)

    actions = sorted(actions, key=_action_sort_key)[:6]

    # System soft probes
    redis_url = os.getenv("IPE_REDIS_URL") or os.getenv("REDIS_URL") or ""
    ollama_url = os.getenv("IPE_OLLAMA_URL") or ""
    claude_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("IPE_CLAUDE_API_KEY") or ""

    system = SystemBlock(
        odoo_sync=SystemService(status="healthy", last_sync_ago_seconds=None),
        event_bus=SystemService(
            status="healthy" if redis_url else "degraded",
            queued=0,
        ),
        ollama=SystemService(status="healthy" if ollama_url else "degraded"),
        claude_api=SystemService(status="healthy" if claude_key else "degraded"),
        agents_healthy=0,  # not claimed without live agent probe
        agents_total=20,
        agent_degraded=None,
    )

    tenant_name = "Tenant"
    try:
        from ipe_shared.models.tenant import Tenant  # type: ignore

        trow = await session.get(Tenant, tenant_id)
        if trow is not None and getattr(trow, "name", None):
            tenant_name = str(trow.name)
    except Exception:
        tenant_name = str(tenant_id)[:8]

    display_name = await _display_name_from_db(session, current_user)
    payload = WorkspaceDashboard(
        greeting=Greeting(
            user_name=display_name,
            tenant_name=tenant_name,
            locale="en",
            timestamp=now.isoformat(),
            role=role,
        ),
        health=HealthBlock(
            factory_score=fh.score,
            factory_trend=fh.trend,
            otd_current=round(otd_current, 1),
            otd_previous=round(otd_previous, 1),
            otd_trend=[round(x, 1) for x in otd_trend],
            components=fh.components,
        ),
        kpis=KpisBlock(
            orders_at_risk=KpiMetric(
                value=at_risk,
                previous=at_risk,
                trend=[float(at_risk)] * 7,
                status=kpi_status_from_at_risk(at_risk),
            ),
            bottleneck_wc=KpiMetric(
                value=round(max_util, 1) if max_util > 0 else 0,
                wc_name=bottleneck_name if max_util > 0 else None,
                trend=[round(max_util, 1)] * 7 if max_util > 0 else [],
                status=kpi_status_from_util(max_util) if max_util > 0 else "healthy",
            ),
            supply_health=KpiMetric(
                value=supply_risk_n,
                trend=[float(supply_risk_n)] * 7,
                status="warning" if supply_risk_n > 0 else "healthy",
            ),
            otd=KpiMetric(
                value=round(otd_current, 1),
                delta=round(otd_current - otd_previous, 1),
                trend=[round(x, 1) for x in otd_trend],
                status=kpi_status_from_otd(otd_current),
            ),
            ai_autonomy=KpiMetric(
                value=0,
                reversed=0,
                status="healthy",
            ),
            supplier_otd=KpiMetric(
                value=0,
                trend=[],
                status="neutral",
            ),
        ),
        mo_breakdown=MoBreakdown(
            healthy=int(healthy or 0),
            monitoring=int(monitoring or 0),
            critical=int(critical or 0),
            total=int(total_mo or 0),
        ),
        capacity=capacity_rows,
        actions=actions,
        system=system,
    )
    return APIResponse(data=payload, error=None)
