from app.core.role_agents import list_agents_for_role, resolve_agent


def test_resolve_planner_agent():
    agent = resolve_agent("planner")
    assert agent.role == "planner"
    assert "feasibility_check" in agent.intents


def test_list_agents_includes_primary():
    agents = list_agents_for_role("executive")
    roles = {a["role"] for a in agents}
    assert "executive" in roles
