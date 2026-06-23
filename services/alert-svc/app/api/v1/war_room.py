"""War Room aggregation endpoints."""

import logging

import httpx
from fastapi import APIRouter, Depends, Query

from app.config import settings
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
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
