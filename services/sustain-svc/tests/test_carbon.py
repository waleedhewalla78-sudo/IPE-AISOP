"""A12 carbon + ESG unit tests."""

from app.core.carbon import calculate_product_carbon, score_supplier_esg


def test_product_carbon_total_and_reductions():
    data = calculate_product_carbon("FG-DT100")
    assert data["agent_id"] == "A12"
    assert data["total_kg_co2e"] > 0
    assert data["reduction_opportunities"]
    assert data["better_than_average_pct"] is not None


def test_supplier_esg_flag():
    good = score_supplier_esg("Shanghai Silicon Steel Co.", environmental=78, social=72, governance=80)
    assert good["overall_esg"] >= 70
    assert good["flag"] == "ok"
    weak = score_supplier_esg("Cairo Copper Industries", environmental=45, social=62, governance=55)
    assert weak["flag"] in ("watch", "risk")
