"""Integration-style tests for Odoo sync pipeline (T025, T026)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.odoo.sync_engine import OdooSyncEngine

pytestmark = pytest.mark.asyncio


def _mock_execute_sequence(*returns):
    async def _execute(*_args, **_kwargs):
        mock = MagicMock()
        for attr, val in returns[-1].items():
            setattr(mock, attr, MagicMock(return_value=val))
        return mock

    async def runner(*args, **kwargs):
        if returns:
            item = returns.pop(0)
            mock = MagicMock()
            for attr, val in item.items():
                setattr(mock, attr, MagicMock(return_value=val))
            return mock
        mock = MagicMock()
        mock.scalar_one_or_none.return_value = None
        mock.first.return_value = None
        return mock

    return runner


async def test_validate_mo_missing_routing_sets_dq_flag():
    """T026: MO with BOM but no routing → MISSING_ROUTING flag."""
    session = AsyncMock()
    tenant_id = uuid4()
    mo_id = uuid4()
    bom_id = uuid4()

    mo = MagicMock()
    mo.id = mo_id
    mo.feasibility_score = 75.0

    routing_result = MagicMock()
    routing_result.first.return_value = None

    session.execute = AsyncMock(return_value=routing_result)
    session.flush = AsyncMock()

    engine = OdooSyncEngine(MagicMock(), tenant_id, session)
    engine._clear_flags = AsyncMock()
    engine._set_flag = AsyncMock()

    await engine._validate_mo(mo, bom_id)

    engine._set_flag.assert_awaited()
    call_args = engine._set_flag.await_args
    assert call_args[0][1] == "MISSING_ROUTING"
    assert mo.feasibility_score is None


async def test_sync_inventory_aggregates_stock_quants():
    """T088: stock.quant levels update product.safety_stock."""
    session = AsyncMock()
    tenant_id = uuid4()
    product = MagicMock()
    product.safety_stock = 0
    product.updated_at = None

    client = MagicMock()
    client.search_read = MagicMock(return_value=[
        {"product_id": [42, "TR-500"], "quantity": 100, "reserved_quantity": 20},
        {"product_id": [42, "TR-500"], "quantity": 50, "reserved_quantity": 10},
    ])

    engine = OdooSyncEngine(client, tenant_id, session)
    engine._get_product = AsyncMock(return_value=product)

    result = await engine.sync_inventory()

    assert result["updated"] == 1
    assert result["errors"] == 0
    assert float(product.safety_stock) == 120.0


async def test_sync_mo_detects_sync_conflict():
    """T025: date change in Odoo after IPE sync resolves via LWW (Odoo wins)."""
    session = AsyncMock()
    tenant_id = uuid4()
    product_id = uuid4()
    bom_id = uuid4()

    product = MagicMock()
    product.id = product_id
    bom = MagicMock()
    bom.id = bom_id

    existing_mo = MagicMock()
    existing_mo.id = uuid4()
    existing_mo.planned_start = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
    existing_mo.planned_end = datetime(2026, 7, 1, 17, 0, tzinfo=UTC)
    existing_mo.erp_synced_at = datetime(2026, 6, 28, 8, 0, tzinfo=UTC)
    existing_mo.updated_at = datetime(2026, 6, 29, 8, 0, tzinfo=UTC)
    existing_mo.version = 1
    existing_mo.ai_schedule_version = 2
    existing_mo.sync_conflict = {"prior": True}
    existing_mo.quantity = 1

    mo_result = MagicMock()
    mo_result.scalar_one_or_none.return_value = existing_mo

    routing_result = MagicMock()
    routing_result.first.return_value = (1,)

    session.execute = AsyncMock(side_effect=[mo_result, routing_result])
    session.flush = AsyncMock()

    engine = OdooSyncEngine(MagicMock(), tenant_id, session)
    engine._get_product = AsyncMock(return_value=product)
    engine._get_bom = AsyncMock(return_value=bom)
    engine._validate_mo = AsyncMock()
    engine._set_flag = AsyncMock()

    with patch("app.odoo.sync_engine.count_tenant_resource", AsyncMock(return_value=0)):
        client = MagicMock()
        client.search_read = MagicMock(return_value=[{
            "id": 501,
            "product_id": [10, "Test"],
            "bom_id": [20, "BOM"],
            "product_qty": 5,
            "date_start": "2026-07-05 08:00:00",
            "date_finished": "2026-07-06 17:00:00",
            "state": "confirmed",
            "write_date": "2026-06-30 09:00:00",
        }])
        engine.client = client

        result = await engine.sync_manufacturing_orders()

    assert result["updated"] == 1
    assert existing_mo.sync_conflict is None
    engine._set_flag.assert_not_awaited()
