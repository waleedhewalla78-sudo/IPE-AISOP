"""A8 customer portal helpers."""

from app.core.customer_portal import build_portal_summary, delivery_confidence, map_order_status


def test_map_status():
    assert map_order_status("open") == "confirmed"
    assert map_order_status("shipped") == "shipped"


def test_confidence_colors():
    assert delivery_confidence(5, 0.05)["color"] == "green"
    assert delivery_confidence(-1, 0.5)["color"] == "red"


def test_portal_summary_readonly():
    data = build_portal_summary(
        [{"id": "1", "order_number": "SO-1", "status": "promised", "days_to_due": 4, "otd_risk": 0.05}]
    )
    assert data["read_only"] is True
    assert data["orders"][0]["confidence"] == "on_track"
