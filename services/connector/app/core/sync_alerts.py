"""Sync failure notifications for Release 1 ops (webhook or structured log)."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def notify_sync_failure(
    *,
    tenant_id: str,
    sync_run_id: str | None,
    status: str,
    error_summary: str | None,
    entity_counts: dict | None = None,
) -> None:
    """Fire-and-forget alert on sync failure/partial. Never raises."""
    payload = {
        "event": "odoo_sync_failure",
        "tenant_id": tenant_id,
        "sync_run_id": sync_run_id,
        "status": status,
        "error_summary": error_summary,
        "entity_counts": entity_counts or {},
    }
    logger.error("Odoo sync alert: %s", json.dumps(payload, default=str))

    webhook = os.getenv("ODOO_SYNC_ALERT_WEBHOOK", "").strip()
    if not webhook:
        return

    try:
        req = urllib.request.Request(
            webhook,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Sync alert webhook responded %s", resp.status)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("Sync alert webhook failed: %s", exc)
