"""
Monitors bi-directional sync health between IPE and Odoo.
Reports sync status to Prometheus metrics.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from prometheus_client import Counter, Gauge

HEALTHY_THRESHOLD_SECONDS = int(os.getenv("IPE_ODOO_SYNC_HEALTHY_THRESHOLD_SEC", "300"))

ODOO_SYNC_EVENTS = Counter(
    "ipe_odoo_sync_events_total",
    "Odoo bi-directional sync events",
    ["service", "direction", "entity_type", "success"],
)

ODOO_SYNC_LAG_SECONDS = Gauge(
    "ipe_odoo_sync_seconds_since_last",
    "Seconds since last sync event by direction and entity type",
    ["service", "direction", "entity_type"],
)

ODOO_SYNC_HEALTHY = Gauge(
    "ipe_odoo_sync_healthy",
    "1 if last sync is within the healthy threshold, else 0",
    ["service", "direction", "entity_type"],
)


class OdooSyncMonitor:
    """Track sync health metrics."""

    def __init__(self, service_name: str = "odoo-connector"):
        self.service_name = service_name
        self._last_sync_timestamp: dict[str, datetime] = {}

    def record_sync(self, direction: str, entity_type: str, entity_id: str, success: bool) -> None:
        """Record a sync event (ipe_to_odoo or odoo_to_ipe)."""
        key = f"{direction}:{entity_type}"
        now = datetime.now(UTC)
        self._last_sync_timestamp[key] = now

        success_label = "true" if success else "false"
        ODOO_SYNC_EVENTS.labels(
            service=self.service_name,
            direction=direction,
            entity_type=entity_type,
            success=success_label,
        ).inc()

        elapsed = 0.0
        ODOO_SYNC_LAG_SECONDS.labels(
            service=self.service_name,
            direction=direction,
            entity_type=entity_type,
        ).set(elapsed)

        ODOO_SYNC_HEALTHY.labels(
            service=self.service_name,
            direction=direction,
            entity_type=entity_type,
        ).set(1 if success else 0)

    def time_since_last_sync(self, direction: str, entity_type: str) -> timedelta | None:
        key = f"{direction}:{entity_type}"
        last_time = self._last_sync_timestamp.get(key)
        if last_time is None:
            return None
        return datetime.now(UTC) - last_time

    def get_sync_status(self) -> dict:
        """Return sync health status for all tracked entities."""
        now = datetime.now(UTC)
        status: dict[str, dict] = {}
        for key, last_time in self._last_sync_timestamp.items():
            elapsed = (now - last_time).total_seconds()
            direction, entity_type = key.split(":", 1)
            ODOO_SYNC_LAG_SECONDS.labels(
                service=self.service_name,
                direction=direction,
                entity_type=entity_type,
            ).set(elapsed)
            healthy = elapsed < HEALTHY_THRESHOLD_SECONDS
            ODOO_SYNC_HEALTHY.labels(
                service=self.service_name,
                direction=direction,
                entity_type=entity_type,
            ).set(1 if healthy else 0)
            status[key] = {
                "direction": direction,
                "entity_type": entity_type,
                "last_sync": last_time.isoformat(),
                "seconds_since_sync": elapsed,
                "healthy": healthy,
            }
        return status


odoo_sync_monitor = OdooSyncMonitor()
