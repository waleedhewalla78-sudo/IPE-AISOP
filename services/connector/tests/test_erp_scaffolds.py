"""Unit tests for SAP/D365 connector scaffolds and registry (Gate 10)."""

from __future__ import annotations

import pytest

from app.connectors.d365.sync_engine import D365SyncEngine
from app.connectors.registry import ERPTYPE, ConnectorRegistry
from app.connectors.sap.sync_engine import SAPSyncEngine


class _FakeSession:
    pass


@pytest.mark.asyncio
async def test_sap_sync_all_skipped_scaffold():
    engine = SAPSyncEngine(_FakeSession(), "tenant-1", {})
    result = await engine.sync_all()
    assert result["status"] in ("success", "skipped")
    assert "products" in result


@pytest.mark.asyncio
async def test_d365_sync_all_skipped_scaffold():
    engine = D365SyncEngine(_FakeSession(), "tenant-1", {})
    result = await engine.sync_all()
    assert result["status"] in ("success", "skipped")


def test_registry_sap_engine():
    reg = ConnectorRegistry(_FakeSession())
    engine = reg.get_engine("tenant-1", ERPTYPE.SAP, {})
    assert isinstance(engine, SAPSyncEngine)


def test_registry_d365_engine():
    reg = ConnectorRegistry(_FakeSession())
    engine = reg.get_engine("tenant-1", ERPTYPE.D365, {})
    assert isinstance(engine, D365SyncEngine)


def test_registry_odoo_raises_not_implemented():
    reg = ConnectorRegistry(_FakeSession())
    with pytest.raises(NotImplementedError):
        reg.get_engine("tenant-1", ERPTYPE.ODOO, {})
