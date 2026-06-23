from app.core.po_suggestion import (
    calculate_eoq,
    generate_po_suggestions,
    merge_po_suggestions,
    suggest_order_quantity,
)


class TestEOQ:
    def test_basic_eoq(self):
        eoq = calculate_eoq(annual_demand=1000, order_cost=50, holding_cost_per_unit=5)
        assert eoq > 0
        assert abs(eoq - 141.42) < 1

    def test_zero_holding_cost(self):
        eoq = calculate_eoq(1000, 50, 0)
        assert eoq == 0.0

    def test_zero_demand(self):
        eoq = calculate_eoq(0, 50, 5)
        assert eoq == 0.0

    def test_higher_order_cost_means_larger_eoq(self):
        low = calculate_eoq(1000, 25, 5)
        high = calculate_eoq(1000, 100, 5)
        assert high > low


class TestSuggestOrderQuantity:
    def test_shortage_only(self):
        qty = suggest_order_quantity(
            shortage_qty=50,
            safety_stock_qty=0,
            avg_daily_demand=10,
            lead_time_days=7,
        )
        assert qty == 50

    def test_shortage_plus_safety_stock(self):
        qty = suggest_order_quantity(
            shortage_qty=50,
            safety_stock_qty=30,
            avg_daily_demand=10,
            lead_time_days=7,
        )
        assert qty == 80

    def test_eoq_floor(self):
        qty = suggest_order_quantity(
            shortage_qty=5,
            safety_stock_qty=5,
            avg_daily_demand=10,
            lead_time_days=7,
            eoq=100,
        )
        assert qty == 100

    def test_min_order_qty(self):
        qty = suggest_order_quantity(
            shortage_qty=0,
            safety_stock_qty=0,
            avg_daily_demand=10,
            lead_time_days=7,
            min_order_qty=25,
        )
        assert qty == 25

    def test_order_multiple_rounding(self):
        qty = suggest_order_quantity(
            shortage_qty=53,
            safety_stock_qty=0,
            avg_daily_demand=10,
            lead_time_days=7,
            order_multiple=10,
        )
        assert qty == 60

    def test_max_order_qty(self):
        qty = suggest_order_quantity(
            shortage_qty=200,
            safety_stock_qty=100,
            avg_daily_demand=10,
            lead_time_days=7,
            max_order_qty=150,
        )
        assert qty == 150


class TestGeneratePOSuggestions:
    def test_basic_suggestion(self):
        shortages = [
            {
                "product_id": "P001",
                "component_name": "Widget A",
                "shortage_qty": 100,
                "avg_daily_demand": 10,
                "demand_std_dev": 2,
                "required_date": "2026-07-01",
            }
        ]
        suppliers = {
            "P001": {
                "supplier_id": "S001",
                "supplier_name": "Acme Parts",
                "lead_time_days": 7,
                "lead_time_std_dev": 1,
                "unit_cost": 25.0,
                "min_order_qty": 10,
                "order_multiple": 1,
            }
        }

        suggestions = generate_po_suggestions(shortages, suppliers)
        assert len(suggestions) == 1
        s = suggestions[0]
        assert s["product_id"] == "P001"
        assert s["supplier_id"] == "S001"
        assert s["order_quantity"] >= 100
        assert s["unit_cost"] == 25.0
        assert s["total_cost"] > 0
        assert "suggested_order_date" in s
        assert "expected_delivery_date" in s

    def test_urgent_priority(self):
        shortages = [
            {
                "product_id": "P001",
                "shortage_qty": 200,
                "avg_daily_demand": 10,
                "required_date": "2026-07-01",
            }
        ]
        suppliers = {
            "P001": {
                "supplier_id": "S001",
                "lead_time_days": 7,
                "lead_time_std_dev": 1,
                "unit_cost": 10.0,
            }
        }

        suggestions = generate_po_suggestions(shortages, suppliers, service_level=0.95)
        assert suggestions[0]["priority"] == "urgent"

    def test_normal_priority(self):
        shortages = [
            {
                "product_id": "P001",
                "shortage_qty": 5,
                "avg_daily_demand": 10,
                "required_date": "2026-07-01",
            }
        ]
        suppliers = {
            "P001": {
                "supplier_id": "S001",
                "lead_time_days": 7,
                "lead_time_std_dev": 1,
                "unit_cost": 10.0,
            }
        }

        suggestions = generate_po_suggestions(shortages, suppliers, service_level=0.95)
        assert suggestions[0]["priority"] == "normal"

    def test_sorted_by_priority_and_date(self):
        shortages = [
            {
                "product_id": "P001",
                "shortage_qty": 5,
                "avg_daily_demand": 10,
                "required_date": "2026-07-15",
            },
            {
                "product_id": "P002",
                "shortage_qty": 200,
                "avg_daily_demand": 10,
                "required_date": "2026-07-01",
            },
        ]
        suppliers = {
            "P001": {
                "supplier_id": "S001",
                "lead_time_days": 7,
                "lead_time_std_dev": 1,
                "unit_cost": 10.0,
            },
            "P002": {
                "supplier_id": "S002",
                "lead_time_days": 7,
                "lead_time_std_dev": 1,
                "unit_cost": 10.0,
            },
        }

        suggestions = generate_po_suggestions(shortages, suppliers)
        assert suggestions[0]["priority"] == "urgent"
        assert suggestions[0]["product_id"] == "P002"

    def test_empty_shortages(self):
        suggestions = generate_po_suggestions([], {})
        assert len(suggestions) == 0


class TestMergePOSuggestions:
    def test_merge_same_product_supplier(self):
        suggestions = [
            {
                "product_id": "P001",
                "supplier_id": "S001",
                "order_quantity": 50,
                "unit_cost": 10.0,
                "total_cost": 500,
                "shortage_qty": 40,
                "safety_stock_qty": 10,
                "suggested_order_date": "2026-06-20",
                "expected_delivery_date": "2026-06-27",
                "priority": "normal",
            },
            {
                "product_id": "P001",
                "supplier_id": "S001",
                "order_quantity": 30,
                "unit_cost": 10.0,
                "total_cost": 300,
                "shortage_qty": 25,
                "safety_stock_qty": 10,
                "suggested_order_date": "2026-06-22",
                "expected_delivery_date": "2026-07-01",
                "priority": "normal",
            },
        ]

        merged = merge_po_suggestions(suggestions)
        assert len(merged) == 1
        assert merged[0]["order_quantity"] == 80
        assert merged[0]["total_cost"] == 800
        assert merged[0]["shortage_qty"] == 65
        assert merged[0]["expected_delivery_date"] == "2026-07-01"
        assert merged[0]["suggested_order_date"] == "2026-06-20"

    def test_different_products_not_merged(self):
        suggestions = [
            {
                "product_id": "P001",
                "supplier_id": "S001",
                "order_quantity": 50,
                "total_cost": 500,
                "shortage_qty": 40,
                "safety_stock_qty": 10,
                "suggested_order_date": "2026-06-20",
                "expected_delivery_date": "2026-06-27",
                "priority": "normal",
            },
            {
                "product_id": "P002",
                "supplier_id": "S001",
                "order_quantity": 30,
                "total_cost": 300,
                "shortage_qty": 25,
                "safety_stock_qty": 10,
                "suggested_order_date": "2026-06-22",
                "expected_delivery_date": "2026-07-01",
                "priority": "normal",
            },
        ]

        merged = merge_po_suggestions(suggestions)
        assert len(merged) == 2

    def test_urgent_preserved_after_merge(self):
        suggestions = [
            {
                "product_id": "P001",
                "supplier_id": "S001",
                "order_quantity": 50,
                "total_cost": 500,
                "shortage_qty": 40,
                "safety_stock_qty": 10,
                "suggested_order_date": "2026-06-20",
                "expected_delivery_date": "2026-06-27",
                "priority": "normal",
            },
            {
                "product_id": "P001",
                "supplier_id": "S001",
                "order_quantity": 50,
                "total_cost": 500,
                "shortage_qty": 100,
                "safety_stock_qty": 10,
                "suggested_order_date": "2026-06-22",
                "expected_delivery_date": "2026-07-01",
                "priority": "urgent",
            },
        ]

        merged = merge_po_suggestions(suggestions)
        assert len(merged) == 1
        assert merged[0]["priority"] == "urgent"
        assert merged[0]["shortage_qty"] == 140
