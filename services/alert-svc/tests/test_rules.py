from app.core.rules import evaluate_event, Alert


def test_evaluate_feasibility_high_alert():
    payload = {
        "feasibility_score": 55,
        "mo_id": "MO-001",
        "tenant_id": "tenant-1",
        "primary_constraint": "material",
    }
    alerts = evaluate_event("ipe.mo.feasibility_scored", payload)
    assert len(alerts) == 1
    a = alerts[0]
    assert a.alert_type == "feasibility_critical"
    assert a.severity == "high"
    assert "MO-001" in a.title
    assert a.entity_id == "MO-001"
    assert a.metadata["score"] == 55


def test_evaluate_feasibility_no_alert():
    payload = {"feasibility_score": 85, "mo_id": "MO-002"}
    alerts = evaluate_event("ipe.mo.feasibility_scored", payload)
    assert len(alerts) == 0


def test_evaluate_workcenter_high_alert():
    payload = {
        "utilization_pct": 92,
        "work_center_id": "WC-1",
        "work_center_name": "Assembly Line A",
        "tenant_id": "tenant-1",
    }
    alerts = evaluate_event("ipe.workcenter.status_changed", payload)
    assert len(alerts) == 1
    a = alerts[0]
    assert a.alert_type == "workcenter_overloaded"
    assert a.severity == "medium"
    assert "Assembly Line A" in a.title


def test_evaluate_unknown_event():
    alerts = evaluate_event("ipe.unknown.event", {})
    assert len(alerts) == 0
