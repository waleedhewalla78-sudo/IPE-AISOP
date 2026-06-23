from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.rules import evaluate_event
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])

# In-memory alert store (production would use DB)
_alert_store: dict[str, dict] = {}


class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: str | None = None


@router.get("")
async def list_alerts(
    tenant_id: str | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
):
    """List alerts with optional filtering."""
    tid = tenant_id or tenant_ctx.get()
    alerts = [
        a for a in _alert_store.values()
        if (not tid or a.get("tenant_id") == tid)
        and (not severity or a.get("severity") == severity)
        and (acknowledged is None or a.get("acknowledged") == acknowledged)
    ]
    return APIResponse(
        success=True,
        data={"alerts": alerts, "total": len(alerts)},
        error=None,
    )


@router.get("/{alert_id}")
async def get_alert(alert_id: str):
    """Get a single alert by ID."""
    alert = _alert_store.get(alert_id)
    if not alert:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": f"Alert {alert_id} not found"},
        )
    return APIResponse(success=True, data=alert, error=None)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, req: AlertAcknowledgeRequest | None = None, current_user=Depends(require_roles(["admin", "planner", "supervisor"]))):
    """Acknowledge an alert."""
    alert = _alert_store.get(alert_id)
    if not alert:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": f"Alert {alert_id} not found"},
        )
    alert["acknowledged"] = True
    alert["acknowledged_at"] = datetime.now(UTC).isoformat()
    alert["acknowledged_by"] = req.acknowledged_by if req else None
    return APIResponse(success=True, data=alert, error=None)


@router.get("/rules/active")
async def list_active_rules():
    """List active alert rule thresholds."""
    from app.core.rules import FEASIBILITY_THRESHOLD_LOW, UTILIZATION_THRESHOLD_HIGH
    return APIResponse(
        success=True,
        data={
            "rules": [
                {
                    "name": "feasibility_critical",
                    "description": "MO feasibility score below threshold",
                    "threshold": FEASIBILITY_THRESHOLD_LOW,
                    "severity": "high",
                    "enabled": True,
                },
                {
                    "name": "workcenter_overloaded",
                    "description": "Work center utilization exceeds threshold",
                    "threshold": UTILIZATION_THRESHOLD_HIGH,
                    "severity": "medium",
                    "enabled": True,
                },
            ]
        },
        error=None,
    )


async def store_alert_from_event(event_type: str, payload: dict):
    """Evaluate an event against rules and store any resulting alerts."""
    alerts = evaluate_event(event_type, payload)
    for alert in alerts:
        alert_id = str(uuid4())
        alert_dict = {
            "id": alert_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "tenant_id": alert.tenant_id,
            "entity_id": alert.entity_id,
            "metadata": alert.metadata,
            "acknowledged": False,
            "acknowledged_at": None,
            "acknowledged_by": None,
            "created_at": datetime.now(UTC).isoformat(),
            "event_type": event_type,
        }
        _alert_store[alert_id] = alert_dict
    return alerts
