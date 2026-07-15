"""Unit tests — RootCauseAnalyzer (no DB)."""

import pytest

from app.core.root_cause_analyzer import RootCauseAnalyzer


@pytest.mark.asyncio
async def test_analyze_capacity_chain_reaches_supplier_root():
    analyzer = RootCauseAnalyzer()
    chain = await analyzer.analyze(
        None,
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
        gate_scores={"capacity": 40, "material": 70, "delivery": 80, "bom": 100, "demand": 95},
    )
    data = chain.to_dict()
    assert data["chain_depth"] >= 2
    assert chain.root_cause is not None
    assert chain.root_cause.cause_type == "systemic_supplier_issue"
    assert len(data["recommendations"]) >= 1
    assert data["recommendations"][0]["timeframe"] == "immediate"


@pytest.mark.asyncio
async def test_analyze_material_shortage_root():
    analyzer = RootCauseAnalyzer()
    chain = await analyzer.analyze(
        None,
        "11111111-1111-1111-1111-111111111111",
        "mo-xyz",
        gate_scores={"capacity": 90, "material": 30, "delivery": 80, "bom": 100, "demand": 95},
    )
    assert chain.levels[0].cause_type == "material_shortage"
    assert chain.root_cause is not None
    assert chain.root_cause.is_root_cause or chain.root_cause.cause_type == "systemic_supplier_issue"
