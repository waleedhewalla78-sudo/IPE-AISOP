import pytest
from ipe_shared.api.edge_sync import _detect_conflict, _is_simple_update


class TestDetectConflict:
    def test_no_conflict_new_record(self):
        result = _detect_conflict(
            {"payload": {"status": "pending"}, "local_timestamp": "2026-07-01T10:00:00Z", "version": 1},
            None,
        )
        assert result is None

    def test_no_conflict_same_version(self):
        result = _detect_conflict(
            {"payload": {"status": "pending"}, "local_timestamp": "2026-07-01T10:00:00Z", "version": 2},
            {"status": "pending", "version": 2, "updated_at": "2026-07-01T09:00:00Z"},
        )
        assert result is None

    def test_conflict_edge_newer_wins_simple(self):
        result = _detect_conflict(
            {"payload": {"actual_qty": 50}, "local_timestamp": "2026-07-01T11:00:00Z", "version": 1},
            {"status": "in_progress", "actual_qty": 30, "version": 2, "updated_at": "2026-07-01T10:00:00Z"},
        )
        assert result is not None
        assert result["conflict_type"] == "last_write_wins"
        assert result["resolution"] == "edge_wins"
        assert result["requires_manual"] is False

    def test_conflict_cloud_newer_wins_simple(self):
        result = _detect_conflict(
            {"payload": {"actual_qty": 50}, "local_timestamp": "2026-07-01T09:00:00Z", "version": 1},
            {"status": "in_progress", "actual_qty": 30, "version": 2, "updated_at": "2026-07-01T10:00:00Z"},
        )
        assert result is not None
        assert result["conflict_type"] == "last_write_wins"
        assert result["resolution"] == "cloud_wins"
        assert result["requires_manual"] is False

    def test_complex_conflict_requires_manual(self):
        result = _detect_conflict(
            {"payload": {"status": "completed", "operator_id": "op-1"}, "local_timestamp": "2026-07-01T11:00:00Z", "version": 1},
            {"status": "in_progress", "operator_id": "op-2", "version": 2, "updated_at": "2026-07-01T10:00:00Z"},
        )
        assert result is not None
        assert result["conflict_type"] == "complex_conflict"
        assert result["resolution"] == "requires_manual_resolution"
        assert result["requires_manual"] is True


class TestIsSimpleUpdate:
    def test_simple_qty_update(self):
        assert _is_simple_update({"actual_qty": 50}, {"actual_qty": 30}) is True

    def test_simple_status_update(self):
        assert _is_simple_update({"status": "completed"}, {"status": "in_progress"}) is True

    def test_complex_update_with_operator(self):
        assert _is_simple_update(
            {"status": "completed", "operator_id": "op-1"},
            {"status": "in_progress", "operator_id": "op-2"},
        ) is False

    def test_empty_payloads(self):
        assert _is_simple_update({}, {}) is True

    def test_non_simple_field(self):
        assert _is_simple_update(
            {"custom_field": "value"},
            {"custom_field": "other"},
        ) is False
