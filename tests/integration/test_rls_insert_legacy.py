"""RLS INSERT policy verification for legacy tenant-scoped tables (migration 035)."""

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


@pytest.fixture
def conn():
    connection = _connect()
    connection.autocommit = False
    yield connection
    connection.rollback()
    connection.close()


def test_plant_insert_allowed_for_matching_tenant(conn):
    cur = conn.cursor()
    _set_tenant(cur, DEMO_TENANT)
    pid = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO cdm_plant (id, tenant_id, name, code, latitude, longitude, capacity_hours_per_day, is_active)
        VALUES (%s, %s, 'RLS Test Plant', %s, 1.0, 2.0, 8.0, true)
        """,
        (pid, DEMO_TENANT, f"RLS-{pid[:8]}"),
    )
    cur.execute("SELECT tenant_id FROM cdm_plant WHERE id = %s", (pid,))
    row = cur.fetchone()
    assert row is not None
    assert str(row[0]) == DEMO_TENANT


def test_plant_insert_rejected_for_cross_tenant(conn):
    cur = conn.cursor()
    _set_tenant(cur, DEMO_TENANT)
    pid = str(uuid.uuid4())
    with pytest.raises(psycopg2.Error):
        cur.execute(
            """
            INSERT INTO cdm_plant (id, tenant_id, name, code, latitude, longitude, capacity_hours_per_day, is_active)
            VALUES (%s, %s, 'RLS Cross Tenant', %s, 1.0, 2.0, 8.0, true)
            """,
            (pid, OTHER_TENANT, f"RLS-X-{pid[:8]}"),
        )


def test_delay_event_insert_matching_tenant(conn):
    cur = conn.cursor()
    _set_tenant(cur, DEMO_TENANT)
    cur.execute(
        "SELECT id FROM cdm_manufacturing_order WHERE tenant_id = %s LIMIT 1",
        (DEMO_TENANT,),
    )
    mo = cur.fetchone()
    if not mo:
        pytest.skip("No demo manufacturing order for delay_event test")
    eid = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO cdm_delay_event (id, tenant_id, mo_id, cause_category, delay_minutes)
        VALUES (%s, %s, %s, 'material_shortage', 15)
        """,
        (eid, DEMO_TENANT, str(mo[0])),
    )
    cur.execute("SELECT tenant_id FROM cdm_delay_event WHERE id = %s", (eid,))
    assert str(cur.fetchone()[0]) == DEMO_TENANT


def test_delay_event_cross_tenant_insert_rejected(conn):
    cur = conn.cursor()
    _set_tenant(cur, DEMO_TENANT)
    cur.execute(
        "SELECT id FROM cdm_manufacturing_order WHERE tenant_id = %s LIMIT 1",
        (DEMO_TENANT,),
    )
    mo = cur.fetchone()
    if not mo:
        pytest.skip("No demo manufacturing order for delay_event test")
    eid = str(uuid.uuid4())
    with pytest.raises(psycopg2.Error):
        cur.execute(
            """
            INSERT INTO cdm_delay_event (id, tenant_id, mo_id, cause_category, delay_minutes)
            VALUES (%s, %s, %s, 'material_shortage', 15)
            """,
            (eid, OTHER_TENANT, str(mo[0])),
        )
