"""Phase 8 narrative helpers — Ollama when available, rule-based degrade otherwise."""

from __future__ import annotations

from typing import Any

from ipe_shared.llm.ollama_client import generate_agent_explanation, get_ollama_client
from ipe_shared.roles import AgentRoleContext


def feasibility_explanation(
    mo_id: str,
    gate_scores: dict[str, float],
    *,
    user_role: str = "supervisor",
    locale: str = "en",
) -> dict[str, Any]:
    """A4 narrative explanation."""
    result = generate_agent_explanation(
        "A4",
        {"mo_id": mo_id, "gate_scores": gate_scores},
        locale=locale,
    )
    health = get_ollama_client().last_health()
    return {
        "agent_id": "A4",
        "mo_id": mo_id,
        "explanation": result.text,
        "source": result.source,
        "degraded": result.degraded,
        "ai_banner": health.to_api_flag() if result.degraded or not health.available else None,
        "role": AgentRoleContext.normalize_role(user_role),
    }


def resolution_narrative(
    mo_id: str,
    scenarios: list[dict[str, Any]],
    *,
    user_role: str = "supervisor",
    locale: str = "en",
) -> dict[str, Any]:
    """A5 resolution scenario narrative with role-filtered financials."""
    filtered = [
        AgentRoleContext.filter_financials(user_role, s, agent_id="A5") for s in scenarios
    ]
    result = generate_agent_explanation(
        "A5",
        {"mo_id": mo_id, "scenarios": filtered},
        locale=locale,
    )
    health = get_ollama_client().last_health()
    return {
        "agent_id": "A5",
        "mo_id": mo_id,
        "scenarios": filtered,
        "narrative": result.text,
        "source": result.source,
        "degraded": result.degraded,
        "show_amber_banner": not health.available,
        "role_context": AgentRoleContext.get_context(user_role, "A5"),
    }
