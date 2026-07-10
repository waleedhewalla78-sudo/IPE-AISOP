"""LLM API client - delegates to TieredRouter or LLMTierRouter based on config.

R2 fallback chain (via LLMTierRouter when LLM_ROUTING_ENABLED=false):
Anthropic -> OpenRouter -> Ollama -> LLMUnavailableError.
"""

from collections.abc import AsyncGenerator

from app.config import settings
from app.core.llm_errors import LLMUnavailableError
from app.core.llm_router import LLMProvider, LLMTierRouter, R2_CLOUD_FALLBACK
from app.core.tiered_router import TieredRouter
from app.core.tool_agent_backend import _get_client, get_tool_agent_backend

_router = LLMTierRouter()
_tiered_router = TieredRouter()

__all__ = [
    "query_llm",
    "get_llm_status",
    "stream_llm",
    "get_r2_fallback_chain",
    "_get_client",
    "get_tool_agent_backend",
]


def get_r2_fallback_chain() -> list[str]:
    """Return configured R2 cloud fallback provider order."""
    return [provider.value for provider in R2_CLOUD_FALLBACK]


async def query_llm(prompt: str, system_prompt: str = "") -> str:
    """Query LLM through tiered router with PII stripping."""
    from ipe_shared.middleware.tenant_context import tenant_ctx

    if settings.LLM_ROUTING_ENABLED:
        tenant_id = tenant_ctx.get() or ""
        return await _tiered_router.call(tenant_id, prompt, system_prompt)

    result = await _router.route(prompt, system_prompt)
    if isinstance(result, str) and result.startswith("LLM error:"):
        raise LLMUnavailableError(result)
    return result


async def get_llm_status(tenant_id: str = "") -> dict:
    """Return LLM tier health for admin UI."""
    if settings.LLM_ROUTING_ENABLED:
        return await _tiered_router.get_tier_status(tenant_id)
    return await _router.get_tier_status()


async def stream_llm(prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
    """Stream tokens from the LLM.

    Falls back to a single yield of the non-streaming response if streaming fails.
    PII is stripped before sending.
    """
    from ipe_shared.security.pii import strip_pii_from_prompt

    clean_prompt, _ = strip_pii_from_prompt(prompt)
    clean_system, _ = strip_pii_from_prompt(system_prompt)

    if _router.provider != LLMProvider.ANTHROPIC:
        result = await query_llm(prompt, system_prompt)
        yield result
        return

    client = _router.get_anthropic_client()
    if client is None:
        yield "LLM service not configured"
        return

    try:
        kwargs = {
            "model": settings.MODEL_CONFIG.get("model", "claude-sonnet-4-20250514"),
            "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": clean_prompt}],
            "stream": True,
        }
        if clean_system:
            kwargs["system"] = clean_system

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception:
        fallback = await query_llm(prompt, system_prompt)
        yield fallback
