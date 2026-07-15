"""Exception lifecycle — detect, enrich, acknowledge, resolve, escalate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_SLA = {
    "critical": (15, 60),
    "high": (30, 240),
    "medium": (120, 1440),
    "low": (480, 4320),
}


class ExceptionLifecycle:
    async def create(
        self,
        db: AsyncSession | None,
        tenant_id: str,
        agent_id: str,
        exception_type: str,
        severity: str,
        title: str,
        description: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        resolution_options: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        ack_m, res_m = DEFAULT_SLA.get(severity, DEFAULT_SLA["medium"])
        payload = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "exception_type": exception_type,
            "severity": severity,
            "title": title,
            "description": description,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": "open",
            "resolution_options": resolution_options or [],
            "ack_due_at": (now + timedelta(minutes=ack_m)).isoformat(),
            "resolve_due_at": (now + timedelta(minutes=res_m)).isoformat(),
            "escalation_level": 0,
            "created_at": now.isoformat(),
        }
        if db is not None:
            import json

            result = await db.execute(
                text("""
                    INSERT INTO cdm_agent_exception (
                        tenant_id, agent_id, exception_type, severity, title, description,
                        entity_type, entity_id, status, resolution_options,
                        ack_due_at, resolve_due_at
                    ) VALUES (
                        :tenant_id, :agent_id, :exception_type, :severity, :title, :description,
                        :entity_type, :entity_id, 'open', CAST(:resolution_options AS jsonb),
                        :ack_due_at, :resolve_due_at
                    )
                    RETURNING id
                """),
                {
                    "tenant_id": UUID(tenant_id),
                    "agent_id": agent_id,
                    "exception_type": exception_type,
                    "severity": severity,
                    "title": title[:300],
                    "description": description,
                    "entity_type": entity_type,
                    "entity_id": UUID(entity_id) if entity_id and _is_uuid(entity_id) else None,
                    "resolution_options": json.dumps(resolution_options or []),
                    "ack_due_at": now + timedelta(minutes=ack_m),
                    "resolve_due_at": now + timedelta(minutes=res_m),
                },
            )
            row = result.first()
            if row:
                payload["id"] = str(row[0])
        else:
            payload["id"] = "dry-run"
        return payload

    def acknowledge(self, exception: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        exception = {**exception, "status": "acknowledged", "acknowledged_at": now, "acknowledged_by": user_id}
        return exception

    def resolve(
        self,
        exception: dict[str, Any],
        selected_option: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            **exception,
            "status": "resolved",
            "resolved_at": now,
            "resolved_by": user_id,
            "selected_option": selected_option,
        }

    def escalate(self, exception: dict[str, Any]) -> dict[str, Any]:
        level = int(exception.get("escalation_level") or 0) + 1
        status = exception.get("status", "open")
        if level >= 2:
            status = "overdue"
        return {**exception, "escalation_level": level, "status": status}


class FinancialDecisionFramework:
    """Present resolution options with full financial impact."""

    def evaluate_options(self, options: list[dict[str, Any]]) -> dict[str, Any]:
        enriched = []
        for opt in options:
            direct = float(opt.get("direct_cost", 0))
            penalty = float(opt.get("penalty_risk", 0))
            revenue = float(opt.get("revenue_impact", 0))
            net = -(direct + penalty) + revenue
            enriched.append(
                {
                    **opt,
                    "net_impact": net,
                    "risk": opt.get("risk", "medium"),
                }
            )
        enriched.sort(key=lambda o: (-o["net_impact"], o.get("direct_cost", 0)))
        recommended = enriched[0] if enriched else None
        return {
            "options": enriched,
            "recommendation": recommended,
            "rationale": (
                f"Recommend {recommended.get('name')} — best net impact {recommended.get('net_impact')}"
                if recommended
                else "No options provided"
            ),
        }


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
