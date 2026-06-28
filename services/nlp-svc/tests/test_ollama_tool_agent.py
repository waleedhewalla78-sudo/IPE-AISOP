# Test Ollama tool client and Ollama copilot agent loop.

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.copilot_agent import run_agent_with_tools
from app.core.ollama_tool_client import (
    OllamaToolClient,
    OllamaToolCall,
    OllamaTurnResult,
    anthropic_tool_defs_to_ollama,
)
from app.core.tool_agent_backend import ToolAgentBackend


def test_anthropic_tools_to_ollama_format():
    tools = [
        {
            "name": "get_order_status",
            "description": "Get MO status",
            "input_schema": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        }
    ]
    converted = anthropic_tool_defs_to_ollama(tools)
    assert converted[0]["type"] == "function"
    assert converted[0]["function"]["name"] == "get_order_status"
    assert "order_id" in converted[0]["function"]["parameters"]["properties"]


@pytest.mark.asyncio
async def test_ollama_agent_end_turn():
    mock_client = MagicMock(spec=OllamaToolClient)
    mock_client.create_turn = AsyncMock(
        return_value=OllamaTurnResult(stop_reason="end_turn", text="All good", raw_message={"content": "All good"})
    )
    backend = ToolAgentBackend(
        provider="ollama",
        client=mock_client,
        model_config={"model": "llama3.1:8b", "max_tokens": 256},
    )

    with patch("app.core.copilot_agent.get_tool_agent_backend", return_value=backend):
        events = [e async for e in run_agent_with_tools("hello", "tenant-1")]

    assert events[-1]["type"] == "response"
    assert events[-1]["content"] == "All good"


@pytest.mark.asyncio
async def test_ollama_agent_tool_use():
    mock_client = MagicMock(spec=OllamaToolClient)
    mock_client.create_turn = AsyncMock(
        side_effect=[
            OllamaTurnResult(
                stop_reason="tool_use",
                tool_calls=[OllamaToolCall(id="c1", name="get_order_status", arguments={"order_id": "MO-1"})],
                raw_message={
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "c1",
                            "function": {"name": "get_order_status", "arguments": '{"order_id": "MO-1"}'},
                        }
                    ],
                },
            ),
            OllamaTurnResult(stop_reason="end_turn", text="MO-1 is scheduled", raw_message={"content": "MO-1 is scheduled"}),
        ]
    )
    backend = ToolAgentBackend(
        provider="ollama",
        client=mock_client,
        model_config={"model": "llama3.1:8b", "max_tokens": 256},
    )

    with patch("app.core.copilot_agent.get_tool_agent_backend", return_value=backend), patch(
        "app.core.copilot_agent.TOOL_HANDLERS",
        {"get_order_status": AsyncMock(return_value={"status": "scheduled"})},
    ):
        events = [e async for e in run_agent_with_tools("status of MO-1?", "tenant-1", max_iterations=3)]

    tool_calls = [e for e in events if e.get("type") == "tool_call"]
    assert tool_calls and tool_calls[0]["tool"] == "get_order_status"
    assert events[-1]["content"] == "MO-1 is scheduled"


@pytest.mark.asyncio
async def test_tool_backend_prefers_ollama_when_configured(monkeypatch):
    monkeypatch.setenv("IPE_LLM_PRIMARY_PROVIDER", "ollama")
    monkeypatch.setenv("IPE_OLLAMA_ENDPOINT_URL", "http://ollama:11434")
    monkeypatch.setenv("IPE_OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("IPE_ANTHROPIC_API_KEY", "sk-ant-real")

    from app.config import Settings
    from app.core import tool_agent_backend

    tool_agent_backend.settings = Settings()
    backend = tool_agent_backend.get_tool_agent_backend()
    assert backend is not None
    assert backend.provider == "ollama"
