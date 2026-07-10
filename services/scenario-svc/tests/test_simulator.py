from app.core.simulator import DEFAULT_BASELINE, compare_scenarios, simulate_kpis


def test_simulate_demand_increase_raises_risk():
    kpis = simulate_kpis({"demand_change_pct": "20%"})
    assert kpis["orders_at_risk"] >= DEFAULT_BASELINE["orders_at_risk"]


def test_compare_scenarios_scores():
    results = [simulate_kpis({"demand_change_pct": "0%"}), simulate_kpis({"demand_change_pct": "10%"})]
    baseline = results[0]
    comparison = compare_scenarios(results, baseline)
    assert len(comparison) == 2
    assert "fitness_score" in comparison[0]
