"""LLM API client using Anthropic Claude."""

import os
from collections.abc import AsyncGenerator

from app.config import settings


def _get_client() -> tuple:
    api_key = os.environ.get("IPE_ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY
    if not api_key or api_key == "sk-ant-placeholder":
        return None, None
    try:
        import anthropic

        return anthropic.AsyncAnthropic(api_key=api_key), settings.MODEL_CONFIG
    except ImportError:
        return None, None


def _build_kwargs(prompt: str, system_prompt: str) -> dict:
    model = settings.MODEL_CONFIG.get("model", "claude-sonnet-4-20250514")
    max_tokens = settings.MODEL_CONFIG.get("max_tokens", 1024)
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    return kwargs


async def query_llm(prompt: str, system_prompt: str = "") -> str:
    client, _ = _get_client()
    if client is None:
        return "LLM service not configured"

    try:
        import anthropic

        kwargs = _build_kwargs(prompt, system_prompt)
        message = await client.messages.create(**kwargs)
        return message.content[0].text.strip() if message.content else ""
    except anthropic.APIStatusError as exc:
        return f"LLM API error ({exc.status_code}): {exc.message}"
    except Exception as exc:
        return f"LLM error: {exc}"


async def stream_llm(prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
    """Stream tokens from Anthropic Claude SSE API.

    Falls back to a single yield of the non-streaming response if streaming fails.
    """
    client, _ = _get_client()
    if client is None:
        yield "LLM service not configured"
        return

    try:
        kwargs = _build_kwargs(prompt, system_prompt)
        kwargs["stream"] = True
        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception:
        fallback = await query_llm(prompt, system_prompt)
        yield fallback
