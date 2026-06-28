"""Ollama chat API with tool calling for the Copilot tool agent."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def anthropic_tool_defs_to_ollama(tool_definitions: list[dict]) -> list[dict]:
    """Convert Anthropic-style tool definitions to Ollama/OpenAI function format."""
    ollama_tools: list[dict] = []
    for tool in tool_definitions:
        ollama_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
        )
    return ollama_tools


@dataclass
class OllamaToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class OllamaTurnResult:
    stop_reason: str  # "end_turn" | "tool_use"
    text: str = ""
    tool_calls: list[OllamaToolCall] = field(default_factory=list)
    raw_message: dict[str, Any] = field(default_factory=dict)


class OllamaToolClient:
    """Async client for Ollama /api/chat with tools."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_ENDPOINT_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url)

    async def create_turn(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict],
        system_prompt: str = "",
        max_tokens: int = 1024,
    ) -> OllamaTurnResult:
        if not self.base_url:
            raise RuntimeError("Ollama endpoint URL not configured")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        if system_prompt:
            payload["messages"] = [{"role": "system", "content": system_prompt}, *messages]
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as cli:
            resp = await cli.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        message = data.get("message") or {}
        content = (message.get("content") or "").strip()
        raw_tool_calls = message.get("tool_calls") or []

        if raw_tool_calls:
            parsed: list[OllamaToolCall] = []
            for idx, tc in enumerate(raw_tool_calls):
                fn = tc.get("function") or {}
                name = fn.get("name") or ""
                raw_args = fn.get("arguments")
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args) if raw_args else {}
                    except json.JSONError:
                        args = {}
                elif isinstance(raw_args, dict):
                    args = raw_args
                else:
                    args = {}
                parsed.append(
                    OllamaToolCall(
                        id=tc.get("id") or f"call_{idx}",
                        name=name,
                        arguments=args,
                    )
                )
            return OllamaTurnResult(
                stop_reason="tool_use",
                text=content,
                tool_calls=parsed,
                raw_message=message,
            )

        return OllamaTurnResult(
            stop_reason="end_turn",
            text=content,
            raw_message=message,
        )

    @staticmethod
    def append_assistant_message(messages: list[dict], raw_message: dict) -> None:
        messages.append(
            {
                "role": "assistant",
                "content": raw_message.get("content") or "",
                **({"tool_calls": raw_message.get("tool_calls")} if raw_message.get("tool_calls") else {}),
            }
        )

    @staticmethod
    def append_tool_results(
        messages: list[dict],
        tool_calls: list[OllamaToolCall],
        results: list[dict],
    ) -> None:
        for tc, result in zip(tool_calls, results, strict=False):
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_name": tc.name,
                }
            )
