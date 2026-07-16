"""Phase 7 §1 — Multi-Horizon Planning core tests."""

from app.core.phase7 import build_horizons, cascade_plan


def test_horizons_three_cards_and_health():
    data = build_horizons()
    assert set(data["horizons"].keys()) == {"strategic", "tactical", "operational"}
    for card in data["horizons"].values():
        assert 0 <= card["coverage_pct"] <= 100
        assert card["status"] in ("healthy", "attention", "critical")
        assert "█" in card["health_bar"] or "░" in card["health_bar"]
    assert 0 <= data["overall_coverage_pct"] <= 100


def test_horizons_attention_flags_low_coverage():
    data = build_horizons(
        strategic={"coverage_pct": 60.0, "pending_decisions": 3},
        tactical={"coverage_pct": 95.0, "pending_decisions": 0},
        operational={"coverage_pct": 92.0, "pending_decisions": 0},
    )
    codes = {a["horizon"] for a in data["attention"]}
    assert "strategic" in codes
    assert data["horizons"]["strategic"]["status"] == "critical"


def test_cascade_down_produces_tactical_and_operational():
    data = cascade_plan(direction="down", growth_pct=20, product="DT250")
    assert data["direction"] == "down"
    assert any("DT250" in x["action"] for x in data["cascades_to_tactical"])
    assert len(data["cascades_to_operational"]) >= 3


def test_cascade_up_escalates_to_board():
    data = cascade_plan(direction="up", capex_usd=180_000, growth_pct=20)
    assert data["direction"] == "up"
    assert data["board_decision_required"] is True
    assert data["escalates_to_strategic"][0]["governance_level"] == 4
    assert any(x["agent"] == "A6" for x in data["escalates_to_tactical"])
