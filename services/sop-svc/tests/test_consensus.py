from pytest import approx

from app.core.consensus import calculate_consensus_qty


def test_calculate_consensus_qty_all_sources():
    assert calculate_consensus_qty(
        sales=100,
        statistical=120,
        marketing=90,
        finance=110,
    ) == approx(107.0)


def test_calculate_consensus_qty_redistributes_null_weights():
    assert calculate_consensus_qty(sales=100, statistical=120) == approx(111.4285714286)


def test_calculate_consensus_qty_all_none():
    assert calculate_consensus_qty() == 0.0
