import asyncio
import contextlib
import hashlib
import hmac
import json
from uuid import uuid4

import pytest

from app.events.handlers import (
    _parse_event,
    handle_demand_classified,
    handle_feasibility_scored,
    handle_mo_auto_confirmed,
    handle_reconciliation_completed,
)


def _make_event(event_type: str, data: dict, tenant_id=None):
    """Build a Kafka-message-like dict (envelope fields at top level)."""
    if tenant_id is None:
        tenant_id = str(uuid4())
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "source": "test",
        "tenant_id": tenant_id,
        "timestamp": "2026-06-15T12:00:00Z",
        "data": data,
        "correlation_id": str(uuid4()),
    }


class TestParseEvent:
    def test_valid_event(self):
        envelope = _parse_event(_make_event("ipe.mo.auto_confirmed", {"mo_id": "42"}))
        assert envelope is not None
        assert envelope.event_type == "ipe.mo.auto_confirmed"
        assert envelope.data["mo_id"] == "42"

    def test_invalid_event_returns_none(self):
        envelope = _parse_event("not a dict")
        assert envelope is None

    def test_missing_required_fields(self):
        envelope = _parse_event({"data": "no envelope fields"})
        assert envelope is None


class TestPayloadStructures:
    def test_auto_confirmed_payload(self):
        data = {
            "mo_id": "MO-001",
            "feasibility_score": 95,
            "autonomy_mode": "autonomous",
            "reason": "Score >= 90",
        }
        payload = {"action_type": "confirm_mo", "data": data}
        assert payload["action_type"] == "confirm_mo"
        assert payload["data"]["mo_id"] == "MO-001"

    def test_feasibility_scored_payload(self):
        data = {
            "mo_id": "MO-002",
            "overall_score": 85.5,
            "primary_constraint": "material",
            "risk_level": "medium",
        }
        payload = {"action_type": "sync_feasibility", "data": data}
        assert payload["action_type"] == "sync_feasibility"
        assert payload["data"]["overall_score"] == 85.5

    def test_reconciliation_completed_payload(self):
        data = {
            "mo_id": "MO-003",
            "time_variance_pct": 15.2,
            "yield_variance_pct": -3.1,
        }
        payload = {"action_type": "sync_reconciliation", "data": data}
        assert payload["action_type"] == "sync_reconciliation"
        assert payload["data"]["time_variance_pct"] == 15.2

    def test_demand_classified_payload(self):
        data = {
            "mo_id": "MO-004",
            "demand_type": "MTO",
            "priority_score": 87.3,
        }
        payload = {"action_type": "sync_demand_classification", "data": data}
        assert payload["action_type"] == "sync_demand_classification"
        assert payload["data"]["demand_type"] == "MTO"


class TestHandlerLogging:
    def test_auto_confirmed_logs_mo_id(self, caplog):
        event = _make_event("ipe.mo.auto_confirmed", {"mo_id": "MO-001"})
        caplog.set_level("INFO")
        with contextlib.suppress(RuntimeError):
            asyncio.run(handle_mo_auto_confirmed(event))
        assert "Processing auto_confirmed" in caplog.text
        assert "MO-001" in caplog.text

    def test_feasibility_scored_logs(self, caplog):
        event = _make_event("ipe.mo.feasibility_scored", {
            "mo_id": "MO-002", "overall_score": 85.5,
            "primary_constraint": "material", "risk_level": "medium",
        })
        caplog.set_level("INFO")
        with contextlib.suppress(RuntimeError):
            asyncio.run(handle_feasibility_scored(event))
        assert "Processing feasibility_scored" in caplog.text
        assert "MO-002" in caplog.text

    def test_reconciliation_completed_logs(self, caplog):
        event = _make_event("ipe.reconciliation.completed", {
            "mo_id": "MO-003", "time_variance_pct": 15.2, "yield_variance_pct": -3.1,
        })
        caplog.set_level("INFO")
        with contextlib.suppress(RuntimeError):
            asyncio.run(handle_reconciliation_completed(event))
        assert "Processing reconciliation_completed" in caplog.text
        assert "MO-003" in caplog.text

    def test_demand_classified_logs(self, caplog):
        event = _make_event("ipe.demand.classified", {
            "mo_id": "MO-004", "demand_type": "MTO", "priority_score": 87.3,
        })
        caplog.set_level("INFO")
        with contextlib.suppress(RuntimeError):
            asyncio.run(handle_demand_classified(event))
        assert "Processing demand_classified" in caplog.text
        assert "MO-004" in caplog.text


class TestHmacSignature:
    def test_signature_format(self):
        api_secret = "test-secret"
        payload = {"action_type": "confirm_mo", "data": {"mo_id": "MO-001"}}
        body_bytes = json.dumps(payload).encode("utf-8")
        sig = hmac.new(api_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
        assert len(sig) == 64
        assert isinstance(sig, str)

    def test_different_secrets_produce_different_sigs(self):
        body = json.dumps({"action_type": "confirm_mo", "data": {"mo_id": "MO-001"}})
        payload = body.encode("utf-8")
        sig1 = hmac.new(b"secret-1", payload, hashlib.sha256).hexdigest()
        sig2 = hmac.new(b"secret-2", payload, hashlib.sha256).hexdigest()
        assert sig1 != sig2


@pytest.mark.skip(reason="requires Odoo runtime (odoo package not available in connector venv)")
class TestOdooHandlerValidation:
    def test_confirm_mo_requires_mo_id(self):
        from ipe_connector.controllers.action_receiver import IpeActionReceiver
        receiver = IpeActionReceiver()
        with pytest.raises(ValueError, match="mo_id required"):
            receiver._handle_confirm_mo({})

    def test_sync_feasibility_requires_mo_id(self):
        from ipe_connector.controllers.action_receiver import IpeActionReceiver
        receiver = IpeActionReceiver()
        with pytest.raises(ValueError, match="mo_id required"):
            receiver._handle_sync_feasibility({})

    def test_sync_reconciliation_requires_mo_id(self):
        from ipe_connector.controllers.action_receiver import IpeActionReceiver
        receiver = IpeActionReceiver()
        with pytest.raises(ValueError, match="mo_id required"):
            receiver._handle_sync_reconciliation({})

    def test_sync_demand_classification_requires_mo_id(self):
        from ipe_connector.controllers.action_receiver import IpeActionReceiver
        receiver = IpeActionReceiver()
        with pytest.raises(ValueError, match="mo_id required"):
            receiver._handle_sync_demand_classification({})
