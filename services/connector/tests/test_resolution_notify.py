"""Resolution notify endpoint tests — 014 Stream D."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.erp_odoo import ResolutionNotifyRequest, _resolution_writeback_enabled


def test_writeback_disabled_by_default():
    assert _resolution_writeback_enabled(None) is False


@pytest.mark.asyncio
async def test_resolution_notify_skipped_when_disabled():
    from app.api.v1 import erp_odoo as mod

    with patch.object(mod, "tenant_ctx") as ctx:
        ctx.get.return_value = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        with patch.object(mod, "_resolution_writeback_enabled", return_value=False):
            result = await mod.resolution_notify(
                ResolutionNotifyRequest(
                    mo_id="mo-1",
                    erp_mo_id="42",
                    scenario_id="sc-1",
                    strategy="expedite_internal",
                    approved_by="planner",
                ),
                session=AsyncMock(),
            )
    assert result.success is True
    assert result.data["skipped"] is True


@pytest.mark.asyncio
async def test_resolution_notify_calls_adapter_when_enabled():
    from app.api.v1 import erp_odoo as mod

    tenant = type("T", (), {"config": {}})()
    session = AsyncMock()
    session.execute = AsyncMock(return_value=type("R", (), {"scalar_one_or_none": lambda self: tenant})())

    with patch.object(mod, "tenant_ctx") as ctx:
        ctx.get.return_value = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        with patch.object(mod, "_resolution_writeback_enabled", return_value=True):
            with patch.object(mod, "OdooAdapter") as Adapter:
                inst = Adapter.return_value
                inst.push_resolution_notify = AsyncMock(return_value={"status": "success"})
                result = await mod.resolution_notify(
                    ResolutionNotifyRequest(
                        mo_id="mo-1",
                        erp_mo_id="42",
                        scenario_id="sc-1",
                        strategy="expedite_internal",
                        approved_by="planner",
                    ),
                    session=session,
                )
    assert result.success is True
    inst.push_resolution_notify.assert_awaited_once()
