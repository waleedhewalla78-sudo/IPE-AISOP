"""LLM client and streaming coverage (P8 R1-01)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.llm_client import _get_client, get_llm_status, query_llm, stream_llm
from app.core.llm_errors import LLMUnavailableError
from app.core.llm_router import LLMProvider


@pytest.mark.asyncio
async def test_query_llm_routing_disabled_success():
    with patch("app.core.llm_client._router.route", return_value="ok answer"):
        assert await query_llm("hi") == "ok answer"


@pytest.mark.asyncio
async def test_query_llm_raises_on_error_prefix():
    with patch("app.core.llm_client._router.route", return_value="LLM error: fail"):
        with pytest.raises(LLMUnavailableError):
            await query_llm("hi")


@pytest.mark.asyncio
async def test_query_llm_routing_enabled():
    with (
        patch("app.config.settings.LLM_ROUTING_ENABLED", True),
        patch("app.core.llm_client._tiered_router.call", return_value="tiered"),
        patch("ipe_shared.middleware.tenant_context.tenant_ctx") as ctx,
    ):
        ctx.get.return_value = "tenant-a"
        assert await query_llm("hi", "sys") == "tiered"


@pytest.mark.asyncio
async def test_get_llm_status_tiered():
    with (
        patch("app.config.settings.LLM_ROUTING_ENABLED", True),
        patch("app.core.llm_client._tiered_router.get_tier_status", return_value={"tier": "saas"}),
    ):
        status = await get_llm_status("t1")
        assert status["tier"] == "saas"


@pytest.mark.asyncio
async def test_get_llm_status_router():
    with (
        patch("app.config.settings.LLM_ROUTING_ENABLED", False),
        patch("app.core.llm_client._router.get_tier_status", return_value={"ok": True}),
    ):
        assert await get_llm_status() == {"ok": True}


def test_get_client_none_when_no_anthropic():
    with patch("app.core.llm_client._router.get_anthropic_client", return_value=None):
        client, cfg = _get_client()
        assert client is None and cfg is None


@pytest.mark.asyncio
async def test_stream_non_anthropic_yields_full():
    mock_router = MagicMock()
    mock_router.provider = LLMProvider.OLLAMA
    with (
        patch("app.core.llm_client._router", mock_router),
        patch("app.core.llm_client.query_llm", return_value="full text"),
    ):
        chunks = [c async for c in stream_llm("p", "s")]
        assert chunks == ["full text"]


@pytest.mark.asyncio
async def test_stream_no_client_yields_not_configured():
    mock_router = MagicMock()
    mock_router.provider = LLMProvider.ANTHROPIC
    mock_router.get_anthropic_client.return_value = None
    with patch("app.core.llm_client._router", mock_router):
        chunks = [c async for c in stream_llm("p")]
        assert chunks == ["LLM service not configured"]


@pytest.mark.asyncio
async def test_stream_fallback_on_exception():
    mock_client = MagicMock()
    mock_client.messages.stream.side_effect = RuntimeError("stream fail")

    mock_router = MagicMock()
    mock_router.provider = LLMProvider.ANTHROPIC
    mock_router.get_anthropic_client.return_value = mock_client

    with (
        patch("app.core.llm_client._router", mock_router),
        patch("app.core.llm_client.query_llm", return_value="fallback answer"),
    ):
        chunks = [c async for c in stream_llm("prompt")]
        assert chunks == ["fallback answer"]
