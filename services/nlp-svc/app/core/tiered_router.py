"""Tiered LLM routing based on tenant data privacy requirements.

Tier precedence: ON_PREM (highest) > PRIVATE_VPC > SAAS (lowest).

ON_PREM tenants route to a local vLLM endpoint — no data leaves the network.
PRIVATE_VPC tenants route to an AWS SageMaker endpoint within their VPC.
SAAS tenants route to Anthropic Claude via the public API.

If a tier's provider is unavailable, the router falls back to the next
lower tier.  PII is always stripped before prompts leave the service,
regardless of tier.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import StrEnum

import httpx

from app.config import settings
from app.core.llm_errors import LLMUnavailableError
from ipe_shared.security.pii import strip_pii_from_prompt

logger = logging.getLogger(__name__)


class LLMTier(StrEnum):
    SAAS = "saas"
    PRIVATE_VPC = "private_vpc"
    ON_PREM = "on_prem"


_TIER_FALLBACK: dict[LLMTier, list[LLMTier]] = {
    LLMTier.ON_PREM: [LLMTier.ON_PREM, LLMTier.PRIVATE_VPC, LLMTier.SAAS],
    LLMTier.PRIVATE_VPC: [LLMTier.PRIVATE_VPC, LLMTier.SAAS],
    LLMTier.SAAS: [LLMTier.SAAS],
}


@dataclass
class TenantTierConfig:
    tier: LLMTier
    model_name: str
    max_tokens: int
    api_key_env: str = ""
    endpoint_url: str = ""


DEFAULT_TIER_CONFIGS: dict[LLMTier, TenantTierConfig] = {
    LLMTier.SAAS: TenantTierConfig(
        tier=LLMTier.SAAS,
        model_name="claude-sonnet-4-20250514",
        max_tokens=1024,
        api_key_env="ANTHROPIC_API_KEY",
    ),
    LLMTier.PRIVATE_VPC: TenantTierConfig(
        tier=LLMTier.PRIVATE_VPC,
        model_name="sagemaker-claude",
        max_tokens=2048,
        api_key_env="AWS_ACCESS_KEY_ID",
        endpoint_url="",
    ),
    LLMTier.ON_PREM: TenantTierConfig(
        tier=LLMTier.ON_PREM,
        model_name="llama3-70b",
        max_tokens=2048,
        api_key_env="",
        endpoint_url="",
    ),
}


@dataclass
class LLMConfig:
    provider: str
    model_name: str
    max_tokens: int
    api_key: str = ""
    endpoint_url: str = ""


class TieredRouter:
    """Routes LLM requests to the provider matching the tenant's data tier."""

    def __init__(
        self,
        tenant_tiers: dict[str, LLMTier] | None = None,
        tier_configs: dict[LLMTier, TenantTierConfig] | None = None,
    ) -> None:
        self._tenant_tiers: dict[str, LLMTier] = tenant_tiers or {}
        self._tier_configs = tier_configs or DEFAULT_TIER_CONFIGS

    def register_tenant(self, tenant_id: str, tier: LLMTier) -> None:
        self._tenant_tiers[tenant_id] = tier

    def get_tier(self, tenant_id: str) -> LLMTier:
        return self._tenant_tiers.get(tenant_id, LLMTier.SAAS)

    def route(self, tenant_id: str) -> LLMConfig:
        """Determine tenant LLM tier and return config, with fallback."""
        tier = self.get_tier(tenant_id)
        fallback_chain = _TIER_FALLBACK.get(tier, [LLMTier.SAAS])

        for fallback_tier in fallback_chain:
            config = self._tier_configs.get(fallback_tier)
            if config is None:
                continue

            if fallback_tier == LLMTier.ON_PREM:
                url = config.endpoint_url
                if not url:
                    url = os.environ.get(
                        "VLLM_ENDPOINT_URL",
                        settings.VLLM_ENDPOINT_URL,
                    )
                if url:
                    return LLMConfig(
                        provider="vllm",
                        model_name=config.model_name,
                        max_tokens=config.max_tokens,
                        endpoint_url=url,
                    )
                continue

            if fallback_tier == LLMTier.PRIVATE_VPC:
                url = config.endpoint_url
                if not url:
                    url = os.environ.get(
                        "SAGEMAKER_ENDPOINT_URL",
                        settings.SAGEMAKER_ENDPOINT_URL,
                    )
                if url:
                    return LLMConfig(
                        provider="sagemaker",
                        model_name=config.model_name,
                        max_tokens=config.max_tokens,
                        endpoint_url=url,
                    )
                continue

            if fallback_tier == LLMTier.SAAS:
                api_key = os.environ.get(config.api_key_env, settings.ANTHROPIC_API_KEY)
                if api_key and api_key != "sk-ant-placeholder":
                    return LLMConfig(
                        provider="anthropic",
                        model_name=config.model_name,
                        max_tokens=config.max_tokens,
                        api_key=api_key,
                    )
                return LLMConfig(
                    provider="anthropic",
                    model_name=config.model_name,
                    max_tokens=config.max_tokens,
                    api_key="",
                )

        return LLMConfig(
            provider="anthropic",
            model_name="claude-sonnet-4-20250514",
            max_tokens=1024,
            api_key="",
        )

    async def call(self, tenant_id: str, prompt: str, system_prompt: str = "") -> str:
        """Route and call the appropriate LLM for the tenant, stripping PII first."""
        clean_prompt, redacted_types = strip_pii_from_prompt(prompt)
        clean_system, _ = strip_pii_from_prompt(system_prompt)

        if redacted_types:
            logger.info("PII stripped for tenant %s: types=%s", tenant_id, redacted_types)

        tier = self.get_tier(tenant_id)
        fallback_chain = _TIER_FALLBACK.get(tier, [LLMTier.SAAS])
        last_error: Exception | None = None

        for fallback_tier in fallback_chain:
            config = self._config_for_tier(fallback_tier)
            if config is None:
                continue
            try:
                if config.provider == "anthropic":
                    return await self._call_anthropic(config, clean_prompt, clean_system)
                if config.provider == "sagemaker":
                    return await self._call_sagemaker(config, clean_prompt, clean_system)
                if config.provider == "vllm":
                    return await self._call_vllm(config, clean_prompt, clean_system)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LLM tier %s provider %s failed: %s — trying next",
                    fallback_tier.value,
                    config.provider,
                    exc,
                )

        try:
            return await self._call_ollama(clean_prompt, clean_system)
        except Exception as exc:
            last_error = exc
            logger.warning("Ollama fallback failed: %s", exc)

        raise LLMUnavailableError(
            f"LLM inference unavailable. Last error: {last_error}"
        )

    def _config_for_tier(self, fallback_tier: LLMTier) -> LLMConfig | None:
        config = self._tier_configs.get(fallback_tier)
        if config is None:
            return None

        if fallback_tier == LLMTier.ON_PREM:
            url = config.endpoint_url or os.environ.get(
                "VLLM_ENDPOINT_URL",
                settings.VLLM_ENDPOINT_URL,
            )
            if url:
                return LLMConfig(
                    provider="vllm",
                    model_name=config.model_name,
                    max_tokens=config.max_tokens,
                    endpoint_url=url,
                )
            return None

        if fallback_tier == LLMTier.PRIVATE_VPC:
            url = config.endpoint_url or os.environ.get(
                "SAGEMAKER_ENDPOINT_URL",
                settings.SAGEMAKER_ENDPOINT_URL,
            )
            if url:
                return LLMConfig(
                    provider="sagemaker",
                    model_name=config.model_name,
                    max_tokens=config.max_tokens,
                    endpoint_url=url,
                )
            return None

        if fallback_tier == LLMTier.SAAS:
            api_key = os.environ.get(config.api_key_env, settings.ANTHROPIC_API_KEY)
            if api_key and api_key != "sk-ant-placeholder":
                return LLMConfig(
                    provider="anthropic",
                    model_name=config.model_name,
                    max_tokens=config.max_tokens,
                    api_key=api_key,
                )
        return None

    async def get_tier_status(self, tenant_id: str) -> dict:
        """Return provider availability for the tenant's fallback chain."""
        tier = self.get_tier(tenant_id)
        fallback_chain = _TIER_FALLBACK.get(tier, [LLMTier.SAAS])
        providers: dict[str, dict] = {}
        active: str | None = None

        for fallback_tier in fallback_chain:
            config = self._config_for_tier(fallback_tier)
            if config is None:
                providers[fallback_tier.value] = {"available": False, "detail": "not configured"}
                continue
            ok = bool(config.api_key or config.endpoint_url)
            providers[fallback_tier.value] = {
                "available": ok,
                "detail": config.provider,
                "provider": config.provider,
            }
            if ok and active is None:
                active = config.provider

        ollama_ok = False
        ollama_detail = "unreachable"
        try:
            base = settings.OLLAMA_ENDPOINT_URL.rstrip("/")
            async with httpx.AsyncClient(timeout=3.0) as cli:
                resp = await cli.get(f"{base}/api/tags")
                ollama_ok = resp.is_success
                ollama_detail = "reachable" if ollama_ok else "unreachable"
        except Exception as exc:
            ollama_detail = str(exc)[:120]
        providers["ollama"] = {"available": ollama_ok, "detail": ollama_detail, "provider": "ollama"}
        if not active and ollama_ok:
            active = "ollama"

        return {
            "tenant_tier": tier.value,
            "active_provider": active,
            "providers": providers,
            "routing_enabled": settings.LLM_ROUTING_ENABLED,
        }

    async def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        base = settings.OLLAMA_ENDPOINT_URL.rstrip("/")
        if not base:
            raise RuntimeError("Ollama endpoint URL not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as cli:
            resp = await cli.post(
                f"{base}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return (data.get("message") or {}).get("content", "").strip()

    async def _call_anthropic(self, config: LLMConfig, prompt: str, system_prompt: str) -> str:
        if not config.api_key:
            raise RuntimeError("Anthropic API key not configured")
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=config.api_key)
        except ImportError as exc:
            raise RuntimeError("anthropic package not installed") from exc

        kwargs: dict = {
            "model": config.model_name,
            "max_tokens": config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        message = await client.messages.create(**kwargs)
        return message.content[0].text.strip() if message.content else ""

    async def _call_sagemaker(self, config: LLMConfig, prompt: str, system_prompt: str) -> str:
        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "max_tokens": config.max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as cli:
            resp = await cli.post(config.endpoint_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("text", data.get("response", str(data)))

    async def _call_vllm(self, config: LLMConfig, prompt: str, system_prompt: str) -> str:
        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "max_tokens": config.max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as cli:
            resp = await cli.post(config.endpoint_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("text", data.get("response", str(data)))
