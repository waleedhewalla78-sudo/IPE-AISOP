"""Tests for TieredRouter LLM fallback chain."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.llm_errors import LLMUnavailableError
from app.core.tiered_router import LLMTier, LLMConfig, TieredRouter


@pytest.mark.asyncio
async def test_call_uses_anthropic_when_configured():
    router = TieredRouter()
    config = LLMConfig(
        provider="anthropic",
        model_name="claude-sonnet-4-20250514",
        max_tokens=1024,
        api_key="test-key",
    )
    with patch.object(router, "_config_for_tier", return_value=config):
        with patch.object(router, "_call_anthropic", AsyncMock(return_value="anthropic reply")) as mock_call:
            result = await router.call("tenant-1", "hello", "system")
    assert result == "anthropic reply"
    mock_call.assert_awaited_once()


@pytest.mark.asyncio
async def test_call_falls_back_to_ollama():
    router = TieredRouter(tenant_tiers={"tenant-1": LLMTier.SAAS})
    with patch.object(router, "_config_for_tier", return_value=None):
        with patch.object(router, "_call_ollama", AsyncMock(return_value="ollama reply")) as mock_ollama:
            result = await router.call("tenant-1", "hello")
    assert result == "ollama reply"
    mock_ollama.assert_awaited_once()


@pytest.mark.asyncio
async def test_call_raises_when_all_providers_fail():
    router = TieredRouter()
    with patch.object(router, "_config_for_tier", return_value=None):
        with patch.object(router, "_call_ollama", AsyncMock(side_effect=RuntimeError("down"))):
            with pytest.raises(LLMUnavailableError):
                await router.call("tenant-1", "hello")


@pytest.mark.asyncio
async def test_get_tier_status_includes_ollama():
    router = TieredRouter(tenant_tiers={"tenant-1": LLMTier.SAAS})
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_resp = AsyncMock()
        mock_resp.is_success = True
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        status = await router.get_tier_status("tenant-1")
    assert "ollama" in status["providers"]
    assert status["routing_enabled"] is False
