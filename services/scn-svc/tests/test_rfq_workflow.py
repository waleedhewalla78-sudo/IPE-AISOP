import pytest

from app.core.rfq_workflow import (
    RFQState,
    _rfq_response_store,
    _rfq_store,
    award_rfq,
    cancel_rfq,
    create_rfq,
    evaluate_rfq,
    publish_rfq,
    respond_to_rfq,
)


@pytest.fixture(autouse=True)
def clear_stores():
    _rfq_store.clear()
    _rfq_response_store.clear()
    yield
    _rfq_store.clear()
    _rfq_response_store.clear()


class TestCreateRFQ:
    def test_basic_creation(self):
        result = create_rfq("tenant-1", {"title": "Test RFQ"})
        assert result["title"] == "Test RFQ"
        assert result["state"] == RFQState.DRAFT
        assert result["tenant_id"] == "tenant-1"
        assert "rfq_id" in result

    def test_creation_with_items(self):
        items = [{"name": "Widget A", "qty": 100}]
        result = create_rfq("tenant-1", {"title": "RFQ", "items": items})
        assert result["items"] == items

    def test_creation_with_requirements(self):
        reqs = {"delivery_window": "30d", "certification": "ISO9001"}
        result = create_rfq("tenant-1", {"title": "RFQ", "requirements": reqs})
        assert result["requirements"] == reqs

    def test_creation_with_deadline(self):
        result = create_rfq("tenant-1", {"title": "RFQ", "deadline": "2025-12-31"})
        assert result["deadline"] == "2025-12-31"


class TestPublishRFQ:
    def test_publish_draft(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        result = publish_rfq(rfq["rfq_id"])
        assert result["state"] == RFQState.PUBLISHED

    def test_publish_nonexistent_raises(self):
        with pytest.raises(ValueError, match="not found"):
            publish_rfq("nonexistent-id")

    def test_double_publish_raises(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        with pytest.raises(ValueError, match="Invalid transition"):
            publish_rfq(rfq["rfq_id"])


class TestRespondToRFQ:
    def test_respond_to_published(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        result = respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0, "lead_time_days": 14})
        assert result["supplier_id"] == "supp-1"
        assert result["price"] == 100.0
        assert result["lead_time_days"] == 14

    def test_respond_transitions_to_responding(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0})
        assert _rfq_store[rfq["rfq_id"]]["state"] == RFQState.RESPONDING

    def test_respond_to_draft_raises(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        with pytest.raises(ValueError, match="cannot accept responses"):
            respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0})

    def test_multiple_responses(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0})
        respond_to_rfq(rfq["rfq_id"], "supp-2", {"price": 95.0})
        assert len(_rfq_response_store[rfq["rfq_id"]]) == 2


class TestEvaluateRFQ:
    def test_evaluate_with_responses(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0, "lead_time_days": 14})
        result = evaluate_rfq(rfq["rfq_id"])
        assert result["state"] == RFQState.UNDER_REVIEW
        assert result["response_count"] == 1
        assert len(result["evaluations"]) == 1

    def test_evaluate_sorts_by_composite(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0, "lead_time_days": 14})
        respond_to_rfq(rfq["rfq_id"], "supp-2", {"price": 50.0, "lead_time_days": 7})
        result = evaluate_rfq(rfq["rfq_id"])
        assert result["evaluations"][0]["composite_score"] >= result["evaluations"][1]["composite_score"]

    def test_evaluate_from_responding(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0})
        evaluate_rfq(rfq["rfq_id"])
        assert _rfq_store[rfq["rfq_id"]]["state"] == RFQState.UNDER_REVIEW


class TestAwardRFQ:
    def test_award_after_review(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0})
        evaluate_rfq(rfq["rfq_id"])
        result = award_rfq(rfq["rfq_id"], "supp-1")
        assert result["state"] == RFQState.AWARDED
        assert result["awarded_supplier_id"] == "supp-1"

    def test_award_from_draft_raises(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        with pytest.raises(ValueError, match="Invalid transition"):
            award_rfq(rfq["rfq_id"], "supp-1")


class TestCancelRFQ:
    def test_cancel_draft(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        result = cancel_rfq(rfq["rfq_id"])
        assert result["state"] == RFQState.CANCELLED

    def test_cancel_published(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        result = cancel_rfq(rfq["rfq_id"])
        assert result["state"] == RFQState.CANCELLED

    def test_cancel_awarded_raises(self):
        rfq = create_rfq("tenant-1", {"title": "Test"})
        publish_rfq(rfq["rfq_id"])
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 100.0})
        evaluate_rfq(rfq["rfq_id"])
        award_rfq(rfq["rfq_id"], "supp-1")
        with pytest.raises(ValueError, match="Invalid transition"):
            cancel_rfq(rfq["rfq_id"])


class TestRFQLifecycle:
    def test_full_lifecycle(self):
        rfq = create_rfq("tenant-1", {"title": "Full Lifecycle"})
        assert rfq["state"] == RFQState.DRAFT
        publish_rfq(rfq["rfq_id"])
        assert _rfq_store[rfq["rfq_id"]]["state"] == RFQState.PUBLISHED
        respond_to_rfq(rfq["rfq_id"], "supp-1", {"price": 80.0, "lead_time_days": 7})
        assert _rfq_store[rfq["rfq_id"]]["state"] == RFQState.RESPONDING
        evaluate_rfq(rfq["rfq_id"])
        assert _rfq_store[rfq["rfq_id"]]["state"] == RFQState.UNDER_REVIEW
        result = award_rfq(rfq["rfq_id"], "supp-1")
        assert result["state"] == RFQState.AWARDED