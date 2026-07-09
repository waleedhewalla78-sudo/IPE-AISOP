"""Ecosystem Integration Bus (EIB) — topic constants and activity normalization."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

# Consolidated republish topic (Sprint 7 roadmap)
ACTIVITY_UNIFIED_TOPIC = "ipe.activity.unified"

# Known tool-specific ingress topics (extensible)
EIB_INGRESS_TOPICS = [
    "ipe.demand.created",
    "ipe.demand.updated",
    "ipe.sync.completed",
    "ipe.feasibility.scored",
    "ipe.schedule.created",
    "ipe.resolution.proposed",
    "ipe.alert.raised",
]

_TOPIC_RE = re.compile(r"^ipe\.([a-z0-9_-]+)\.([a-z0-9_.-]+)$")


def parse_kafka_topic(topic: str) -> tuple[str, str]:
    """Return (source_tool, event_type) from an ipe.* Kafka topic."""
    match = _TOPIC_RE.match(topic.strip())
    if not match:
        return "unknown", topic.replace("ipe.", "", 1)
    tool, event = match.group(1), match.group(2)
    return tool.replace("-", "_"), event.replace(".", "_")


def build_summary(source_tool: str, event_type: str, payload: dict[str, Any]) -> str:
    """Human-readable one-line summary for activity feed."""
    if payload.get("summary"):
        return str(payload["summary"])[:500]
    mo_id = payload.get("mo_id") or payload.get("erp_mo_id")
    if mo_id:
        return f"{source_tool}: {event_type} for MO {mo_id}"
    entity = payload.get("entity") or payload.get("entity_type")
    if entity:
        return f"{source_tool}: {event_type} on {entity}"
    return f"{source_tool}: {event_type}"


def normalize_kafka_message(
    topic: str,
    envelope: dict[str, Any],
    *,
    tenant_id: str | UUID | None = None,
) -> dict[str, Any]:
    """Map a Kafka envelope to ActivityEvent insert fields."""
    payload = envelope.get("payload", envelope)
    if not isinstance(payload, dict):
        payload = {"value": payload}

    tid = (
        tenant_id
        or envelope.get("tenant_id")
        or payload.get("tenant_id")
        or ""
    )
    source_tool, event_type = parse_kafka_topic(topic)
    occurred_raw = envelope.get("occurred_at") or payload.get("occurred_at")
    if isinstance(occurred_raw, str):
        try:
            occurred_at = datetime.fromisoformat(occurred_raw.replace("Z", "+00:00"))
        except ValueError:
            occurred_at = datetime.now(UTC)
    elif isinstance(occurred_raw, datetime):
        occurred_at = occurred_raw
    else:
        occurred_at = datetime.now(UTC)

    event_id = envelope.get("event_id") or payload.get("event_id")
    idempotency_key = str(event_id) if event_id else f"{topic}:{envelope.get('id', '')}"

    severity = str(payload.get("severity") or envelope.get("severity") or "info").lower()
    if severity not in ("info", "warning", "critical"):
        severity = "warning" if "fail" in event_type or "alert" in event_type else "info"

    entity_type = payload.get("entity_type") or payload.get("entity")
    entity_id = payload.get("entity_id") or payload.get("mo_id")

    return {
        "tenant_id": str(tid) if tid else None,
        "source_tool": source_tool,
        "event_type": event_type,
        "actor_id": payload.get("actor_id") or envelope.get("actor_id"),
        "entity_type": str(entity_type) if entity_type else None,
        "entity_id": str(entity_id) if entity_id else None,
        "summary": build_summary(source_tool, event_type, payload),
        "metadata": {
            "topic": topic,
            "payload": payload,
        },
        "severity": severity,
        "occurred_at": occurred_at,
        "idempotency_key": idempotency_key or None,
    }
