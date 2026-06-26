"""Disruption WebSocket broadcaster tests (P8 R1-02)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ws.disruption import DisruptionBroadcaster, publish_disruption


@pytest.mark.asyncio
async def test_broadcaster_connect_disconnect():
    bc = DisruptionBroadcaster()
    ws = AsyncMock()
    await bc.connect(ws)
    assert ws in bc.connections
    bc.disconnect(ws)
    assert ws not in bc.connections


@pytest.mark.asyncio
async def test_broadcaster_broadcast():
    bc = DisruptionBroadcaster()
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws2.send_text = AsyncMock(side_effect=Exception("closed"))
    await bc.connect(ws1)
    await bc.connect(ws2)
    await bc.broadcast({"type": "disruption", "severity": "high"})
    ws1.send_text.assert_called_once()
    assert ws2 not in bc.connections


@pytest.mark.asyncio
async def test_publish_disruption_delegates():
    with pytest.MonkeyPatch.context() as mp:
        mock_bc = AsyncMock()
        mp.setattr("app.ws.disruption.broadcaster", mock_bc)
        await publish_disruption({"type": "test"})
        mock_bc.broadcast.assert_awaited_once_with({"type": "test"})
