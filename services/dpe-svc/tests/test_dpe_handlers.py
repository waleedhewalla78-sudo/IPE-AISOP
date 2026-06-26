"""DPE event handler unit tests — R2-03."""

import pytest

from app.events.handlers import handle_demand_created


@pytest.mark.asyncio
async def test_handle_demand_created_missing_id():
    await handle_demand_created({})
    await handle_demand_created({"demand_line_id": None})


@pytest.mark.asyncio
async def test_handle_demand_created_no_row(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(one_or_none=MagicMock(return_value=None)))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_factory = MagicMock(return_value=mock_session)
    mock_ctx = MagicMock()
    mock_ctx.get.return_value = None

    monkeypatch.setattr("app.events.handlers.get_engine", lambda: MagicMock())
    monkeypatch.setattr("app.events.handlers.async_sessionmaker", lambda *a, **k: mock_factory)
    monkeypatch.setattr("app.events.handlers.tenant_ctx", mock_ctx)

    await handle_demand_created({"demand_line_id": "dl-1"})
