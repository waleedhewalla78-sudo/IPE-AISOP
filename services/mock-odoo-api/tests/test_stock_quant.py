"""Unit tests for mock Odoo stock.quant fidelity (Spec 019)."""

from app.main import _execute_kw, _sample_quants


def test_sample_quants_non_empty():
    quants = _sample_quants()
    assert len(quants) >= 2
    assert all("product_id" in q and "quantity" in q for q in quants)


def test_search_read_stock_quant_returns_rows():
    rows = _execute_kw("stock.quant", "search_read", [[]], {"fields": ["product_id", "quantity"]})
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert rows[0]["product_id"][0] == 1
    assert float(rows[0]["quantity"]) > 0
