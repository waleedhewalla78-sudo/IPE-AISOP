"""Copilot agent tool loop tests (P8 R1-01)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.copilot_agent import run_agent_streaming, run_agent_with_tools
from app.core.tool_agent_backend import ToolAgentBackend


@pytest.mark.asyncio
async def test_agent_no_client_configured():
    with patch("app.core.copilot_agent.get_tool_agent_backend", return_value=None):
        events = [e async for e in run_agent_with_tools("hello", "tenant-1")]
    assert events[0]["type"] == "response"
    assert "not configured" in events[0]["content"]
    assert "OLLAMA" in events[0]["content"] or "ANTHROPIC" in events[0]["content"]


@pytest.mark.asyncio
async def test_agent_end_turn_response():
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Done"
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("app.core.copilot_agent.get_tool_agent_backend") as mock_backend:
        mock_backend.return_value = ToolAgentBackend(
            provider="anthropic",
            client=mock_client,
            model_config={"model": "m", "max_tokens": 100},
        )
        events = [e async for e in run_agent_with_tools("status?", "tenant-1")]
    assert events[-1]["content"] == "Done"


@pytest.mark.asyncio
async def test_agent_unknown_tool():
    mock_tool = MagicMock()
    mock_tool.type = "tool_use"
    mock_tool.name = "missing_tool"
    mock_tool.input = {}
    mock_tool.id = "tu1"

    mock_response = MagicMock()
    mock_response.stop_reason = "tool_use"
    mock_response.content = [mock_tool]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=[mock_response, MagicMock(stop_reason="end_turn", content=[MagicMock(type="text", text="ok")])])

    with patch("app.core.copilot_agent.get_tool_agent_backend") as mock_backend:
        mock_backend.return_value = ToolAgentBackend(
            provider="anthropic",
            client=mock_client,
            model_config={"model": "m", "max_tokens": 100},
        )
        events = [e async for e in run_agent_with_tools("simulate", "tenant-1", max_iterations=2)]
    tool_calls = [e for e in events if e.get("type") == "tool_call"]
    assert tool_calls and tool_calls[0]["tool"] == "missing_tool"


@pytest.mark.asyncio
async def test_agent_streaming_sse_format():
    async def fake_agent(*args, **kwargs):
        yield {"type": "response", "content": "hi"}

    with patch("app.core.copilot_agent.run_agent_with_tools", return_value=fake_agent()):
        chunks = [c async for c in run_agent_streaming("q", "t1")]
    assert chunks[0].startswith("data: ")
    assert json.loads(chunks[0].replace("data: ", "").strip())["content"] == "hi"
    assert "done" in chunks[-1]
