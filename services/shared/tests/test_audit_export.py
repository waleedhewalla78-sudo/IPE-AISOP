"""Tests for audit export helpers."""

from ipe_shared.audit.export import audit_rows_to_csv


def test_audit_rows_to_csv_empty():
    csv_text = audit_rows_to_csv([])
    assert "id" in csv_text


def test_audit_rows_to_csv_with_data():
    rows = [
        {
            "id": "1",
            "tenant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "actor_type": "user",
            "actor_id": "u1",
            "action": "HTTP_POST",
            "entity_type": "api_request",
            "entity_id": "e1",
            "timestamp": "2026-01-01T00:00:00Z",
        }
    ]
    csv_text = audit_rows_to_csv(rows)
    assert "HTTP_POST" in csv_text
