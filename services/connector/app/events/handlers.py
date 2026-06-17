import hashlib
import hmac
import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ipe_shared.database.connection import get_engine
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.models.tenant import Tenant

logger = logging.getLogger(__name__)


async def _post_to_odoo(
    tenant_id: str,
    action_type: str,
    data: dict,
) -> None:
    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            logger.error("Tenant %s not found", tenant_id)
            return

        erp_base_url = tenant.erp_base_url
        api_secret = tenant.api_secret

        if not erp_base_url or not api_secret:
            logger.error("Tenant %s missing erp_base_url or api_secret", tenant_id)
            return

        odoo_action_url = f"{erp_base_url.rstrip('/')}/ipe/action"

        payload = {
            "action_type": action_type,
            "data": data,
        }

        body_bytes = json.dumps(payload).encode("utf-8")

        signature = hmac.new(
            api_secret.encode(), body_bytes, hashlib.sha256,
        ).hexdigest()

        headers = {
            "X-IPE-Signature": signature,
            "X-Tenant-ID": str(tenant_id),
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(odoo_action_url, content=body_bytes, headers=headers)
                resp.raise_for_status()
                logger.info(
                    "Odoo %s success: action=%s status=%s",
                    action_type, action_type, resp.status_code,
                )
        except httpx.RequestError as e:
            logger.error("Failed to send %s to Odoo: %s", action_type, e)


def _parse_event(event: dict) -> EventEnvelope | None:
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        try:
            return EventEnvelope(**value)
        except Exception as exc:
            logger.warning("Failed to parse EventEnvelope: %s", exc)
            return None
    logger.warning("Unrecognized event format: %s", type(value))
    return None


async def handle_mo_auto_confirmed(event: dict):
    envelope = _parse_event(event)
    if not envelope:
        return

    data = envelope.data
    tenant_id = str(envelope.tenant_id)
    mo_id = data.get("mo_id", "")
    feasibility_score = data.get("feasibility_score", 0)
    autonomy_mode = data.get("autonomy_mode", "shadow")
    reason = data.get("reason", "")

    logger.info(
        "Processing auto_confirmed: mo_id=%s tenant=%s score=%s mode=%s",
        mo_id, tenant_id, feasibility_score, autonomy_mode,
    )

    await _post_to_odoo(
        tenant_id=tenant_id,
        action_type="confirm_mo",
        data={
            "mo_id": mo_id,
            "feasibility_score": feasibility_score,
            "autonomy_mode": autonomy_mode,
            "reason": reason,
        },
    )


async def handle_feasibility_scored(event: dict):
    envelope = _parse_event(event)
    if not envelope:
        return

    data = envelope.data
    tenant_id = str(envelope.tenant_id)
    mo_id = data.get("mo_id", "")
    overall_score = data.get("overall_score", 0)
    primary_constraint = data.get("primary_constraint")
    risk_level = data.get("risk_level", "medium")

    logger.info(
        "Processing feasibility_scored: mo_id=%s score=%s constraint=%s",
        mo_id, overall_score, primary_constraint,
    )

    await _post_to_odoo(
        tenant_id=tenant_id,
        action_type="sync_feasibility",
        data={
            "mo_id": mo_id,
            "overall_score": overall_score,
            "primary_constraint": primary_constraint,
            "risk_level": risk_level,
        },
    )


async def handle_reconciliation_completed(event: dict):
    envelope = _parse_event(event)
    if not envelope:
        return

    data = envelope.data
    tenant_id = str(envelope.tenant_id)
    mo_id = data.get("mo_id", "")
    time_variance_pct = data.get("time_variance_pct", 0)
    yield_variance_pct = data.get("yield_variance_pct", 0)

    logger.info(
        "Processing reconciliation_completed: mo_id=%s time_var=%s yield_var=%s",
        mo_id, time_variance_pct, yield_variance_pct,
    )

    await _post_to_odoo(
        tenant_id=tenant_id,
        action_type="sync_reconciliation",
        data={
            "mo_id": mo_id,
            "time_variance_pct": time_variance_pct,
            "yield_variance_pct": yield_variance_pct,
        },
    )


async def handle_demand_classified(event: dict):
    envelope = _parse_event(event)
    if not envelope:
        return

    data = envelope.data
    tenant_id = str(envelope.tenant_id)
    mo_id = data.get("mo_id") or data.get("demand_line_id", "")
    demand_type = data.get("demand_type", "")
    priority_score = data.get("priority_score", 0)

    logger.info(
        "Processing demand_classified: mo_id=%s type=%s priority=%s",
        mo_id, demand_type, priority_score,
    )

    await _post_to_odoo(
        tenant_id=tenant_id,
        action_type="sync_demand_classification",
        data={
            "mo_id": mo_id,
            "demand_type": demand_type,
            "priority_score": priority_score,
        },
    )
