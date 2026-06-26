"""Feasibility WebSocket manager tests (P8 R1-02)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ws import ConnectionManager, _try_avro_decode


def test_try_avro_decode_invalid():
    assert _try_avro_decode(b"not avro") is None


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    mgr = ConnectionManager()
    ws_ok = AsyncMock()
    ws_bad = AsyncMock()
    ws_bad.send_json = AsyncMock(side_effect=Exception("closed"))
    await mgr.connect("tenant-a", ws_ok)
    await mgr.connect("tenant-a", ws_bad)
    await mgr.broadcast("tenant-a", {"score": 90})
    ws_ok.send_json.assert_awaited_once()
    assert ws_bad not in mgr._connections["tenant-a"]


@pytest.mark.asyncio
async def test_disconnect_removes_empty_tenant():
    mgr = ConnectionManager()
    ws = AsyncMock()
    await mgr.connect("t1", ws)
    await mgr.disconnect("t1", ws)
    assert "t1" not in mgr._connections
