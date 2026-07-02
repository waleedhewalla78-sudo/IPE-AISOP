"""Tool-agent backend selection for Copilot chat (/copilot/chat)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.config import settings
from app.core.llm_router import LLMTierRouter
from app.core.ollama_tool_client import OllamaToolClient

_router = LLMTierRouter()


@dataclass(frozen=True)
class ToolAgentBackend:
    provider: Literal["anthropic", "ollama"]
    client: Any
    model_config: dict[str, Any]


def _anthropic_configured() -> bool:
    key = settings.ANTHROPIC_API_KEY
    return bool(key and key != "sk-ant-placeholder")


def _ollama_configured() -> bool:
    return bool(settings.OLLAMA_ENDPOINT_URL.strip())


def get_tool_agent_backend() -> ToolAgentBackend | None:
    """Return the LLM backend for tool-calling Copilot chat.

    Respects IPE_LLM_PRIMARY_PROVIDER:
    - ollama: local Ollama first
    - anthropic: Anthropic SDK only
    - openrouter: not supported for tools — falls through to ollama/anthropic
    - auto: ollama if configured, else anthropic
    """
    pref = (settings.LLM_PRIMARY_PROVIDER or "auto").lower().strip()

    if pref == "ollama" and _ollama_configured():
        client = OllamaToolClient()
        return ToolAgentBackend(
            provider="ollama",
            client=client,
            model_config={
                "model": settings.OLLAMA_MODEL,
                "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
            },
        )

    if pref == "anthropic" and _anthropic_configured():
        client = _router.get_anthropic_client()
        if client is not None:
            return ToolAgentBackend(
                provider="anthropic",
                client=client,
                model_config=settings.MODEL_CONFIG,
            )

    if pref == "auto":
        if _ollama_configured():
            return ToolAgentBackend(
                provider="ollama",
                client=OllamaToolClient(),
                model_config={
                    "model": settings.OLLAMA_MODEL,
                    "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
                },
            )
        if _anthropic_configured():
            client = _router.get_anthropic_client()
            if client is not None:
                return ToolAgentBackend(
                    provider="anthropic",
                    client=client,
                    model_config=settings.MODEL_CONFIG,
                )
        return None

    # openrouter or unknown pref — tools need ollama or anthropic
    if _ollama_configured():
        return ToolAgentBackend(
            provider="ollama",
            client=OllamaToolClient(),
            model_config={
                "model": settings.OLLAMA_MODEL,
                "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
            },
        )
    if _anthropic_configured():
        client = _router.get_anthropic_client()
        if client is not None:
            return ToolAgentBackend(
                provider="anthropic",
                client=client,
                model_config=settings.MODEL_CONFIG,
            )
    return None


def _get_client() -> tuple:
    """Backward-compatible Anthropic client accessor."""
    backend = get_tool_agent_backend()
    if backend is None or backend.provider != "anthropic":
        return None, None
    return backend.client, backend.model_config
