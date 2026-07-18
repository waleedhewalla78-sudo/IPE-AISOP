"""Shared LLM helpers (Ollama scaffold for Phase 8)."""

from ipe_shared.llm.ollama_client import (
    AI_UNAVAILABLE_BANNER,
    AI_UNAVAILABLE_BANNER_AR,
    NarrativeResult,
    OllamaClient,
    OllamaHealth,
    generate_agent_explanation,
    get_ollama_client,
    get_ollama_url,
)

__all__ = [
    "AI_UNAVAILABLE_BANNER",
    "AI_UNAVAILABLE_BANNER_AR",
    "NarrativeResult",
    "OllamaClient",
    "OllamaHealth",
    "generate_agent_explanation",
    "get_ollama_client",
    "get_ollama_url",
]
