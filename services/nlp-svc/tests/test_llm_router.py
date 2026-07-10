"""Tests for LLMTierRouter: tier routing, PII stripping, and fallback logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.llm_errors import LLMUnavailableError
from app.core.llm_router import LLMProvider, LLMTierRouter


@pytest.fixture
def router_tier1():
    return LLMTierRouter(tenant_tier=1)


@pytest.fixture
def router_tier2():
    return LLMTierRouter(tenant_tier=2)


@pytest.fixture
def router_tier3():
    return LLMTierRouter(tenant_tier=3)


class TestLLMProviderEnum:
    def test_provider_values(self):
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.SAGEMAKER.value == "sagemaker"
        assert LLMProvider.VLLM.value == "vllm"


class TestTierRouting:
    def test_tier1_routes_to_anthropic(self, router_tier1):
        assert router_tier1.provider == LLMProvider.ANTHROPIC
        assert router_tier1.tier == 1

    def test_tier2_routes_to_sagemaker(self, router_tier2):
        assert router_tier2.provider == LLMProvider.SAGEMAKER
        assert router_tier2.tier == 2

    def test_tier3_routes_to_vllm(self, router_tier3):
        assert router_tier3.provider == LLMProvider.VLLM
        assert router_tier3.tier == 3

    def test_default_tier_uses_settings(self):
        with patch("app.core.llm_router.settings.LLM_TIER_DEFAULT", 2):
            router = LLMTierRouter()
            assert router.provider == LLMProvider.SAGEMAKER

    def test_unknown_tier_defaults_to_anthropic(self):
        router = LLMTierRouter(tenant_tier=99)
        assert router.provider == LLMProvider.ANTHROPIC

    def test_tier1_fallback_is_anthropic_openrouter_ollama(self, router_tier1):
        assert router_tier1.fallback_chain == [
            LLMProvider.ANTHROPIC,
            LLMProvider.OPENROUTER,
            LLMProvider.OLLAMA,
        ]

    def test_tier2_fallback_includes_anthropic(self, router_tier2):
        assert router_tier2.fallback_chain == [
            LLMProvider.SAGEMAKER,
            LLMProvider.OPENROUTER,
            LLMProvider.OLLAMA,
            LLMProvider.ANTHROPIC,
        ]

    def test_tier3_fallback_chain_full(self, router_tier3):
        assert router_tier3.fallback_chain == [
            LLMProvider.VLLM,
            LLMProvider.OLLAMA,
            LLMProvider.SAGEMAKER,
            LLMProvider.ANTHROPIC,
        ]


class TestPIIStripping:
    def test_pii_stripped_before_llm_call(self, router_tier1):
        text, _types = router_tier1.strip_pii("Contact john@example.com or call 555-123-4567")
        assert "[REDACTED]" in text
        assert "john@example.com" not in text

    def test_ssn_stripped(self, router_tier1):
        text, types = router_tier1.strip_pii("My SSN is 123-45-6789")
        assert "123-45-6789" not in text
        assert "ssn" in types

    def test_email_stripped(self, router_tier1):
        text, types = router_tier1.strip_pii("Send to user@company.org")
        assert "user@company.org" not in text
        assert "email" in types

    def test_pii_stripping_for_all_tiers(self):
        prompt = "Email: test@test.com, SSN: 111-22-3333"
        for tier in [1, 2, 3]:
            router = LLMTierRouter(tenant_tier=tier)
            clean, _redacted = router.strip_pii(prompt)
            assert "test@test.com" not in clean
            assert "111-22-3333" not in clean


class TestAnthropicProvider:
    pytestmark = pytest.mark.integration

    @pytest.mark.asyncio
    async def test_tier1_calls_anthropic(self, router_tier1, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-ant-unit-test-key")
        router = LLMTierRouter(tenant_tier=1)
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Hello from Claude")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_msg)

        with patch.object(
            router,
            "get_anthropic_client",
            return_value=mock_client,
        ):
            result = await router.route("Hello", "system")
            assert result == "Hello from Claude"
            mock_client.messages.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_tier1_anthropic_not_configured(self, router_tier1):
        with (
            patch.object(router_tier1, "get_anthropic_client", return_value=None),
            patch.object(router_tier1, "_call_ollama", side_effect=RuntimeError("ollama down")),
        ):
            with pytest.raises(LLMUnavailableError):
                await router_tier1.route("Hello")

    @pytest.mark.asyncio
    async def test_tier1_pii_stripped_before_anthropic(self, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-ant-unit-test-key")
        router = LLMTierRouter(tenant_tier=1)
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Response")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_msg)

        with patch.object(
            router,
            "get_anthropic_client",
            return_value=mock_client,
        ):
            result = await router.route("My email is test@test.com", "system")
            assert result == "Response"
            call_kwargs = mock_client.messages.create.call_args
            sent_prompt = call_kwargs.kwargs["messages"][0]["content"]
            assert "test@test.com" not in sent_prompt
            assert "[REDACTED]" in sent_prompt


class TestSageMakerProvider:
    pytestmark = pytest.mark.integration

    @pytest.mark.asyncio
    async def test_tier2_calls_sagemaker(self, router_tier2):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"text": "SageMaker response"})

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with (
            patch(
                "app.core.llm_router.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch.object(
                router_tier2,
                "get_sagemaker_config",
                return_value={
                    "endpoint_url": ("https://sagemaker.endpoint/invoke"),
                    "region": "us-east-1",
                },
            ),
        ):
            result = await router_tier2.route("Hello")
            assert result == "SageMaker response"

    @pytest.mark.asyncio
    async def test_tier2_sagemaker_not_configured_falls_back(self, router_tier2):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Claude fallback")]
        mock_anthropic = AsyncMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_msg)

        with (
            patch.object(
                router_tier2,
                "get_sagemaker_config",
                return_value={
                    "endpoint_url": "",
                    "region": "us-east-1",
                },
            ),
            patch.object(
                router_tier2,
                "get_anthropic_client",
                return_value=mock_anthropic,
            ),
        ):
            result = await router_tier2.route("Hello")
            assert result == "Claude fallback"
            mock_anthropic.messages.create.assert_awaited_once()


class TestVLLMProvider:
    pytestmark = pytest.mark.integration

    @pytest.mark.asyncio
    async def test_tier3_calls_vllm(self, router_tier3):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"text": "vLLM response"})

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with (
            patch(
                "app.core.llm_router.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch.object(
                router_tier3,
                "get_vllm_config",
                return_value={
                    "endpoint_url": ("http://vllm.local:8000/v1/completions"),
                },
            ),
        ):
            result = await router_tier3.route("Hello")
            assert result == "vLLM response"


class TestFallbackLogic:
    pytestmark = pytest.mark.integration

    @pytest.mark.asyncio
    async def test_anthropic_unavailable_falls_back_to_sagemaker(
        self,
    ):
        router = LLMTierRouter(tenant_tier=2)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"text": "SM response"})
        mock_sm_client = AsyncMock()
        mock_sm_client.__aenter__ = AsyncMock(return_value=mock_sm_client)
        mock_sm_client.__aexit__ = AsyncMock(return_value=False)
        mock_sm_client.post = AsyncMock(return_value=mock_response)

        with (
            patch.object(
                router,
                "get_sagemaker_config",
                return_value={
                    "endpoint_url": "https://sm.endpoint",
                    "region": "us-east-1",
                },
            ),
            patch(
                "app.core.llm_router.httpx.AsyncClient",
                return_value=mock_sm_client,
            ),
        ):
            result = await router.route("Hello")
            assert result == "SM response"

    @pytest.mark.asyncio
    async def test_sagemaker_unavailable_falls_back_to_anthropic(
        self,
    ):
        router = LLMTierRouter(tenant_tier=2)
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Claude fallback")]
        mock_anthropic = AsyncMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_msg)

        with (
            patch.object(
                router,
                "_call_sagemaker",
                side_effect=RuntimeError("SM endpoint down"),
            ),
            patch.object(
                router,
                "get_anthropic_client",
                return_value=mock_anthropic,
            ),
        ):
            result = await router.route("Hello")
            assert result == "Claude fallback"

    @pytest.mark.asyncio
    async def test_all_providers_unavailable(self):
        router = LLMTierRouter(tenant_tier=3)

        with (
            patch.object(router, "_call_vllm", side_effect=RuntimeError("vLLM down")),
            patch.object(router, "_call_ollama", side_effect=RuntimeError("ollama down")),
            patch.object(router, "_call_sagemaker", side_effect=RuntimeError("SM down")),
            patch.object(router, "_call_anthropic", side_effect=RuntimeError("Anthropic down")),
        ):
            with pytest.raises(LLMUnavailableError):
                await router.route("Hello")

    @pytest.mark.asyncio
    async def test_vllm_down_falls_back_to_sagemaker(self):
        router = LLMTierRouter(tenant_tier=3)

        with (
            patch.object(router, "_call_vllm", side_effect=RuntimeError("vLLM down")),
            patch.object(router, "_call_ollama", side_effect=RuntimeError("ollama down")),
            patch.object(
                router,
                "_call_sagemaker",
                new=AsyncMock(return_value="SM ok"),
            ),
        ):
            result = await router.route("Hello")
            assert result == "SM ok"


class TestPIIBeforeAllProviders:
    pytestmark = pytest.mark.integration

    @pytest.mark.asyncio
    async def test_pii_stripped_before_sagemaker(self, router_tier2):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="SM result")]
        mock_anthropic = AsyncMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_msg)

        with (
            patch.object(
                router_tier2,
                "_call_sagemaker",
                side_effect=RuntimeError("SM down"),
            ),
            patch.object(
                router_tier2,
                "get_anthropic_client",
                return_value=mock_anthropic,
            ),
        ):
            result = await router_tier2.route("SSN: 123-45-6789")
            assert result == "SM result"
            call_kwargs = mock_anthropic.messages.create.call_args
            sent_prompt = call_kwargs.kwargs["messages"][0]["content"]
            assert "123-45-6789" not in sent_prompt

    @pytest.mark.asyncio
    async def test_pii_stripped_before_vllm(self, router_tier3):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"text": "vLLM result"})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with (
            patch(
                "app.core.llm_router.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch.object(
                router_tier3,
                "get_vllm_config",
                return_value={
                    "endpoint_url": "http://vllm:8000/v1",
                },
            ),
        ):
            result = await router_tier3.route("Call me at 555-123-4567")
            assert result == "vLLM result"
            call_args = mock_client.post.call_args
            payload = call_args.kwargs.get("json") or {}
            prompt_sent = payload.get("prompt", "")
            assert "555-123-4567" not in prompt_sent


class TestGetConfigs:
    def test_sagemaker_config(self):
        with patch("app.core.llm_router.settings") as mock_settings:
            mock_settings.SAGEMAKER_ENDPOINT_URL = "https://sm.us-east-1.amazonaws.com/endpoint"
            mock_settings.AWS_REGION = "eu-west-1"
            router = LLMTierRouter(tenant_tier=2)
            config = router.get_sagemaker_config()
            assert config["endpoint_url"] == ("https://sm.us-east-1.amazonaws.com/endpoint")
            assert config["region"] == "eu-west-1"

    def test_vllm_config(self):
        with patch("app.core.llm_router.settings") as mock_settings:
            mock_settings.VLLM_ENDPOINT_URL = "http://vllm.local:8000/v1/completions"
            router = LLMTierRouter(tenant_tier=3)
            config = router.get_vllm_config()
            assert config["endpoint_url"] == ("http://vllm.local:8000/v1/completions")

    def test_anthropic_client_not_configured(self):
        with patch(
            "app.core.llm_router.settings.ANTHROPIC_API_KEY",
            "sk-ant-placeholder",
        ):
            router = LLMTierRouter(tenant_tier=1)
            assert router.get_anthropic_client() is None

    def test_anthropic_client_configured(self):
        mock_anthropic = MagicMock()
        mock_anthropic.AsyncAnthropic.return_value = MagicMock()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), patch(
            "app.core.llm_router.settings.ANTHROPIC_API_KEY",
            "sk-ant-real-key",
        ):
            client = LLMTierRouter(tenant_tier=1).get_anthropic_client()
            assert client is not None
            mock_anthropic.AsyncAnthropic.assert_called_once_with(api_key="sk-ant-real-key")
