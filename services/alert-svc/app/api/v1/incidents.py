from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ipe_shared.auth.rbac import require_roles
from ipe_shared.integrations.alertmanager import AlertManagerClient
from ipe_shared.integrations.pagerduty import PagerDutyClient
from ipe_shared.schemas.common import APIResponse, APIError

router = APIRouter(prefix="/incidents", tags=["incidents"])

_pd_client = PagerDutyClient()
_am_client = AlertManagerClient()


class PagerDutyIncidentRequest(BaseModel):
    summary: str
    severity: str = "medium"
    source: str = "ipe"
    component: str = ""
    group: str = ""
    details: dict[str, Any] | None = None
    incident_key: str | None = None


class AlertManagerAlertRequest(BaseModel):
    name: str
    severity: str = "warning"
    source: str = "ipe"
    labels: dict[str, str] | None = None
    annotations: dict[str, str] | None = None
    generator_url: str = ""


@router.post("/pagerduty")
async def trigger_pagerduty_incident(
    req: PagerDutyIncidentRequest,
    current_user=Depends(require_roles(["admin"])),
):
    result = await _pd_client.send_alert(
        action="trigger",
        summary=req.summary,
        severity=req.severity,
        source=req.source,
        component=req.component,
        group=req.group,
        details=req.details,
        incident_key=req.incident_key,
    )
    if result is None:
        return APIResponse(
            success=False,
            data=None,
            error=APIError(code="PAGERDUTY_NOT_CONFIGURED", message="PagerDuty routing key not set or send failed"),
        )
    return APIResponse(success=True, data=result, error=None)


@router.post("/alertmanager")
async def trigger_alertmanager_alert(
    req: AlertManagerAlertRequest,
    current_user=Depends(require_roles(["admin"])),
):
    ok = await _am_client.send_alert(
        name=req.name,
        severity=req.severity,
        source=req.source,
        labels=req.labels,
        annotations=req.annotations,
        generator_url=req.generator_url,
    )
    if not ok:
        return APIResponse(
            success=False,
            data=None,
            error=APIError(code="ALERTMANAGER_NOT_CONFIGURED", message="Alertmanager URL not set or send failed"),
        )
    return APIResponse(success=True, data={"status": "sent"}, error=None)


@router.get("/alerts")
async def list_alertmanager_alerts(
    current_user=Depends(require_roles(["admin"])),
):
    alerts = await _am_client.list_alerts()
    return APIResponse(
        success=True,
        data={"alerts": alerts, "total": len(alerts)},
        error=None,
    )