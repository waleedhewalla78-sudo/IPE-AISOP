import pytest

from app.core.agent_orchestrator import AgentOrchestrator
from app.core.exception_lifecycle import ExceptionLifecycle, FinancialDecisionFramework


@pytest.mark.asyncio
async def test_orchestrator_dry_run_chain():
    orch = AgentOrchestrator(dry_run=True)
    result = await orch.run_chain(
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "upload",
        ["demand", "inventory", "production", "supply", "master"],
    )
    assert result["agents_run"] >= 1
    assert "details" in result
    assert result["details"]["A4"]["status"] == "completed"


@pytest.mark.asyncio
async def test_exception_lifecycle():
    life = ExceptionLifecycle()
    exc = await life.create(
        None,
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "A2",
        "STOCKOUT",
        "high",
        "Copper wire risk",
    )
    assert exc["status"] == "open"
    ack = life.acknowledge(exc, "planner")
    assert ack["status"] == "acknowledged"
    resolved = life.resolve(ack, {"name": "Expedite"}, "planner")
    assert resolved["status"] == "resolved"


def test_financial_decision_framework():
    fw = FinancialDecisionFramework()
    result = fw.evaluate_options(
        [
            {"name": "A", "direct_cost": 0, "penalty_risk": 6000, "revenue_impact": 0},
            {"name": "B", "direct_cost": 1800, "penalty_risk": 0, "revenue_impact": 0},
            {"name": "C", "direct_cost": 400, "penalty_risk": 0, "revenue_impact": 0},
        ]
    )
    assert result["recommendation"]["name"] == "C"
