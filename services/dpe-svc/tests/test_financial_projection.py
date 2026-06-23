import pytest
from app.core.financial_projection import (
    FinancialProjectionInput,
    BOMComponent,
    RoutingStep,
    calculate_material_cost,
    calculate_labor_cost,
    calculate_energy_cost,
    calculate_wip_value,
    assess_margin,
    generate_financial_projection,
)


class TestCalculateMaterialCost:
    def test_basic(self):
        components = [BOMComponent("c1", 2.0, 10.0)]
        total, unit = calculate_material_cost(components, 100)
        assert total == 2000.0
        assert unit == 20.0

    def test_with_scrap(self):
        components = [BOMComponent("c1", 2.0, 10.0, scrap_rate_pct=10.0)]
        total, unit = calculate_material_cost(components, 100)
        assert total == pytest.approx(2200.0)

    def test_multiple_components(self):
        components = [
            BOMComponent("c1", 1.0, 10.0),
            BOMComponent("c2", 3.0, 5.0),
        ]
        total, unit = calculate_material_cost(components, 100)
        assert total == 2500.0

    def test_zero_quantity(self):
        components = [BOMComponent("c1", 2.0, 10.0)]
        total, unit = calculate_material_cost(components, 0)
        assert total == 0.0
        assert unit == 0.0


class TestCalculateLaborCost:
    def test_basic(self):
        steps = [RoutingStep("wc1", 60.0, 50.0)]
        cost = calculate_labor_cost(steps, 100, 50.0)
        assert cost == 5000.0

    def test_multiple_steps(self):
        steps = [
            RoutingStep("wc1", 30.0, 50.0),
            RoutingStep("wc2", 60.0, 50.0),
        ]
        cost = calculate_labor_cost(steps, 10, 50.0)
        assert cost == 750.0


class TestCalculateEnergyCost:
    def test_basic(self):
        steps = [RoutingStep("wc1", 60.0, 50.0, 10.0, 0.1)]
        cost = calculate_energy_cost(steps, 100)
        assert cost == pytest.approx(100.0)


class TestCalculateWipValue:
    def test_full_completion(self):
        components = [BOMComponent("c1", 1.0, 10.0)]
        steps = [RoutingStep("wc1", 60.0, 50.0, 10.0, 0.1)]
        wip = calculate_wip_value(components, steps, 100, 100.0)
        assert wip > 0

    def test_partial_completion(self):
        components = [BOMComponent("c1", 1.0, 10.0)]
        steps = [RoutingStep("wc1", 60.0, 50.0, 10.0, 0.1)]
        wip_full = calculate_wip_value(components, steps, 100, 100.0)
        wip_half = calculate_wip_value(components, steps, 100, 50.0)
        assert wip_half < wip_full


class TestAssessMargin:
    def test_negative(self):
        assert assess_margin(-5.0) == "negative_margin"

    def test_low(self):
        assert assess_margin(3.0) == "low_margin_warning"

    def test_below_target(self):
        assert assess_margin(8.0) == "margin_below_target"

    def test_ok(self):
        assert assess_margin(15.0) is None


class TestGenerateFinancialProjection:
    def test_basic(self):
        input_data = FinancialProjectionInput(
            product_id="p1",
            quantity=100,
            selling_price=50.0,
            bom_components=[BOMComponent("c1", 2.0, 10.0)],
            routing_steps=[RoutingStep("wc1", 60.0, 50.0, 10.0, 0.1)],
        )
        result = generate_financial_projection(input_data)
        assert result.quantity == 100
        assert result.total_cost > 0
        assert result.revenue == 5000.0

    def test_margin_alert_negative(self):
        input_data = FinancialProjectionInput(
            product_id="p1",
            quantity=100,
            selling_price=1.0,
            bom_components=[BOMComponent("c1", 2.0, 10.0)],
            routing_steps=[RoutingStep("wc1", 60.0, 50.0)],
        )
        result = generate_financial_projection(input_data)
        assert result.margin_alert == "negative_margin"

    def test_wip_value(self):
        input_data = FinancialProjectionInput(
            product_id="p1",
            quantity=100,
            bom_components=[BOMComponent("c1", 2.0, 10.0)],
            routing_steps=[RoutingStep("wc1", 60.0, 50.0, 10.0, 0.1)],
        )
        result = generate_financial_projection(input_data)
        assert result.wip_value > 0

    def test_cost_breakdown(self):
        input_data = FinancialProjectionInput(
            product_id="p1",
            quantity=100,
            bom_components=[BOMComponent("c1", 2.0, 10.0)],
            routing_steps=[RoutingStep("wc1", 60.0, 50.0, 10.0, 0.1)],
        )
        result = generate_financial_projection(input_data)
        assert "material" in result.cost_breakdown
        assert "labor" in result.cost_breakdown
        assert "energy" in result.cost_breakdown
        assert "overhead" in result.cost_breakdown
