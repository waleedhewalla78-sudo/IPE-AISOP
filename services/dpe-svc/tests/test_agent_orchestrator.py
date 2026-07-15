"""Unit tests — AgentOrchestrator dry-run + ExceptionLifecycle."""

import pytest

from app.core.agent_orchestrator import AgentOrchestrator
from app.core.exception_lifecycle import ExceptionLifecycle, FinancialDecisionFramework


@pytest.mark.asyncio
async def test_orchestrator_dry_run_always_steps():
    orch = AgentOrchestrator(dry_run=True)
    result = await orch.run_chain("11111111-1111-1111-1111-111111111111", "manual", ["demand"])
    assert result["agents_run"] >= 2  # A4 + A4-predict always
    assert "A4" in result["details"]
    assert result["details"]["A4"]["status"] in ("completed", "error", "timeout")


@pytest.mark.asyncio
async def test_orchestrator_skips_demand_steps_without_demand_change():
    orch = AgentOrchestrator(dry_run=True)
    result = await orch.run_chain("t1", "upload", ["production"])
    assert result["details"]["A1"]["status"] == "skipped"
    assert result["details"]["A4"]["status"] == "completed"

def test_exception_ack_does_not_auto_close():
    life = ExceptionLifecycle()
    opened = {"id": "e1", "status": "open"}
    acked = life.acknowledge(opened, user_id="u1")
    assert acked["status"] == "acknowledged"
    assert acked["status"] != "resolved"
    resolved = life.resolve(acked, selected_option={"name": "expedite"}, user_id="u1")
    assert resolved["status"] == "resolved"


def test_financial_framework_ranks_net_impact():
    fw = FinancialDecisionFramework()
    out = fw.evaluate_options(
        [
            {"name": "do_nothing", "direct_cost": 0, "penalty_risk": 10000, "revenue_impact": 0},
            {"name": "expedite", "direct_cost": 800, "penalty_risk": 0, "revenue_impact": 0},
        ]
    )
    assert out["recommendation"]["name"] == "expedite"
