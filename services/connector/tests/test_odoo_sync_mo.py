"""Unit tests for MO sync upsert logic (mock session + Odoo client)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.odoo.sync_engine import OdooSyncEngine

pytestmark = pytest.mark.asyncio


def _mock_client(mo_records: list[dict]) -> MagicMock:
    client = MagicMock()
    client.search_read = MagicMock(return_value=mo_records)
    return client


def _scalar_result(obj):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=obj)
    return result


async def test_sync_mo_skips_without_bom():
    session = AsyncMock()
    tenant_id = uuid4()
    product = MagicMock()
    product.id = uuid4()
    product.erp_source_id = "10"

    session.execute = AsyncMock(side_effect=[
        _scalar_result(product),  # _get_product
        _scalar_result(None),   # _get_bom by erp id
        _scalar_result(None),   # _get_bom by product
    ])

    client = _mock_client([{
        "id": 999,
        "product_id": [10, "Test Product"],
        "bom_id": False,
        "product_qty": 1,
        "state": "draft",
        "write_date": "2026-06-29 09:00:00",
    }])
    engine = OdooSyncEngine(client, tenant_id, session)
    result = await engine.sync_manufacturing_orders()
    assert result["skipped"] == 1
    assert result["synced"] == 0
    session.add.assert_not_called()


async def test_sync_mo_creates_new():
    session = AsyncMock()
    tenant_id = uuid4()
    product_id = uuid4()
    bom_id = uuid4()

    product = MagicMock()
    product.id = product_id
    product.erp_source_id = "10"

    bom = MagicMock()
    bom.id = bom_id

    async def mock_execute(*_args, **_kwargs):
        mock = MagicMock()
        mock.scalar_one_or_none.return_value = None
        mock.first.return_value = (1,)
        mock.scalar.return_value = 1
        mock.fetchone.return_value = None
        return mock

    session.execute = AsyncMock(side_effect=mock_execute)
    session.flush = AsyncMock()

    # Patch lookups
    engine = OdooSyncEngine(_mock_client([]), tenant_id, session)
    engine._get_product = AsyncMock(return_value=product)
    engine._get_bom = AsyncMock(return_value=bom)

    client = _mock_client([{
        "id": 501,
        "product_id": [10, "Test"],
        "bom_id": [20, "BOM"],
        "product_qty": 5,
        "date_start": "2026-07-01 08:00:00",
        "date_finished": "2026-07-02 17:00:00",
        "state": "confirmed",
        "write_date": "2026-06-29 09:00:00",
    }])
    engine.client = client
    result = await engine.sync_manufacturing_orders()
    assert result["synced"] == 1
    session.add.assert_called()
