"""Role-based copilot agent registry (v8 Phase 1)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CopilotAgent:
    role: str
    label: str
    description: str
    intents: tuple[str, ...]
    follow_up_suggestions: tuple[str, ...]


AGENT_REGISTRY: dict[str, CopilotAgent] = {
    "planner": CopilotAgent(
        role="planner",
        label="Production Planner",
        description="Schedule, feasibility, resolution, and demand forecasts",
        intents=("feasibility_check", "material_status", "schedule_status", "demand_forecast"),
        follow_up_suggestions=(
            "Which MOs are at risk this week?",
            "Show demand forecast for top SKUs",
            "Open scenario workbench for +10% demand",
        ),
    ),
    "manager": CopilotAgent(
        role="manager",
        label="Plant Manager",
        description="KPIs, exceptions, war room, and scenario comparison",
        intents=("feasibility_check", "delay_analysis", "war_room_summary", "scenario_compare"),
        follow_up_suggestions=(
            "Summarize active war room alerts",
            "Compare baseline vs high-demand scenario",
            "What is average feasibility today?",
        ),
    ),
    "supervisor": CopilotAgent(
        role="supervisor",
        label="Shop Floor Supervisor",
        description="Work orders, equipment status, and shift priorities",
        intents=("shop_floor_status", "capacity_status", "maintenance_alert"),
        follow_up_suggestions=(
            "List active work orders on Assembly Line 1",
            "Any machines above 90% utilization?",
        ),
    ),
    "executive": CopilotAgent(
        role="executive",
        label="Executive",
        description="OTD, cost of chaos, and executive KPI rollups",
        intents=("otd_summary", "cost_of_chaos", "executive_dashboard"),
        follow_up_suggestions=(
            "What is on-time delivery trend?",
            "Top cost-of-chaos drivers this month",
        ),
    ),
}


def resolve_agent(role: str | None) -> CopilotAgent:
    key = (role or "planner").lower()
    return AGENT_REGISTRY.get(key, AGENT_REGISTRY["planner"])


def list_agents_for_role(user_role: str) -> list[dict]:
    """Users see their primary agent plus planner fallback."""
    primary = resolve_agent(user_role)
    agents = [primary]
    if user_role.lower() != "planner" and "planner" in AGENT_REGISTRY:
        agents.append(AGENT_REGISTRY["planner"])
    seen = set()
    out = []
    for agent in agents:
        if agent.role in seen:
            continue
        seen.add(agent.role)
        out.append(
            {
                "role": agent.role,
                "label": agent.label,
                "description": agent.description,
                "intents": list(agent.intents),
                "follow_up_suggestions": list(agent.follow_up_suggestions),
            }
        )
    return out
