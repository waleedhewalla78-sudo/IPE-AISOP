"""Unit tests for Odoo bi-directional sync monitor."""

from datetime import UTC, datetime, timedelta

import pytest

from ipe_shared.events.odoo_sync_monitor import (
    HEALTHY_THRESHOLD_SECONDS,
    OdooSyncMonitor,
)


@pytest.fixture
def monitor() -> OdooSyncMonitor:
    return OdooSyncMonitor(service_name="test-connector")


def test_record_sync_tracks_status(monitor: OdooSyncMonitor):
    monitor.record_sync("odoo_to_ipe", "products", "batch", True)
    status = monitor.get_sync_status()
    assert "odoo_to_ipe:products" in status
    assert status["odoo_to_ipe:products"]["direction"] == "odoo_to_ipe"
    assert status["odoo_to_ipe:products"]["entity_type"] == "products"
    assert status["odoo_to_ipe:products"]["healthy"] is True


def test_time_since_last_sync(monitor: OdooSyncMonitor):
    monitor.record_sync("ipe_to_odoo", "resolution", "mo-1", True)
    elapsed = monitor.time_since_last_sync("ipe_to_odoo", "resolution")
    assert elapsed is not None
    assert elapsed < timedelta(seconds=1)


def test_time_since_last_sync_missing_returns_none(monitor: OdooSyncMonitor):
    assert monitor.time_since_last_sync("odoo_to_ipe", "missing") is None


def test_get_sync_status_marks_stale_unhealthy(monitor: OdooSyncMonitor):
    stale = datetime.now(UTC) - timedelta(seconds=HEALTHY_THRESHOLD_SECONDS + 30)
    monitor._last_sync_timestamp["odoo_to_ipe:boms"] = stale
    status = monitor.get_sync_status()
    assert status["odoo_to_ipe:boms"]["healthy"] is False
