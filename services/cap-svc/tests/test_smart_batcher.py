"""Unit tests — SmartBatcher."""

import pytest

from app.core.smart_batcher import SmartBatcher


@pytest.mark.asyncio
async def test_optimize_batches_reduces_or_keeps_changeover():
    batcher = SmartBatcher()
    mos = [
        {"id": "m1", "product_id": "DT100", "product_family": "DT", "planned_start": "2026-07-15", "planned_end": "2026-07-16", "work_centre_id": "wc1"},
        {"id": "m2", "product_id": "DT250", "product_family": "DT", "planned_start": "2026-07-15", "planned_end": "2026-07-17", "work_centre_id": "wc1"},
        {"id": "m3", "product_id": "DT100", "product_family": "DT", "planned_start": "2026-07-16", "planned_end": "2026-07-18", "work_centre_id": "wc1"},
    ]
    wcs = [{"id": "wc1", "name": "Winding", "changeover_same_family_min": 10, "changeover_different_family_min": 45}]
    results = await batcher.optimize_batches(None, "tenant-1", mos, wcs)
    assert len(results) == 1
    r = results[0]
    assert r["optimised_changeover_min"] <= r["original_changeover_min"]
    assert r["delivery_dates_maintained"] is True
