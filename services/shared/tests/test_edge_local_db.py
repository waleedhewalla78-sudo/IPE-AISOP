import json
import os
import tempfile
import pytest
from datetime import UTC, datetime
from ipe_shared.edge.local_db import EdgeLocalDB


class TestEdgeLocalDB:
    @pytest.fixture
    def db(self, tmp_path):
        db_path = str(tmp_path / "test_edge.db")
        local_db = EdgeLocalDB(db_path)
        local_db.connect()
        local_db.initialize_schema()
        yield local_db
        local_db.close()

    def test_initialize_schema(self, db):
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row["name"] for row in cursor}
        assert "edge_operations" in tables
        assert "quality_events" in tables
        assert "work_order_confirmations" in tables
        assert "schedule_cache" in tables
        assert "sync_queue" in tables
        assert "sync_meta" in tables

    def test_save_operation(self, db):
        operation = {
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
            "status": "in_progress",
            "actual_qty": 10,
        }
        op_id = db.save_operation(operation)
        assert op_id == "op-001"

        cursor = db.conn.execute(
            "SELECT * FROM edge_operations WHERE id = ?", ("op-001",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["mo_id"] == "mo-001"
        assert row["status"] == "in_progress"
        assert row["cloud_synced"] == 0

    def test_save_quality_event(self, db):
        event = {
            "id": "qe-001",
            "mo_id": "mo-001",
            "product_id": "prod-001",
            "event_type": "defect_detected",
            "severity": "major",
            "defect_count": 3,
        }
        event_id = db.save_quality_event(event)
        assert event_id == "qe-001"

        cursor = db.conn.execute(
            "SELECT * FROM quality_events WHERE id = ?", ("qe-001",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["severity"] == "major"
        assert row["defect_count"] == 3

    def test_save_confirmation(self, db):
        confirmation = {
            "id": "conf-001",
            "work_order_id": "wo-001",
            "mo_id": "mo-001",
            "confirmation_type": "production",
            "quantity": 50,
            "duration_mins": 120,
        }
        conf_id = db.save_confirmation(confirmation)
        assert conf_id == "conf-001"

        cursor = db.conn.execute(
            "SELECT * FROM work_order_confirmations WHERE id = ?", ("conf-001",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["quantity"] == 50

    def test_save_schedule(self, db):
        payload = {"id": "mo-001", "status": "scheduled", "planned_start": "2026-07-01T08:00:00Z"}
        db.save_schedule("manufacturing_order", "mo-001", payload, version=1)

        schedule = db.get_schedule("manufacturing_order", "mo-001")
        assert schedule is not None
        assert schedule["payload"]["status"] == "scheduled"
        assert schedule["version"] == 1

    def test_get_pending_sync_records(self, db):
        db.save_operation({
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
        })

        records = db.get_pending_sync_records()
        assert len(records) == 1
        assert records[0]["entity_type"] == "edge_operations"
        assert records[0]["entity_id"] == "op-001"

    def test_mark_synced(self, db):
        db.save_operation({
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
        })

        records = db.get_pending_sync_records()
        assert len(records) == 1

        db.mark_synced([records[0]["id"]])

        pending = db.get_pending_sync_records()
        assert len(pending) == 0

    def test_mark_failed(self, db):
        db.save_operation({
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
        })

        records = db.get_pending_sync_records()
        db.mark_failed(records[0]["id"], "network_error")

        cursor = db.conn.execute(
            "SELECT * FROM sync_queue WHERE id = ?", (records[0]["id"],)
        )
        row = cursor.fetchone()
        assert row["status"] == "failed"
        assert row["error_message"] == "network_error"
        assert row["retry_count"] == 1

    def test_mark_entity_synced(self, db):
        db.save_operation({
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
        })

        db.mark_entity_synced("edge_operations", "op-001", 5)

        cursor = db.conn.execute(
            "SELECT * FROM edge_operations WHERE id = ?", ("op-001",)
        )
        row = cursor.fetchone()
        assert row["cloud_synced"] == 1
        assert row["cloud_version"] == 5

    def test_get_unsynced_count(self, db):
        db.save_operation({
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
        })
        db.save_quality_event({
            "id": "qe-001",
            "mo_id": "mo-001",
            "product_id": "prod-001",
            "event_type": "defect_detected",
        })

        counts = db.get_unsynced_count()
        assert counts["edge_operations"] == 1
        assert counts["quality_events"] == 1
        assert counts["work_order_confirmations"] == 0

    def test_sync_meta(self, db):
        db.set_sync_meta("last_pull_token", "token_123")
        token = db.get_sync_meta("last_pull_token")
        assert token == "token_123"

        db.set_sync_meta("last_pull_token", "token_456")
        token = db.get_sync_meta("last_pull_token")
        assert token == "token_456"

    def test_schedule_expiry(self, db):
        payload = {"id": "mo-001", "status": "scheduled"}
        db.save_schedule("manufacturing_order", "mo-001", payload)

        db.conn.execute(
            """UPDATE schedule_cache
               SET expires_at = datetime('now', '-1 hour')
               WHERE entity_id = 'mo-001'"""
        )
        db.conn.commit()

        schedule = db.get_schedule("manufacturing_order", "mo-001")
        assert schedule is None

    def test_multiple_operations_pending(self, db):
        for i in range(5):
            db.save_operation({
                "id": f"op-{i:03d}",
                "mo_id": f"mo-{i:03d}",
                "work_center_id": "wc-001",
                "operation_name": f"Op {i}",
            })

        records = db.get_pending_sync_records(limit=3)
        assert len(records) == 3

    def test_insert_or_replace_operation(self, db):
        db.save_operation({
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
            "status": "pending",
        })

        db.save_operation({
            "id": "op-001",
            "mo_id": "mo-001",
            "work_center_id": "wc-001",
            "operation_name": "Assembly",
            "status": "in_progress",
        })

        cursor = db.conn.execute(
            "SELECT COUNT(*) as cnt FROM edge_operations WHERE id = 'op-001'"
        )
        assert cursor.fetchone()["cnt"] == 1

        cursor = db.conn.execute(
            "SELECT status FROM edge_operations WHERE id = 'op-001'"
        )
        assert cursor.fetchone()["status"] == "in_progress"
