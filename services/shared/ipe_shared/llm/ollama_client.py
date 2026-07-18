"""Shared Ollama client — Phase 8 Wave 1 scaffold with rule-based degrade.

Does NOT claim fine-tuned ipe-planner/ipe-analyst weights are loaded.
Ops may load Modelfile stubs from ops/ollama/; runtime falls back gracefully.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
AI_UNAVAILABLE_BANNER = (
    "AI explanations temporarily unavailable. Core planning functions continue."
)
AI_UNAVAILABLE_BANNER_AR = (
    "تفسيرات الذكاء الاصطناعي غير متاحة مؤقتاً. تستمر وظائف التخطيط الأساسية."
)

# Preferred model names (ops may load these via Modelfile stubs)
PREFERRED_MODELS = ("ipe-planner:latest", "ipe-analyst:latest", "llama3.1:latest", "llama3.1")


@dataclass
class OllamaHealth:
    available: bool
    url: str
    models: list[str] = field(default_factory=list)
    preferred_loaded: bool = False
    message: str = ""
    degrade_mode: bool = False

    def to_api_flag(self) -> dict[str, Any]:
        return {
            "ollama_available": self.available,
            "degrade_mode": self.degrade_mode or not self.available,
            "show_amber_banner": not self.available,
            "banner_message_en": AI_UNAVAILABLE_BANNER if not self.available else "",
            "banner_message_ar": AI_UNAVAILABLE_BANNER_AR if not self.available else "",
            "url": self.url,
            "models": self.models,
            "preferred_models_loaded": self.preferred_loaded,
            "note": (
                "Fine-tuned ipe-planner/ipe-analyst weights are ops-loaded stubs only; "
                "not claimed present unless listed in models."
            ),
        }


@dataclass
class NarrativeResult:
    text: str
    source: str  # "ollama" | "rule_based"
    model: str | None = None
    degraded: bool = False


def get_ollama_url() -> str:
    return (
        os.environ.get("IPE_OLLAMA_URL")
        or os.environ.get("OLLAMA_URL")
        or DEFAULT_OLLAMA_URL
    ).rstrip("/")


class OllamaClient:
    """HTTP client for Ollama with automatic rule-based degrade."""

    def __init__(self, base_url: str | None = None, timeout_s: float = 3.0) -> None:
        self.base_url = (base_url or get_ollama_url()).rstrip("/")
        self.timeout_s = timeout_s
        self._last_health: OllamaHealth | None = None

    def check_health(self) -> OllamaHealth:
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in payload.get("models", []) if m.get("name")]
            preferred = any(
                any(m.startswith(p.split(":")[0]) for p in PREFERRED_MODELS) for m in models
            )
            health = OllamaHealth(
                available=True,
                url=self.base_url,
                models=models,
                preferred_loaded=preferred,
                message="ok",
                degrade_mode=False,
            )
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
            logger.info("Ollama unreachable at %s: %s — degrading to rule-based", self.base_url, exc)
            health = OllamaHealth(
                available=False,
                url=self.base_url,
                models=[],
                preferred_loaded=False,
                message=str(exc),
                degrade_mode=True,
            )
        self._last_health = health
        return health

    def last_health(self) -> OllamaHealth:
        if self._last_health is None:
            return self.check_health()
        return self._last_health

    def _pick_model(self, models: list[str], preferred: str | None = None) -> str | None:
        if preferred and preferred in models:
            return preferred
        for pref in PREFERRED_MODELS:
            for m in models:
                if m == pref or m.startswith(pref.split(":")[0]):
                    return m
        return models[0] if models else None

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        model: str | None = None,
        locale: str = "en",
    ) -> NarrativeResult:
        health = self.check_health()
        if not health.available:
            return NarrativeResult(
                text=self.rule_based_explanation(prompt, locale=locale),
                source="rule_based",
                degraded=True,
            )
        chosen = self._pick_model(health.models, model)
        if not chosen:
            return NarrativeResult(
                text=self.rule_based_explanation(prompt, locale=locale),
                source="rule_based",
                degraded=True,
            )
        body = {
            "model": chosen,
            "prompt": prompt,
            "stream": False,
            "system": system
            or (
                "أنت وكيل تخطيط ذكي. اكتب تفسيرات موجزة ومهنية بالعربية."
                if locale == "ar"
                else "You are a planning intelligence agent. Write concise professional explanations."
            ),
        }
        try:
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=max(self.timeout_s, 8.0)) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            text = (payload.get("response") or "").strip()
            if not text:
                return NarrativeResult(
                    text=self.rule_based_explanation(prompt, locale=locale),
                    source="rule_based",
                    model=chosen,
                    degraded=True,
                )
            return NarrativeResult(text=text, source="ollama", model=chosen, degraded=False)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
            logger.info("Ollama generate failed: %s — rule-based degrade", exc)
            return NarrativeResult(
                text=self.rule_based_explanation(prompt, locale=locale),
                source="rule_based",
                model=chosen,
                degraded=True,
            )

    @staticmethod
    def rule_based_explanation(prompt: str, locale: str = "en") -> str:
        """Template / bullet fallback when Ollama is down — core logic continues."""
        snippet = (prompt or "").strip().replace("\n", " ")[:180]
        if locale == "ar":
            return (
                "وضع القواعد: التفسير التفصيلي غير متاح حالياً. "
                f"الملخص: {snippet or 'تم اكتشاف حالة تخطيط تتطلب مراجعة.'}"
            )
        return (
            "Rule-based mode: detailed AI narrative unavailable. "
            f"Summary: {snippet or 'Planning situation requires review.'}"
        )


_default_client: OllamaClient | None = None


def get_ollama_client() -> OllamaClient:
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client


def generate_agent_explanation(
    agent_id: str,
    data: dict[str, Any],
    *,
    locale: str = "en",
    client: OllamaClient | None = None,
) -> NarrativeResult:
    """Route narrative tasks (A4/A5/A7 explanations) through Ollama when available.

    A7 Copilot complex NL remains Claude-first in nlp-svc; this helper is for
    structured planning narratives (feasibility / resolution / quality / etc.).
    """
    ollama = client or get_ollama_client()
    prompt = f"Agent {agent_id} explain: {json.dumps(data, default=str)}"
    preferred = "ipe-analyst:latest" if agent_id in {"A1", "A13", "A14"} else "ipe-planner:latest"
    return ollama.generate(prompt, model=preferred, locale=locale)
