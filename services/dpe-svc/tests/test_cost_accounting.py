from app.core.cost_accounting import (
    DEFAULT_GL_ACCOUNT_MAP,
    compute_cogm,
    compute_copq,
    compute_cost_accounting,
    compute_variance_analysis,
    get_gl_account_map,
)


class TestComputeCOGM:
    def test_basic_cogm(self):
        result = compute_cogm(
            material_cost=1000, labor_cost=500, energy_cost=200, overhead_cost=150, quantity=100
        )
        assert result.total_cogm == 1850.0
        assert result.cogm_per_unit == 18.5

    def test_gl_accounts_populated(self):
        result = compute_cogm(100, 50, 20, 30, 10)
        assert "5100-RAW-MATERIAL" in result.gl_accounts
        assert "5200-DIRECT-LABOR" in result.gl_accounts
        assert "5300-ENERGY" in result.gl_accounts
        assert "5400-MFG-OVERHEAD" in result.gl_accounts

    def test_zero_quantity(self):
        result = compute_cogm(100, 50, 20, 30, 0)
        assert result.cogm_per_unit == 0.0

    def test_single_unit(self):
        result = compute_cogm(100, 50, 20, 30, 1)
        assert result.cogm_per_unit == 200.0
        assert result.total_cogm == 200.0


class TestComputeCOPQ:
    def test_basic_copq(self):
        result = compute_copq(1000, defect_rate_pct=5.0, rework_rate_pct=2.0)
        assert result.scrap_cost > 0
        assert result.rework_cost > 0
        assert result.inspection_cost > 0
        assert result.warranty_cost > 0
        assert result.total_copq > 0

    def test_copq_pct_of_revenue(self):
        result = compute_copq(100, selling_price_per_unit=200)
        assert result.copq_as_pct_of_revenue > 0

    def test_zero_defect_rate(self):
        result = compute_copq(100, defect_rate_pct=0.0, rework_rate_pct=0.0)
        assert result.scrap_cost == 0.0
        assert result.rework_cost == 0.0
        assert result.inspection_cost > 0

    def test_high_defect_rate(self):
        result = compute_copq(100, defect_rate_pct=10.0)
        assert result.scrap_cost > 0
        assert result.total_copq > result.inspection_cost


class TestVarianceAnalysis:
    def test_basic_variance(self):
        planned = {"material": 1000, "labor": 500}
        actual = {"material": 1100, "labor": 450}
        variances = compute_variance_analysis(planned, actual)
        assert len(variances) == 2
        mat_var = [v for v in variances if v.cost_element == "material"][0]
        assert mat_var.variance == 100.0
        assert mat_var.variance_pct == 10.0

    def test_missing_actual_key(self):
        planned = {"material": 1000}
        actual: dict[str, float] = {}
        variances = compute_variance_analysis(planned, actual)
        assert len(variances) == 1
        assert variances[0].actual == 0.0
        assert variances[0].variance == -1000.0

    def test_extra_actual_key(self):
        planned: dict[str, float] = {}
        actual = {"material": 1000}
        variances = compute_variance_analysis(planned, actual)
        material_vars = [v for v in variances if v.cost_element == "material"]
        assert len(material_vars) == 1

    def test_zero_planned_variance_pct(self):
        planned = {"material": 0}
        actual = {"material": 100}
        variances = compute_variance_analysis(planned, actual)
        assert variances[0].variance_pct == 0.0


class TestFullCostAccounting:
    def test_full_cost_result(self):
        result = compute_cost_accounting(
            product_id="PROD-001",
            quantity=100,
            selling_price=50.0,
            material_cost=2000.0,
            labor_cost=1000.0,
            energy_cost=500.0,
            overhead_cost=300.0,
        )
        assert result.revenue == 5000.0
        assert result.cogm.total_cogm == 3800.0
        assert result.copq.total_copq > 0
        assert result.gross_margin == 1200.0
        assert result.net_margin < result.gross_margin

    def test_margin_pct(self):
        result = compute_cost_accounting(
            product_id="PROD-001",
            quantity=100,
            selling_price=100.0,
            material_cost=3000.0,
            labor_cost=1000.0,
            energy_cost=500.0,
            overhead_cost=500.0,
        )
        assert result.gross_margin_pct > 0
        assert result.net_margin_pct < result.gross_margin_pct

    def test_with_actual_costs(self):
        actual = {"material": 3300.0, "labor": 1100.0}
        result = compute_cost_accounting(
            product_id="PROD-001",
            quantity=100,
            selling_price=100.0,
            material_cost=3000.0,
            labor_cost=1000.0,
            energy_cost=500.0,
            overhead_cost=500.0,
            actual_costs=actual,
        )
        assert len(result.variances) >= 2
        mat_var = [v for v in result.variances if v.cost_element == "material"][0]
        assert mat_var.variance == 300.0

    def test_xai_factors_populated(self):
        result = compute_cost_accounting(
            product_id="P1", quantity=100, selling_price=100.0,
            material_cost=1000.0, labor_cost=500.0, energy_cost=200.0, overhead_cost=100.0,
        )
        assert "cogm_weight" in result.xai_factors
        assert "copq_weight" in result.xai_factors
        assert "margin_health" in result.xai_factors

    def test_zero_revenue_margin(self):
        result = compute_cost_accounting(
            product_id="P1", quantity=100, selling_price=0.0,
            material_cost=100.0, labor_cost=50.0, energy_cost=10.0, overhead_cost=5.0,
        )
        assert result.gross_margin_pct == 0.0
        assert result.net_margin_pct == 0.0