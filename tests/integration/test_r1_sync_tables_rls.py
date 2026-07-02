"""RLS verification for Release 1 sync tables (migration 036)."""

from __future__ import annotations

import os
import uuid

import psycopg2
import pytest

pytestmark = [pytest.mark.integration]

DB_HOST = os.environ.get("TEST_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("TEST_DB_PORT", "5433"))
DB_USER = os.environ.get("TEST_DB_USER", "ipe_app")
DB_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "ipe_app_pass")
DB_NAME = os.environ.get("TEST_DB_NAME", "ipe_test")

DEMO_TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
OTHER_TENANT = "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380b22"


def _connect():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            connect_timeout=5,
        )
    except psycopg2.OperationalError as exc:
        pytest.skip(f"Database not available: {exc}")


def _set_tenant(cur, tenant_id: str) -> None:
    cur.execute("SET LOCAL app.current_tenant_id = %s", (tenant_id,))


def _migration_036_applied(cur) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'cdm_sync_run'
        """
    )
    return cur.fetchone() is not None


@pytest.fixture
def conn():
    connection = _connect()
    connection.autocommit = False
    cur = connection.cursor()
    if not _migration_036_applied(cur):
        pytest.skip("Migration 036 not applied — run alembic upgrade head")
    yield connection
    connection.rollback()
    connection.close()


def test_sync_run_insert_allowed_for_matching_tenant(conn):
    cur = conn.cursor()
    _set_tenant(cur, DEMO_TENANT)
    run_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO cdm_sync_run (id, tenant_id, status, entity_counts)
        VALUES (%s, %s, 'success', '{"mos": {"synced": 1}}'::jsonb)
        """,
        (run_id, DEMO_TENANT),
    )
    cur.execute("SELECT tenant_id FROM cdm_sync_run WHERE id = %s", (run_id,))
    row = cur.fetchone()
    assert row is not None
    assert str(row[0]) == DEMO_TENANT


def test_sync_run_insert_rejected_for_cross_tenant(conn):
    cur = conn.cursor()
    _set_tenant(cur, DEMO_TENANT)
    run_id = str(uuid.uuid4())
    with pytest.raises(psycopg2.Error):
        cur.execute(
            """
            INSERT INTO cdm_sync_run (id, tenant_id, status)
            VALUES (%s, %s, 'running')
            """,
            (run_id, OTHER_TENANT),
        )


def test_mo_erp_sync_columns_exist(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'cdm_manufacturing_order'
          AND column_name IN ('erp_last_update', 'erp_synced_at', 'sync_conflict')
        ORDER BY column_name
        """
    )
    cols = [row[0] for row in cur.fetchall()]
    assert cols == ["erp_last_update", "erp_synced_at", "sync_conflict"]
