"""Phase 7 §2 — S&OP Deep core tests (financial / rolling / shaping / portfolio)."""

from app.core.phase7 import (
    build_demand_shaping,
    build_financial_sop,
    optimize_portfolio,
    recalc_rolling_sop,
)


def test_financial_sop_computes_margin_and_flags_floor():
    data = build_financial_sop(margin_floor_pct=20.0)
    assert len(data["periods"]) == 3
    for row in data["periods"]:
        assert row["revenue_usd"] > 0
        assert "gross_profit_usd" in row
        assert "margin_pct" in row
    # October has a constraint + inflation → below floor and an alert raised.
    oct_row = next(r for r in data["periods"] if r["period"] == "Oct")
    assert oct_row["lost_sales_units"] == 2
    assert data["finance_alerts"]
    assert data["finance_alerts"][0]["agent"] == "A11"


def test_financial_sop_all_above_floor_no_alert():
    periods = [
        {
            "period": "Sep",
            "consensus_demand": 25,
            "constrained_supply": 25,
            "material_infl_pct": 0.0,
        },
    ]
    data = build_financial_sop(periods=periods, margin_floor_pct=10.0)
    assert data["finance_alerts"] == []


def test_rolling_sop_event_log_and_governance():
    data = recalc_rolling_sop()
    assert data["mode"] == "rolling"
    assert data["events_processed"] == len(data["event_log"])
    assert len(data["governance_cycle"]) == 4
    # A >$100K order is significant → requires meeting; small forecast tweak auto-applies.
    big = next(e for e in data["event_log"] if e["type"] == "large_order")
    assert big["requires_meeting"] is True
    small = next(e for e in data["event_log"] if e["type"] == "forecast_update")
    assert small["auto_applied"] is True


def test_demand_shaping_three_options_ranked():
    data = build_demand_shaping()
    ids = {o["id"] for o in data["options"]}
    assert ids == {"shift_mix", "pull_forward", "outsource"}
    assert "recommendation" in data


def test_portfolio_ranks_by_margin_per_constraint_hour():
    data = optimize_portfolio()
    ranking = data["ranking"]
    # Ranking is descending by margin per constraint hour.
    vals = [r["margin_per_constraint_hour_usd"] for r in ranking]
    assert vals == sorted(vals, reverse=True)
    assert ranking[0]["rank"] == 1
    assert data["projected_impact"]["margin_uplift_usd"] > 0
