"""Kafka audit event publisher with per-tenant hash chain (tamper detection)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ipe_shared.config import settings

logger = logging.getLogger(__name__)

_chain_state: dict[str, str] = {}
_producer: Any | None = None


def _compute_hash(prev_hash: str | None, payload: dict[str, Any]) -> str:
    material = json.dumps({"prev": prev_hash, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(material.encode()).hexdigest()


async def _get_producer():
    global _producer
    if _producer is None:
        from ipe_shared.events.producer import KafkaProducer

        _producer = KafkaProducer()
        await _producer.start()
    return _producer


async def publish_audit_event(
    tenant_id: str,
    actor_type: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before_state: dict | None = None,
    after_state: dict | None = None,
    rationale: str | None = None,
) -> dict[str, Any] | None:
    if not settings.AUDIT_KAFKA_ENABLED:
        return None

    tenant_key = str(tenant_id)
    prev_hash = _chain_state.get(tenant_key)
    payload = {
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "before_state": json.dumps(before_state) if before_state else None,
        "after_state": json.dumps(after_state) if after_state else None,
        "rationale": rationale,
    }
    chain_hash = _compute_hash(prev_hash, payload)
    _chain_state[tenant_key] = chain_hash

    envelope = {
        "event_id": str(uuid4()),
        "tenant_id": tenant_key,
        "event_type": "audit.v3",
        "occurred_at": datetime.now(UTC).isoformat(),
        "schema_version": 3,
        "prev_hash": prev_hash,
        "chain_hash": chain_hash,
        "payload": payload,
    }

    try:
        producer = await _get_producer()
        topic = settings.AUDIT_KAFKA_TOPIC
        await producer.send_avro(topic, tenant_key, envelope)
        return envelope
    except Exception as exc:
        logger.warning("Kafka audit publish failed: %s", exc)
        return None
