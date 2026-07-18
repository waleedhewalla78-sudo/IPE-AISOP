"""Phase 8 Wave 1 — agent stubs A18 (multi-site), A19 (learning), A20 (ops)."""

from __future__ import annotations

from typing import Any

from ipe_shared.roles import AgentRoleContext


def a18_multi_site_split(
    demand_qty: float,
    plant_capacities: dict[str, float],
    *,
    user_role: str = "manager",
) -> dict[str, Any]:
    """Scaffold: propose split across plants. Full orchestration → Wave 8B."""
    ctx = AgentRoleContext.get_context(user_role, "A18")
    total_cap = sum(plant_capacities.values()) or 1.0
    allocation = {
        plant: round(demand_qty * (cap / total_cap), 2) for plant, cap in plant_capacities.items()
    }
    return {
        "agent_id": "A18",
        "name": "Multi-Site Network Agent",
        "status": "scaffold",
        "wave": "8A stub — full multi-site coordination deferred to 8B",
        "allocation": allocation,
        "role_context": {"role": ctx["role"], "data_scope": ctx["data_scope"]},
        "autonomous": "all" in ctx.get("autonomous_actions", []),
    }


def a19_learning_retrain_stub(
    model_name: str = "feasibility_scorer",
    *,
    user_role: str = "manager",
) -> dict[str, Any]:
    """Scaffold: learning / retraining trigger. No real training in Wave 1."""
    ctx = AgentRoleContext.get_context(user_role, "A19")
    can_modify = bool(ctx.get("can_modify_autonomous_rules"))
    return {
        "agent_id": "A19",
        "name": "Self-Learning Agent",
        "status": "scaffold",
        "wave": "8A stub — autonomous retraining deferred to 8B",
        "model_name": model_name,
        "retrain_queued": False,
        "can_modify_rules": can_modify,
        "message": "No scikit-learn/XGBoost job started — Wave 8B",
    }


def a20_exception_monitor_stub(
    open_exceptions: int = 0,
    *,
    user_role: str = "supervisor",
) -> dict[str, Any]:
    """Scaffold placeholder for remaining Phase 8 agent surface (monitor/escalate)."""
    ctx = AgentRoleContext.get_context(user_role, "A20")
    return {
        "agent_id": "A20",
        "name": "Exception Monitor Agent",
        "status": "scaffold",
        "wave": "8A stub — deferred to 8B/8C",
        "open_exceptions": open_exceptions,
        "escalation_target": ctx["escalation_target"],
        "message": "Monitor-only stub; humans handle escalations per Phase 8 §7",
    }


PHASE8_AGENT_CATALOG = [
    {"agent_id": "A18", "name": "Multi-Site Network", "status": "scaffold", "wave": "8B"},
    {"agent_id": "A19", "name": "Self-Learning", "status": "scaffold", "wave": "8B"},
    {"agent_id": "A20", "name": "Exception Monitor", "status": "scaffold", "wave": "8B"},
]
