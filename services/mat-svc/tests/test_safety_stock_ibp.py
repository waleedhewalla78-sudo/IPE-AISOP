from app.core.safety_stock import calculate_safety_stock_ibp


def test_ibp_safety_stock_known_series():
    result = calculate_safety_stock_ibp(
        demand_series=[100, 110, 90, 105, 95, 100],
        lead_time_days_series=[14, 16, 12, 15, 13],
        service_level_pct=95,
        period_days=7,
    )

    assert abs(result["components"]["demand_component"] - 16.43) < 0.5
    assert abs(result["components"]["lead_time_component"] - 36.96) < 0.75
    assert abs(result["safety_stock_qty"] - 53.39) < 1.0
    assert abs(result["reorder_point"] - 253.39) < 1.0
    assert result["inputs"]["avg_demand_per_period"] == 100
    assert result["inputs"]["avg_lead_time_periods"] == 2
