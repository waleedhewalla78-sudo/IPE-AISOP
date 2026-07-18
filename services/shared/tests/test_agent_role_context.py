"""Phase 8 — AgentRoleContext unit tests ($1K / $10K / $50K)."""

from ipe_shared.roles import AgentRoleContext


def test_employee_cannot_approve_resolution():
    assert AgentRoleContext.can_execute("employee", "approve_resolution", 100) is False
    assert AgentRoleContext.can_execute("employee", "approve_resolution", 0) is False


def test_employee_threshold_1k():
    assert AgentRoleContext.can_execute("employee", "view", 999) is True
    assert AgentRoleContext.can_execute("employee", "view", 1001) is False


def test_supervisor_threshold_10k():
    assert AgentRoleContext.can_execute("supervisor", "approve_resolution", 9999) is True
    assert AgentRoleContext.can_execute("supervisor", "approve_resolution", 10001) is False
    assert AgentRoleContext.can_execute("supervisor", "override_ai", 100) is False


def test_manager_threshold_50k():
    assert AgentRoleContext.can_execute("manager", "approve_resolution", 49999) is True
    assert AgentRoleContext.can_execute("manager", "approve_resolution", 50001) is False
    assert AgentRoleContext.can_execute("manager", "override_ai", 1000) is True


def test_role_aliases_planner_is_supervisor():
    ctx = AgentRoleContext.get_context("planner", "A5")
    assert ctx["role"] == "supervisor"
    assert ctx["max_financial_impact"] == 10000


def test_a11_financial_visibility_non_manager():
    ctx = AgentRoleContext.get_context("supervisor", "A11")
    assert ctx["financial_visibility"] == ["cost_impact"]
    filtered = AgentRoleContext.filter_financials(
        "supervisor",
        {"cost_impact": 100, "margin": 28.0, "pnl": 1000},
        agent_id="A11",
    )
    assert "cost_impact" in filtered
    assert "margin" not in filtered
    assert "pnl" not in filtered


def test_manager_sees_margin():
    filtered = AgentRoleContext.filter_financials(
        "manager",
        {"cost_impact": 100, "margin": 28.0, "cash_flow": 50},
        agent_id="A11",
    )
    assert filtered["margin"] == 28.0
    assert filtered["cash_flow"] == 50
