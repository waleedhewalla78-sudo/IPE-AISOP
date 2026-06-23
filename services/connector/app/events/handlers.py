import hashlib
import hmac
import json
import logging
from uuid import UUID

import httpx
from sqlalchemy import select, text
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


def _extract_kafka_payload(event: dict) -> tuple[str, str, dict] | None:
    """Parse cap-svc build_envelope (payload) or standard EventEnvelope (data)."""
    value = event.value if hasattr(event, "value") else event
    if not isinstance(value, dict):
        return None
    tenant_id = str(value.get("tenant_id", ""))
    event_id = str(value.get("event_id", ""))
    data = value.get("data") or value.get("payload") or {}
    if not tenant_id and data.get("tenant_id"):
        tenant_id = str(data["tenant_id"])
    if not tenant_id:
        return None
    return tenant_id, event_id, data


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


async def handle_resolution_approved(event: dict):
    """Consume ipe.resolution.approved, write to cdm_export_queue."""
    envelope = _parse_event(event)
    if not envelope:
        return

    data = envelope.data
    tenant_id = str(envelope.tenant_id)
    event_id = str(envelope.event_id)

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        try:
            # Idempotency check on event_id
            existing = await session.execute(
                text("SELECT 1 FROM cdm_export_queue WHERE event_type = :et AND payload->>'event_id' = :eid LIMIT 1"),
                {"et": "ipe.resolution.approved", "eid": event_id},
            )
            if existing.scalar_one_or_none():
                logger.info("Duplicate ipe.resolution.approved event %s, skipping", event_id)
                return

            odoo_payload = {
                "event_id": event_id,
                "mo_id": data.get("mo_id", ""),
                "scenario_id": data.get("scenario_id", ""),
                "strategy": data.get("strategy", ""),
                "approved_by": data.get("approved_by", "system"),
                "delivery_impact_days": data.get("delivery_impact_days", 0),
                "cost_impact": data.get("cost_impact", 0),
            }

            await session.execute(
                text("""
                    INSERT INTO cdm_export_queue
                        (tenant_id, payload, event_type, status, retry_count)
                    VALUES
                        (:tid, :payload, :evt, 'pending', 0)
                """),
                {
                    "tid": UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
                    "payload": odoo_payload,
                    "evt": "ipe.resolution.approved",
                },
            )
            await session.commit()
            logger.info("Enqueued resolution.approved event %s for tenant %s", event_id, tenant_id)
        except Exception as e:
            logger.error("Failed to enqueue resolution.approved: %s", e)


async def handle_schedule_approved(event: dict):
    """Consume ipe.schedule.approved and sync activated MOs to Odoo."""
    parsed = _extract_kafka_payload(event)
    if not parsed:
        envelope = _parse_event(event)
        if not envelope:
            return
        tenant_id = str(envelope.tenant_id)
        event_id = str(envelope.event_id)
        data = envelope.data
    else:
        tenant_id, event_id, data = parsed

    activated = data.get("activated") or []
    approved_by = data.get("approved_by", "system")

    logger.info(
        "Processing schedule_approved: tenant=%s count=%s event=%s",
        tenant_id, len(activated), event_id,
    )

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        try:
            if event_id:
                existing = await session.execute(
                    text(
                        "SELECT 1 FROM cdm_export_queue "
                        "WHERE event_type = :et AND payload->>'event_id' = :eid LIMIT 1"
                    ),
                    {"et": "ipe.schedule.approved", "eid": event_id},
                )
                if existing.scalar_one_or_none():
                    logger.info("Duplicate ipe.schedule.approved event %s, skipping", event_id)
                    return

            odoo_payload = {
                "event_id": event_id,
                "approved_by": approved_by,
                "activated": activated,
            }
            await session.execute(
                text("""
                    INSERT INTO cdm_export_queue
                        (tenant_id, payload, event_type, status, retry_count)
                    VALUES
                        (:tid, :payload, :evt, 'pending', 0)
                """),
                {
                    "tid": UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
                    "payload": odoo_payload,
                    "evt": "ipe.schedule.approved",
                },
            )
            await session.commit()
        except Exception as exc:
            logger.error("Failed to enqueue schedule.approved: %s", exc)

    for item in activated:
        erp_mo_id = item.get("erp_mo_id")
        if not erp_mo_id:
            continue
        await _post_to_odoo(
            tenant_id=tenant_id,
            action_type="reschedule_mo",
            data={
                "mo_id": erp_mo_id,
                "planned_date_finished": item.get("new_planned_end"),
                "planned_date_start": item.get("new_planned_start"),
                "approved_by": approved_by,
                "ipe_schedule_version": item.get("ai_schedule_version"),
            },
        )


async def handle_po_suggested(event: dict):
    """Consume ipe.po.suggested, create draft purchase orders in Odoo."""
    envelope = _parse_event(event)
    if not envelope:
        return

    data = envelope.data
    tenant_id = str(envelope.tenant_id)
    suggestions = data.get("suggestions", [])
    total_cost = data.get("total_cost", 0)

    logger.info(
        "Processing po_suggested: tenant=%s count=%s total_cost=%s",
        tenant_id, len(suggestions), total_cost,
    )

    for suggestion in suggestions:
        po_payload = {
            "product_id": suggestion.get("product_id", ""),
            "supplier_id": suggestion.get("supplier_id", ""),
            "supplier_name": suggestion.get("supplier_name", ""),
            "order_quantity": suggestion.get("order_quantity", 0),
            "unit_cost": suggestion.get("unit_cost", 0),
            "total_cost": suggestion.get("total_cost", 0),
            "suggested_order_date": suggestion.get("suggested_order_date", ""),
            "expected_delivery_date": suggestion.get("expected_delivery_date", ""),
            "priority": suggestion.get("priority", "normal"),
        }

        await _post_to_odoo(
            tenant_id=tenant_id,
            action_type="create_rfq",
            data=po_payload,
        )
