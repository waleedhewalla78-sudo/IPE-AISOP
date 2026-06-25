"""War Room aggregation endpoints."""

import logging
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.disruption import DisruptionEvent
from ipe_shared.models.resolution import ResolutionScenario
from ipe_shared.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/war-room", tags=["war-room"])


@router.get("/aggregate")
async def aggregate_supplier_delay(
    supplier_id: str = Query(default="SUP-T2-001"),
    delay_days: float = Query(default=21.0, ge=0),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
) -> APIResponse:
    """Auto-aggregate impacted MOs for a Tier-1/2 supplier delay event."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    headers = {"X-Tenant-ID": str(tenant_id)}
    url = f"{settings.NETWORK_SVC_URL.rstrip('/')}/api/v1/digital-twin/disrupt"
    payload = {
        "disruption_type": "supplier_delay",
        "source_id": supplier_id,
        "delay_days": delay_days,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as cli:
            resp = await cli.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            body = resp.json()
    except Exception as exc:
        logger.warning("War room aggregate failed: %s", exc)
        return APIResponse(
            success=False,
            data=None,
            error={"code": "AGGREGATE_FAILED", "message": str(exc)},
        )

    data = body.get("data") or body
    impacted = data.get("impacted_mos") or []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for mo in impacted:
        delay = float(mo.get("delay_days") or 0)
        if delay > 14:
            severity_counts["critical"] += 1
        elif delay > 7:
            severity_counts["high"] += 1
        elif delay > 3:
            severity_counts["medium"] += 1
        else:
            severity_counts["low"] += 1

    return APIResponse(
        success=True,
        data={
            "disruption_type": data.get("disruption_type", "supplier_delay"),
            "source_id": data.get("source_id", supplier_id),
            "delay_days": data.get("delay_days", delay_days),
            "impacted_mos": impacted,
            "impacted_suppliers": data.get("impacted_suppliers", []),
            "total_cost_impact": data.get("total_cost_impact", 0),
            "severity_counts": severity_counts,
            "aggregated_at_ms": data.get("resolve_time_ms"),
        },
        error=None,
    )


@router.get("/recovery-plan")
async def recovery_plan(
    disruption_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "executive", "manager"])),
) -> APIResponse:
    """Return top 3 recovery options ranked by business score for a disruption."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    disruption = None

    if disruption_id:
        result = await session.execute(
            select(DisruptionEvent).where(
                DisruptionEvent.tenant_id == tid,
                DisruptionEvent.id == UUID(disruption_id),
            )
        )
        disruption = result.scalar_one_or_none()
    else:
        result = await session.execute(
            select(DisruptionEvent)
            .where(
                DisruptionEvent.tenant_id == tid,
                DisruptionEvent.resolved_at.is_(None),
            )
            .order_by(DisruptionEvent.detected_at.desc())
            .limit(1)
        )
        disruption = result.scalar_one_or_none()

    if not disruption:
        scenarios = (
            await session.execute(
                select(ResolutionScenario)
                .where(
                    ResolutionScenario.tenant_id == tid,
                    ResolutionScenario.status == "proposed",
                )
                .order_by(ResolutionScenario.business_score.desc())
                .limit(3)
            )
        ).scalars().all()
        recovery_options = []
        for rank, scenario in enumerate(scenarios, start=1):
            recovery_options.append({
                "rank": rank,
                "scenario_id": str(scenario.id),
                "business_score_usd": round(float(scenario.business_score or 0) * 1000, 2),
                "delivery_impact_days": float(scenario.delivery_impact_days or 0),
                "activity_cost_usd": float(scenario.cost_impact or 0),
                "summary": scenario.description or scenario.strategy,
            })
        return APIResponse(
            success=True,
            data={
                "disruption_id": disruption_id,
                "impacted_mo_count": len({str(s.mo_id) for s in scenarios if s.mo_id}),
                "recovery_options": recovery_options,
            },
            error=None,
        )

    scenario_stmt = (
        select(ResolutionScenario)
        .where(
            ResolutionScenario.tenant_id == tid,
            ResolutionScenario.status == "proposed",
        )
        .order_by(ResolutionScenario.business_score.desc())
        .limit(3)
    )
    if disruption.mo_id:
        scenario_stmt = scenario_stmt.where(ResolutionScenario.mo_id == disruption.mo_id)

    scenarios = (await session.execute(scenario_stmt)).scalars().all()

    if not scenarios:
        headers = {"X-Tenant-ID": str(tenant_id)}
        try:
            async with httpx.AsyncClient(timeout=15.0) as cli:
                if disruption.mo_id:
                    resp = await cli.post(
                        f"{settings.RES_SVC_URL.rstrip('/')}/api/v1/resolution/scenarios",
                        json={"mo_id": str(disruption.mo_id), "constraints": []},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        body = resp.json().get("data") or {}
                        remote = body.get("scenarios") or []
                        recovery_options = []
                        for rank, s in enumerate(remote[:3], start=1):
                            recovery_options.append({
                                "rank": rank,
                                "scenario_id": s.get("id"),
                                "business_score_usd": float(s.get("business_score") or 0) * 1000,
                                "delivery_impact_days": float(s.get("delivery_impact_days") or 0),
                                "activity_cost_usd": float(s.get("cost_impact") or 0),
                                "summary": s.get("description") or s.get("strategy", ""),
                            })
                        meta = disruption.event_metadata or {}
                        impacted = meta.get("impacted_mo_count") or len(meta.get("impacted_mos") or [])
                        return APIResponse(
                            success=True,
                            data={
                                "disruption_id": str(disruption.id),
                                "impacted_mo_count": impacted,
                                "recovery_options": recovery_options,
                            },
                            error=None,
                        )
        except Exception as exc:
            logger.warning("War room recovery-plan res-svc fallback failed: %s", exc)

    recovery_options = []
    for rank, scenario in enumerate(scenarios, start=1):
        recovery_options.append({
            "rank": rank,
            "scenario_id": str(scenario.id),
            "business_score_usd": round(float(scenario.business_score or 0) * 1000, 2),
            "delivery_impact_days": float(scenario.delivery_impact_days or 0),
            "activity_cost_usd": float(scenario.cost_impact or 0),
            "summary": scenario.description or scenario.strategy,
        })

    meta = disruption.event_metadata or {}
    impacted_mo_count = meta.get("impacted_mo_count") or len(meta.get("impacted_mos") or [])
    if disruption.mo_id and not impacted_mo_count:
        impacted_mo_count = 1

    return APIResponse(
        success=True,
        data={
            "disruption_id": str(disruption.id),
            "impacted_mo_count": impacted_mo_count,
            "recovery_options": recovery_options,
        },
        error=None,
    )
