"""Edge Gateway SQLite schema for offline-first operation.

This module provides the local SQLite database schema for Edge Gateways,
mirroring critical UDM tables to enable shop floor operations during
cloud disconnections.
"""
import sqlite3
import json
from datetime import UTC, datetime
from typing import Any


EDGE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS edge_operations (
    id TEXT PRIMARY KEY,
    mo_id TEXT NOT NULL,
    work_order_id TEXT,
    work_center_id TEXT NOT NULL,
    operation_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    actual_qty REAL DEFAULT 0,
    actual_duration_mins REAL DEFAULT 0,
    scrap_qty REAL DEFAULT 0,
    scrap_reason TEXT,
    operator_id TEXT,
    started_at TEXT,
    completed_at TEXT,
    local_timestamp TEXT NOT NULL,
    cloud_synced INTEGER DEFAULT 0,
    cloud_version INTEGER DEFAULT 0,
    conflict_status TEXT,
    version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS quality_events (
    id TEXT PRIMARY KEY,
    mo_id TEXT NOT NULL,
    work_order_id TEXT,
    work_center_id TEXT,
    product_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT DEFAULT 'minor',
    defect_category TEXT,
    defect_count INTEGER DEFAULT 1,
    rework_required INTEGER DEFAULT 0,
    rework_cycles INTEGER DEFAULT 0,
    max_rework_cycles INTEGER DEFAULT 3,
    scrap_quantity INTEGER DEFAULT 0,
    cost_impact REAL DEFAULT 0.0,
    status TEXT DEFAULT 'open',
    operator_id TEXT,
    detected_at TEXT NOT NULL,
    local_timestamp TEXT NOT NULL,
    cloud_synced INTEGER DEFAULT 0,
    cloud_version INTEGER DEFAULT 0,
    conflict_status TEXT,
    version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS work_order_confirmations (
    id TEXT PRIMARY KEY,
    work_order_id TEXT NOT NULL,
    mo_id TEXT NOT NULL,
    confirmation_type TEXT NOT NULL,
    quantity REAL DEFAULT 0,
    duration_mins REAL DEFAULT 0,
    scrap_qty REAL DEFAULT 0,
    reject_qty REAL DEFAULT 0,
    reason TEXT,
    operator_id TEXT,
    confirmed_at TEXT NOT NULL,
    local_timestamp TEXT NOT NULL,
    cloud_synced INTEGER DEFAULT 0,
    cloud_version INTEGER DEFAULT 0,
    conflict_status TEXT,
    version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS schedule_cache (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    fetched_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    checksum TEXT
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    payload TEXT NOT NULL,
    local_timestamp TEXT NOT NULL,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS sync_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_operations_mo ON edge_operations(mo_id);
CREATE INDEX IF NOT EXISTS idx_operations_status ON edge_operations(status);
CREATE INDEX IF NOT EXISTS idx_operations_synced ON edge_operations(cloud_synced);
CREATE INDEX IF NOT EXISTS idx_quality_mo ON quality_events(mo_id);
CREATE INDEX IF NOT EXISTS idx_quality_synced ON quality_events(cloud_synced);
CREATE INDEX IF NOT EXISTS idx_confirmations_wo ON work_order_confirmations(work_order_id);
CREATE INDEX IF NOT EXISTS idx_confirmations_synced ON work_order_confirmations(cloud_synced);
CREATE INDEX IF NOT EXISTS idx_schedule_entity ON schedule_cache(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status);
"""


class EdgeLocalDB:
    """SQLite database manager for Edge Gateway local storage."""

    def __init__(self, db_path: str = "edge_gateway.db"):
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_schema(self) -> None:
        if not self.conn:
            self.connect()
        self.conn.executescript(EDGE_SCHEMA_SQL)
        self.conn.commit()

    def _ensure_conn(self) -> sqlite3.Connection:
        if not self.conn:
            self.connect()
        return self.conn

    def save_operation(self, operation: dict[str, Any]) -> str:
        conn = self._ensure_conn()
        op_id = operation.get("id")
        now = datetime.now(UTC).isoformat()

        conn.execute(
            """INSERT OR REPLACE INTO edge_operations
            (id, mo_id, work_order_id, work_center_id, operation_name,
             status, actual_qty, actual_duration_mins, scrap_qty, scrap_reason,
             operator_id, started_at, completed_at, local_timestamp,
             cloud_synced, cloud_version, conflict_status, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)""",
            (
                op_id,
                operation.get("mo_id"),
                operation.get("work_order_id"),
                operation.get("work_center_id"),
                operation.get("operation_name", ""),
                operation.get("status", "pending"),
                operation.get("actual_qty", 0),
                operation.get("actual_duration_mins", 0),
                operation.get("scrap_qty", 0),
                operation.get("scrap_reason"),
                operation.get("operator_id"),
                operation.get("started_at"),
                operation.get("completed_at"),
                now,
                operation.get("conflict_status"),
                operation.get("version", 1),
            ),
        )
        conn.commit()

        self._enqueue_sync("edge_operations", op_id, "update", operation, now)
        return op_id

    def save_quality_event(self, event: dict[str, Any]) -> str:
        conn = self._ensure_conn()
        event_id = event.get("id")
        now = datetime.now(UTC).isoformat()

        conn.execute(
            """INSERT OR REPLACE INTO quality_events
            (id, mo_id, work_order_id, work_center_id, product_id,
             event_type, severity, defect_category, defect_count,
             rework_required, rework_cycles, max_rework_cycles,
             scrap_quantity, cost_impact, status, operator_id,
             detected_at, local_timestamp, cloud_synced, cloud_version,
             conflict_status, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)""",
            (
                event_id,
                event.get("mo_id"),
                event.get("work_order_id"),
                event.get("work_center_id"),
                event.get("product_id"),
                event.get("event_type"),
                event.get("severity", "minor"),
                event.get("defect_category"),
                event.get("defect_count", 1),
                event.get("rework_required", 0),
                event.get("rework_cycles", 0),
                event.get("max_rework_cycles", 3),
                event.get("scrap_quantity", 0),
                event.get("cost_impact", 0.0),
                event.get("status", "open"),
                event.get("operator_id"),
                event.get("detected_at", now),
                now,
                event.get("conflict_status"),
                event.get("version", 1),
            ),
        )
        conn.commit()

        self._enqueue_sync("quality_events", event_id, "create", event, now)
        return event_id

    def save_confirmation(self, confirmation: dict[str, Any]) -> str:
        conn = self._ensure_conn()
        conf_id = confirmation.get("id")
        now = datetime.now(UTC).isoformat()

        conn.execute(
            """INSERT OR REPLACE INTO work_order_confirmations
            (id, work_order_id, mo_id, confirmation_type, quantity,
             duration_mins, scrap_qty, reject_qty, reason, operator_id,
             confirmed_at, local_timestamp, cloud_synced, cloud_version,
             conflict_status, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)""",
            (
                conf_id,
                confirmation.get("work_order_id"),
                confirmation.get("mo_id"),
                confirmation.get("confirmation_type"),
                confirmation.get("quantity", 0),
                confirmation.get("duration_mins", 0),
                confirmation.get("scrap_qty", 0),
                confirmation.get("reject_qty", 0),
                confirmation.get("reason"),
                confirmation.get("operator_id"),
                confirmation.get("confirmed_at", now),
                now,
                confirmation.get("conflict_status"),
                confirmation.get("version", 1),
            ),
        )
        conn.commit()

        self._enqueue_sync("work_order_confirmations", conf_id, "create", confirmation, now)
        return conf_id

    def save_schedule(self, entity_type: str, entity_id: str, payload: dict[str, Any], version: int = 1) -> None:
        conn = self._ensure_conn()
        now = datetime.now(UTC).isoformat()

        conn.execute(
            """INSERT OR REPLACE INTO schedule_cache
            (id, entity_type, entity_id, payload, version, fetched_at, expires_at, checksum)
            VALUES (?, ?, ?, ?, ?, ?, datetime(?, '+24 hours'), ?)""",
            (
                f"{entity_type}_{entity_id}",
                entity_type,
                entity_id,
                json.dumps(payload),
                version,
                now,
                now,
                self._compute_checksum(payload),
            ),
        )
        conn.commit()

    def get_pending_sync_records(self, limit: int = 100) -> list[dict[str, Any]]:
        conn = self._ensure_conn()
        cursor = conn.execute(
            """SELECT id, entity_type, entity_id, operation, payload,
                      local_timestamp, retry_count, status
               FROM sync_queue
               WHERE status = 'pending'
               ORDER BY local_timestamp ASC
               LIMIT ?""",
            (limit,),
        )
        records = []
        for row in cursor:
            records.append({
                "id": row["id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "operation": row["operation"],
                "payload": json.loads(row["payload"]),
                "local_timestamp": row["local_timestamp"],
                "retry_count": row["retry_count"],
                "status": row["status"],
            })
        return records

    def mark_synced(self, record_ids: list[int]) -> None:
        conn = self._ensure_conn()
        now = datetime.now(UTC).isoformat()
        for record_id in record_ids:
            conn.execute(
                "UPDATE sync_queue SET status = 'synced' WHERE id = ?",
                (record_id,),
            )
        conn.commit()

    def mark_failed(self, record_id: int, error: str) -> None:
        conn = self._ensure_conn()
        now = datetime.now(UTC).isoformat()
        conn.execute(
            """UPDATE sync_queue
               SET status = 'failed', retry_count = retry_count + 1,
                   last_retry_at = ?, error_message = ?
               WHERE id = ?""",
            (now, error, record_id),
        )
        conn.commit()

    def mark_entity_synced(self, entity_type: str, entity_id: str, cloud_version: int) -> None:
        conn = self._ensure_conn()
        table_map = {
            "edge_operations": "edge_operations",
            "quality_events": "quality_events",
            "work_order_confirmations": "work_order_confirmations",
        }
        table = table_map.get(entity_type)
        if table:
            conn.execute(
                f"UPDATE {table} SET cloud_synced = 1, cloud_version = ? WHERE id = ?",
                (cloud_version, entity_id),
            )
            conn.commit()

    def get_unsynced_count(self) -> dict[str, int]:
        conn = self._ensure_conn()
        counts = {}
        for table in ["edge_operations", "quality_events", "work_order_confirmations"]:
            cursor = conn.execute(
                f"SELECT COUNT(*) as cnt FROM {table} WHERE cloud_synced = 0"
            )
            counts[table] = cursor.fetchone()["cnt"]
        return counts

    def get_schedule(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        conn = self._ensure_conn()
        cursor = conn.execute(
            """SELECT payload, version, expires_at
               FROM schedule_cache
               WHERE entity_type = ? AND entity_id = ?
               AND expires_at > ?""",
            (entity_type, entity_id, datetime.now(UTC).isoformat()),
        )
        row = cursor.fetchone()
        if row:
            return {
                "payload": json.loads(row["payload"]),
                "version": row["version"],
            }
        return None

    def get_pending_pull_count(self) -> int:
        conn = self._ensure_conn()
        cursor = conn.execute(
            "SELECT COUNT(*) as cnt FROM sync_queue WHERE status = 'pending'"
        )
        return cursor.fetchone()["cnt"]

    def _enqueue_sync(self, entity_type: str, entity_id: str, operation: str,
                      payload: dict[str, Any], timestamp: str) -> None:
        conn = self._ensure_conn()
        conn.execute(
            """INSERT INTO sync_queue (entity_type, entity_id, operation, payload, local_timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (entity_type, entity_id, operation, json.dumps(payload), timestamp),
        )
        conn.commit()

    def _compute_checksum(self, payload: dict[str, Any]) -> str:
        import hashlib
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def get_sync_meta(self, key: str) -> str | None:
        conn = self._ensure_conn()
        cursor = conn.execute(
            "SELECT value FROM sync_meta WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return row["value"] if row else None

    def set_sync_meta(self, key: str, value: str) -> None:
        conn = self._ensure_conn()
        now = datetime.now(UTC).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO sync_meta (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now),
        )
        conn.commit()
