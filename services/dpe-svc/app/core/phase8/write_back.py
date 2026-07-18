"""Phase 8 write-back safety — dry-run, approval gates, mock execute."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from ipe_shared.feature_flags.flags import get_feature_flags
from ipe_shared.roles import AgentRoleContext

# In-memory store for unit tests / when DB session not provided
_WRITE_BACK_STORE: dict[str, dict[str, Any]] = {}


def reset_write_back_store() -> None:
    _WRITE_BACK_STORE.clear()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def propose_write_back(
    *,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
    new_value: str,
    old_value: str | None = None,
    field_name: str | None = None,
    action: str = "update",
    requested_by: str = "system",
    user_role: str = "supervisor",
    financial_impact: float = 0.0,
    dry_run: bool = True,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a write-back proposal. Never hits live Odoo in Wave 1."""
    can = AgentRoleContext.can_execute(user_role, "approve_resolution", financial_impact)
    status = "dry_run" if dry_run else ("pending_approval" if not can else "pending_approval")
    entry = {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "field_name": field_name,
        "old_value": old_value,
        "new_value": new_value,
        "action": action,
        "status": status,
        "dry_run": dry_run,
        "requested_by": requested_by,
        "approved_by": None,
        "financial_impact": financial_impact,
        "error_message": None,
        "attempt_count": 0,
        "payload": payload or {},
        "is_live": False,
        "created_at": _now().isoformat(),
        "executed_at": None,
        "rollback_deadline": None,
        "role_can_approve": AgentRoleContext.can_execute(
            user_role, "approve_resolution", financial_impact
        ),
        "escalation_required": AgentRoleContext.escalation_required(user_role, financial_impact),
        "live_writeback_enabled": get_feature_flags().is_enabled("ipe.odoo.live_writeback"),
        "ph1_02_blocker": "PH1-02 OPEN — live Odoo write-back not claimed",
    }
    if dry_run:
        entry["preview"] = {
            "would_change": f"{entity_type}/{entity_id}.{field_name or '*'}",
            "from": old_value,
            "to": new_value,
            "executed": False,
        }
    _WRITE_BACK_STORE[entry["id"]] = entry
    return deepcopy(entry)


def approve_write_back(
    entry_id: str,
    *,
    approved_by: str,
    user_role: str = "manager",
    execute: bool = False,
) -> dict[str, Any]:
    entry = _WRITE_BACK_STORE.get(entry_id)
    if not entry:
        return {"error": "not_found", "id": entry_id}

    impact = float(entry.get("financial_impact") or 0.0)
    if not AgentRoleContext.can_execute(user_role, "approve_resolution", impact):
        entry["status"] = "pending_approval"
        entry["error_message"] = "insufficient_authority"
        return deepcopy(entry)

    entry["approved_by"] = approved_by
    entry["dry_run"] = False

    live_flag = get_feature_flags().is_enabled("ipe.odoo.live_writeback")
    if execute and live_flag:
        # Still MOCK in Wave 1 — never claim live Odoo success
        entry["status"] = "executed"
        entry["is_live"] = False
        entry["attempt_count"] = int(entry.get("attempt_count") or 0) + 1
        entry["executed_at"] = _now().isoformat()
        entry["rollback_deadline"] = (_now() + timedelta(hours=4)).isoformat()
        entry["mock_odoo"] = True
        entry["message"] = "MOCK execute against mock-odoo — PH1-02 required for live"
    elif execute:
        entry["status"] = "queued"
        entry["is_live"] = False
        entry["message"] = (
            "Write-back approved and queued; live flag ipe.odoo.live_writeback=false "
            "(PH1-02 OPEN). Not sent to Odoo."
        )
    else:
        entry["status"] = "pending_approval"
        entry["message"] = "Approved for queue; call again with execute=true to mock-queue"
    return deepcopy(entry)


def list_write_backs(tenant_id: str | None = None) -> list[dict[str, Any]]:
    items = list(_WRITE_BACK_STORE.values())
    if tenant_id:
        items = [i for i in items if i.get("tenant_id") == tenant_id]
    return deepcopy(items)


def get_write_back(entry_id: str) -> dict[str, Any] | None:
    entry = _WRITE_BACK_STORE.get(entry_id)
    return deepcopy(entry) if entry else None
