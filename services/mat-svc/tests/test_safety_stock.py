import math

from app.core.safety_stock import (
    _z_score,
    calculate_all_products_safety_stock,
    calculate_safety_stock,
    calculate_safety_stock_from_history,
)


class TestZScore:
    def test_95_service_level(self):
        z = _z_score(0.95)
        assert abs(z - 1.65) < 0.01

    def test_90_service_level(self):
        z = _z_score(0.90)
        assert abs(z - 1.28) < 0.01

    def test_99_service_level(self):
        z = _z_score(0.99)
        assert abs(z - 2.33) < 0.01

    def test_interpolated_value(self):
        z_93 = _z_score(0.93)
        assert 1.4 < z_93 < 1.6

    def test_zero_service_level(self):
        z = _z_score(0.0)
        assert z == 0.0

    def test_full_service_level(self):
        z = _z_score(1.0)
        assert z >= 3.0

    def test_below_zero(self):
        z = _z_score(-0.5)
        assert z == 0.0


class TestCalculateSafetyStock:
    def test_basic_calculation(self):
        result = calculate_safety_stock(
            avg_daily_demand=100,
            demand_std_dev=20,
            avg_lead_time_days=7,
            lead_time_std_dev=2,
            service_level=0.95,
        )
        assert result["safety_stock_qty"] > 0
        assert result["z_score"] > 0
        assert result["reorder_point"] > 0
        assert result["service_level"] == 0.95

    def test_zero_demand(self):
        result = calculate_safety_stock(
            avg_daily_demand=0,
            demand_std_dev=0,
            avg_lead_time_days=7,
            lead_time_std_dev=2,
        )
        assert result["safety_stock_qty"] == 0
        assert result["reorder_point"] == 0

    def test_zero_lead_time_std(self):
        result = calculate_safety_stock(
            avg_daily_demand=100,
            demand_std_dev=20,
            avg_lead_time_days=7,
            lead_time_std_dev=0,
        )
        assert result["safety_stock_qty"] > 0
        assert result["components"]["lead_time_variance"] == 0

    def test_higher_service_level_means_more_stock(self):
        low = calculate_safety_stock(100, 20, 7, 2, service_level=0.90)
        high = calculate_safety_stock(100, 20, 7, 2, service_level=0.99)
        assert high["safety_stock_qty"] > low["safety_stock_qty"]

    def test_reorder_point_formula(self):
        result = calculate_safety_stock(100, 20, 7, 2, 0.95)
        expected_rop = 100 * 7 + result["safety_stock_qty"]
        assert abs(result["reorder_point"] - expected_rop) < 0.01

    def test_components_present(self):
        result = calculate_safety_stock(100, 20, 7, 2)
        assert "demand_variance" in result["components"]
        assert "lead_time_variance" in result["components"]
        assert "combined_variance" in result["components"]

    def test_inputs_reflected(self):
        result = calculate_safety_stock(50, 10, 5, 1)
        assert result["inputs"]["avg_daily_demand"] == 50
        assert result["inputs"]["demand_std_dev"] == 10


class TestCalculateSafetyStockFromHistory:
    def test_from_demand_history(self):
        history = [90, 100, 110, 95, 105, 98, 102]
        result = calculate_safety_stock_from_history(
            demand_history=history,
            lead_time_days=7,
            lead_time_std_dev=2,
            service_level=0.95,
        )
        assert result["safety_stock_qty"] > 0

    def test_empty_history(self):
        result = calculate_safety_stock_from_history([], 7, 2)
        assert result["safety_stock_qty"] == 0
        assert "error" in result

    def test_single_value_history(self):
        result = calculate_safety_stock_from_history([100], 7, 2)
        assert result["safety_stock_qty"] > 0
        assert "error" not in result

    def test_high_variability_more_stock(self):
        stable = calculate_safety_stock_from_history([100] * 10, 7, 2)
        variable = calculate_safety_stock_from_history([80, 120, 70, 130, 90, 110, 85, 115, 95, 105], 7, 2)
        assert variable["safety_stock_qty"] > stable["safety_stock_qty"]


class TestBulkSafetyStock:
    def test_multiple_products(self):
        products = [
            {
                "product_id": "P001",
                "avg_daily_demand": 100,
                "demand_std_dev": 20,
                "avg_lead_time_days": 7,
                "lead_time_std_dev": 2,
            },
            {
                "product_id": "P002",
                "avg_daily_demand": 50,
                "demand_std_dev": 10,
                "avg_lead_time_days": 14,
                "lead_time_std_dev": 3,
            },
        ]
        results = calculate_all_products_safety_stock(products, service_level=0.95)
        assert len(results) == 2
        assert results[0]["product_id"] == "P001"
        assert results[1]["product_id"] == "P002"
        assert results[0]["safety_stock_qty"] > 0
        assert results[1]["safety_stock_qty"] > 0

    def test_empty_products(self):
        results = calculate_all_products_safety_stock([])
        assert len(results) == 0
