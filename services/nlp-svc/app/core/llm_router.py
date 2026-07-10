"""Tiered LLM routing based on tenant configuration.

Tier 1 (SaaS/Professional): Anthropic Claude with PII stripping.
Tier 2 (Enterprise/Private VPC): AWS SageMaker endpoint.
Tier 3 (On-Prem): Local vLLM endpoint.

Each tier falls back to the next available provider if the configured
one is unavailable. PII is stripped before sending prompts to any
provider.
"""

import logging
from enum import Enum

import httpx

from app.config import settings
from ipe_shared.security.pii import strip_pii_from_prompt

from app.core.llm_errors import LLMUnavailableError

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    SAGEMAKER = "sagemaker"
    VLLM = "vllm"


TIER_PROVIDER_MAP: dict[int, LLMProvider] = {
    1: LLMProvider.ANTHROPIC,
    2: LLMProvider.SAGEMAKER,
    3: LLMProvider.VLLM,
}

TIER_FALLBACK: dict[int, list[LLMProvider]] = {
    1: [LLMProvider.ANTHROPIC, LLMProvider.OPENROUTER, LLMProvider.OLLAMA],
    2: [LLMProvider.SAGEMAKER, LLMProvider.OPENROUTER, LLMProvider.OLLAMA, LLMProvider.ANTHROPIC],
    3: [LLMProvider.VLLM, LLMProvider.OLLAMA, LLMProvider.SAGEMAKER, LLMProvider.ANTHROPIC],
}

R2_CLOUD_FALLBACK: list[LLMProvider] = [
    LLMProvider.ANTHROPIC,
    LLMProvider.OPENROUTER,
    LLMProvider.OLLAMA,
]


def _fallback_chain_for_tier(tier: int) -> list[LLMProvider]:
    chain = list(TIER_FALLBACK.get(tier, [LLMProvider.ANTHROPIC]))
    pref = (settings.LLM_PRIMARY_PROVIDER or "auto").lower().strip()

    ollama_ok = bool(settings.OLLAMA_ENDPOINT_URL.strip())
    openrouter_ok = bool(settings.OPENROUTER_API_KEY)
    anthropic_ok = bool(
        settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "sk-ant-placeholder"
    )

    def _prepend(provider: LLMProvider, base: list[LLMProvider]) -> list[LLMProvider]:
        return [provider] + [p for p in base if p != provider]

    if pref == "ollama" and ollama_ok:
        chain = _prepend(LLMProvider.OLLAMA, chain)
    elif pref == "openrouter" and openrouter_ok:
        chain = _prepend(LLMProvider.OPENROUTER, chain)
    elif pref == "anthropic" and anthropic_ok:
        chain = _prepend(LLMProvider.ANTHROPIC, chain)
    elif pref == "auto":
        auto_chain: list[LLMProvider] = []
        if anthropic_ok:
            auto_chain.append(LLMProvider.ANTHROPIC)
        if openrouter_ok:
            auto_chain.append(LLMProvider.OPENROUTER)
        if ollama_ok:
            auto_chain.append(LLMProvider.OLLAMA)
        if auto_chain:
            chain = auto_chain
    else:
        if openrouter_ok:
            chain = _prepend(LLMProvider.OPENROUTER, chain)

    return chain


_CALL_METHODS: dict[LLMProvider, str] = {
    LLMProvider.OPENROUTER: "_call_openrouter",
    LLMProvider.ANTHROPIC: "_call_anthropic",
    LLMProvider.OLLAMA: "_call_ollama",
    LLMProvider.SAGEMAKER: "_call_sagemaker",
    LLMProvider.VLLM: "_call_vllm",
}


class LLMTierRouter:
    """Routes LLM requests to the provider matching the tenant tier."""

    def __init__(self, tenant_tier: int | None = None) -> None:
        self._tier: int = tenant_tier or settings.LLM_TIER_DEFAULT
        self._provider: LLMProvider = TIER_PROVIDER_MAP.get(self._tier, LLMProvider.ANTHROPIC)
        self._fallback_chain: list[LLMProvider] = _fallback_chain_for_tier(self._tier)
        if self._fallback_chain:
            self._provider = self._fallback_chain[0]

    @property
    def tier(self) -> int:
        return self._tier

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    @property
    def fallback_chain(self) -> list[LLMProvider]:
        return list(self._fallback_chain)

    def strip_pii(self, prompt: str) -> tuple[str, list[str]]:
        """Strip PII from a prompt before sending to any LLM provider."""
        return strip_pii_from_prompt(prompt)

    def get_anthropic_client(self):
        """Return an Anthropic AsyncAnthropic client, or None if not configured."""
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key or api_key == "sk-ant-placeholder":
            return None
        try:
            import anthropic

            return anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            return None

    def get_sagemaker_config(self) -> dict:
        """Return SageMaker endpoint configuration dict."""
        return {
            "endpoint_url": settings.SAGEMAKER_ENDPOINT_URL,
            "region": settings.AWS_REGION,
        }

    def get_vllm_config(self) -> dict:
        """Return vLLM endpoint configuration dict."""
        return {
            "endpoint_url": settings.VLLM_ENDPOINT_URL,
        }

    def _provider_available(self, provider: LLMProvider) -> bool:
        if provider == LLMProvider.OPENROUTER:
            return bool(settings.OPENROUTER_API_KEY)
        if provider == LLMProvider.ANTHROPIC:
            key = settings.ANTHROPIC_API_KEY
            return bool(key and key != "sk-ant-placeholder")
        if provider == LLMProvider.OLLAMA:
            return bool(settings.OLLAMA_ENDPOINT_URL.strip())
        if provider == LLMProvider.SAGEMAKER:
            return bool(settings.SAGEMAKER_ENDPOINT_URL)
        if provider == LLMProvider.VLLM:
            return bool(settings.VLLM_ENDPOINT_URL)
        return False

    async def route(self, prompt: str, system_prompt: str = "") -> str:
        """Route an LLM request through the tier provider with PII
        stripping and fallback."""
        clean_prompt, redacted_types = self.strip_pii(prompt)
        clean_system, _ = self.strip_pii(system_prompt)

        if redacted_types:
            logger.info("PII stripped from prompt: types=%s", redacted_types)

        last_error: Exception | None = None
        for provider in self._fallback_chain:
            if not self._provider_available(provider):
                continue
            method_name = _CALL_METHODS.get(provider)
            if not method_name:
                continue
            call_fn = getattr(self, method_name)
            try:
                result = await call_fn(clean_prompt, clean_system)
                logger.info(
                    "LLM request routed: tier=%d, provider=%s, pii_redacted=%s",
                    self._tier,
                    provider.value,
                    bool(redacted_types),
                )
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LLM provider %s failed: %s — trying next",
                    provider.value,
                    exc,
                )

        raise LLMUnavailableError(
            f"LLM inference unavailable. Last error: {last_error}"
        )

    async def get_tier_status(self) -> dict:
        """Return health of each provider in the fallback chain."""
        status: dict[str, dict] = {}
        for provider in self._fallback_chain:
            ok = False
            detail = ""
            try:
                if provider == LLMProvider.OPENROUTER:
                    ok = bool(settings.OPENROUTER_API_KEY)
                    detail = "configured" if ok else "missing API key"
                elif provider == LLMProvider.ANTHROPIC:
                    ok = self.get_anthropic_client() is not None
                    detail = "configured" if ok else "missing API key"
                elif provider == LLMProvider.OLLAMA:
                    url = settings.OLLAMA_ENDPOINT_URL.rstrip("/")
                    if not url:
                        ok = False
                        detail = "not configured"
                    else:
                        async with httpx.AsyncClient(timeout=3.0) as cli:
                            resp = await cli.get(f"{url}/api/tags")
                            ok = resp.is_success
                        detail = "reachable" if ok else "unreachable"
                elif provider == LLMProvider.SAGEMAKER:
                    ok = bool(settings.SAGEMAKER_ENDPOINT_URL)
                    detail = "configured" if ok else "not configured"
                elif provider == LLMProvider.VLLM:
                    ok = bool(settings.VLLM_ENDPOINT_URL)
                    detail = "configured" if ok else "not configured"
            except Exception as exc:
                detail = str(exc)[:120]
            status[provider.value] = {"available": ok, "detail": detail}
        active = next((p.value for p in self._fallback_chain if status.get(p.value, {}).get("available")), None)
        return {
            "tier": self._tier,
            "active_provider": active,
            "providers": status,
            "routing_enabled": settings.LLM_ROUTING_ENABLED,
        }

    async def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """Call local Ollama (Tier 2 fallback)."""
        base = settings.OLLAMA_ENDPOINT_URL.rstrip("/")
        if not base:
            raise RuntimeError("Ollama endpoint URL not configured")

        model = settings.OLLAMA_MODEL
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as cli:
            resp = await cli.post(
                f"{base}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return (data.get("message") or {}).get("content", "").strip()

    async def _call_openrouter(self, prompt: str, system_prompt: str) -> str:
        """Call OpenRouter (OpenAI-compatible) chat completions API."""
        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            raise RuntimeError("OpenRouter API key not configured")

        base = settings.OPENROUTER_BASE_URL.rstrip("/")
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as cli:
            resp = await cli.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8082",
                    "X-Title": "IPE Copilot",
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
                    "messages": messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("OpenRouter returned no choices")
            content = (choices[0].get("message") or {}).get("content", "")
            return str(content).strip()

    async def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        """Call Anthropic Claude API (Tier 1)."""
        client = self.get_anthropic_client()
        if client is None:
            raise RuntimeError("Anthropic API key not configured")

        kwargs: dict = {
            "model": settings.MODEL_CONFIG.get("model", "claude-sonnet-4-20250514"),
            "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        message = await client.messages.create(**kwargs)
        return message.content[0].text.strip() if message.content else ""

    async def _call_sagemaker(self, prompt: str, system_prompt: str) -> str:
        """Call SageMaker inference endpoint (Tier 2)."""
        config = self.get_sagemaker_config()
        if not config["endpoint_url"]:
            raise RuntimeError("SageMaker endpoint URL not configured")

        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
        }
        async with httpx.AsyncClient(timeout=60) as cli:
            resp = await cli.post(config["endpoint_url"], json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("text", data.get("response", str(data)))

    async def _call_vllm(self, prompt: str, system_prompt: str) -> str:
        """Call local vLLM inference endpoint (Tier 3)."""
        config = self.get_vllm_config()
        if not config["endpoint_url"]:
            raise RuntimeError("vLLM endpoint URL not configured")

        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "max_tokens": settings.MODEL_CONFIG.get("max_tokens", 1024),
        }
        async with httpx.AsyncClient(timeout=60) as cli:
            resp = await cli.post(config["endpoint_url"], json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("text", data.get("response", str(data)))
