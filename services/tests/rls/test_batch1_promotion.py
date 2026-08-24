"""BATCH1-1 RLS enforcement for promoted cdm_ingest_* tables.

Requires live lab Postgres (IPE_DATABASE_URL_SYNC or localhost:5433/ipe_test).
Uses app.current_tenant_id (platform convention), not ipe.tenant_id.
Does not use BYPASSRLS.
"""

from __future__ import annotations

import os
import uuid

import pytest

try:
    import psycopg
except ImportError:
    psycopg = pytest.importorskip("psycopg2")

TENANT_A = uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TENANT_B = uuid.UUID("b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22")
TABLE = "cdm_ingest_product"
# Lab role `ipe` is SUPERUSER + BYPASSRLS; isolation must use a normal login.
RLS_APP = "ipe_rls_app"
RLS_PASS = "ipe_rls_app_pass"


def _dsn() -> str:
    return os.environ.get(
        "IPE_DATABASE_URL_SYNC",
        "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test",
    )


def _rls_dsn() -> str:
    from urllib.parse import urlparse, urlunparse

    p = urlparse(_dsn())
    netloc = f"{RLS_APP}:{RLS_PASS}@{p.hostname}"
    if p.port:
        netloc += f":{p.port}"
    return urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))


def _connect(dsn: str):
    conn = psycopg.connect(dsn)
    conn.autocommit = True
    return conn


def _conn():
    return _connect(_dsn())


def _set_tenant(cur, tenant: uuid.UUID | None) -> None:
    # Session-level (is_local=false): autocommit would drop SET LOCAL immediately.
    if tenant is None:
        cur.execute("SELECT set_config('app.current_tenant_id', '', false)")
        return
    cur.execute("SELECT set_config('app.current_tenant_id', %s, false)", (str(tenant),))


def _ensure_rls_app(cur) -> None:
    cur.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ipe_rls_app') THEN
            CREATE ROLE ipe_rls_app LOGIN PASSWORD 'ipe_rls_app_pass'
              NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOBYPASSRLS;
          END IF;
        END $$;
        """
    )
    cur.execute("GRANT USAGE ON SCHEMA public TO ipe_rls_app")
    cur.execute("GRANT CONNECT ON DATABASE ipe_test TO ipe_rls_app")
    cur.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO ipe_rls_app")
    cur.execute("GRANT SELECT ON cdm_tenant TO ipe_rls_app")


@pytest.fixture(scope="module")
def db():
    try:
        conn = _conn()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"lab DB unavailable: {exc}")
    cur = conn.cursor()
    cur.execute(
        "SELECT to_regclass('public.cdm_ingest_product') IS NOT NULL AND "
        "to_regclass('public.cdm_tenant') IS NOT NULL"
    )
    if not cur.fetchone()[0]:
        conn.close()
        pytest.skip("migration 083 not applied")
    cur.execute(
        """
        INSERT INTO cdm_tenant (id, name, erp_type)
        VALUES (%s, 'BATCH1-RLS-B', 'none')
        ON CONFLICT (id) DO NOTHING
        """,
        (str(TENANT_B),),
    )
    try:
        _ensure_rls_app(cur)
    except Exception as exc:  # noqa: BLE001
        conn.close()
        pytest.skip(f"cannot create ipe_rls_app: {exc}")
    yield conn
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {TABLE} WHERE product_id LIKE 'RLS-TEST-%'")
    conn.close()


@pytest.fixture(scope="module")
def rls_db(db):
    """Connection as NOSUPERUSER / NOBYPASSRLS so FORCE RLS is actually evaluated."""
    try:
        conn = _connect(_rls_dsn())
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ipe_rls_app login failed: {exc}")
    yield conn
    conn.close()


def test_1_tenant_a_cannot_select_tenant_b(rls_db):
    cur = rls_db.cursor()
    _set_tenant(cur, TENANT_A)
    cur.execute(
        f"INSERT INTO {TABLE} (tenant_id, product_id, name) VALUES (%s, %s, %s) "
        f"ON CONFLICT (tenant_id, product_id) DO UPDATE SET name = EXCLUDED.name",
        (str(TENANT_A), "RLS-TEST-A", "A"),
    )
    _set_tenant(cur, TENANT_B)
    cur.execute(
        f"INSERT INTO {TABLE} (tenant_id, product_id, name) VALUES (%s, %s, %s) "
        f"ON CONFLICT (tenant_id, product_id) DO UPDATE SET name = EXCLUDED.name",
        (str(TENANT_B), "RLS-TEST-B", "B"),
    )
    _set_tenant(cur, TENANT_A)
    cur.execute(f"SELECT product_id FROM {TABLE} WHERE product_id LIKE 'RLS-TEST-%'")
    rows = [r[0] for r in cur.fetchall()]
    assert "RLS-TEST-A" in rows
    assert "RLS-TEST-B" not in rows


def test_2_tenant_a_cannot_insert_as_tenant_b(rls_db):
    cur = rls_db.cursor()
    _set_tenant(cur, TENANT_A)
    with pytest.raises(Exception):
        cur.execute(
            f"INSERT INTO {TABLE} (tenant_id, product_id, name) VALUES (%s, %s, %s)",
            (str(TENANT_B), "RLS-TEST-SPOOF", "nope"),
        )


def test_3_tenant_a_cannot_update_tenant_b(rls_db):
    cur = rls_db.cursor()
    _set_tenant(cur, TENANT_B)
    cur.execute(
        f"INSERT INTO {TABLE} (tenant_id, product_id, name) VALUES (%s, %s, %s) "
        f"ON CONFLICT (tenant_id, product_id) DO UPDATE SET name = EXCLUDED.name",
        (str(TENANT_B), "RLS-TEST-B2", "orig"),
    )
    _set_tenant(cur, TENANT_A)
    cur.execute(f"UPDATE {TABLE} SET name = 'hacked' WHERE product_id = 'RLS-TEST-B2'")
    assert cur.rowcount == 0
    _set_tenant(cur, TENANT_B)
    cur.execute(f"SELECT name FROM {TABLE} WHERE product_id = 'RLS-TEST-B2'")
    assert cur.fetchone()[0] == "orig"


def test_4_tenant_a_cannot_delete_tenant_b(rls_db):
    cur = rls_db.cursor()
    _set_tenant(cur, TENANT_B)
    cur.execute(
        f"INSERT INTO {TABLE} (tenant_id, product_id, name) VALUES (%s, %s, %s) "
        f"ON CONFLICT (tenant_id, product_id) DO NOTHING",
        (str(TENANT_B), "RLS-TEST-B3", "keep"),
    )
    _set_tenant(cur, TENANT_A)
    cur.execute(f"DELETE FROM {TABLE} WHERE product_id = 'RLS-TEST-B3'")
    assert cur.rowcount == 0
    _set_tenant(cur, TENANT_B)
    cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE product_id = 'RLS-TEST-B3'")
    assert cur.fetchone()[0] == 1


def test_5_null_tenant_id_rejected(db):
    cur = db.cursor()
    _set_tenant(cur, TENANT_A)
    with pytest.raises(Exception):
        cur.execute(
            f"INSERT INTO {TABLE} (tenant_id, product_id, name) VALUES (NULL, %s, %s)",
            ("RLS-TEST-NULL", "x"),
        )


def test_6_cross_tenant_join_returns_zero(rls_db):
    cur = rls_db.cursor()
    _set_tenant(cur, TENANT_A)
    cur.execute(
        f"""
        SELECT COUNT(*) FROM {TABLE} a
        JOIN {TABLE} b ON a.product_id = b.product_id AND a.tenant_id <> b.tenant_id
        WHERE a.product_id LIKE 'RLS-TEST-%'
        """
    )
    assert cur.fetchone()[0] == 0


def test_7_unset_tenant_cannot_query(rls_db):
    cur = rls_db.cursor()
    _set_tenant(cur, TENANT_A)
    cur.execute(
        f"INSERT INTO {TABLE} (tenant_id, product_id, name) VALUES (%s, %s, %s) "
        f"ON CONFLICT (tenant_id, product_id) DO NOTHING",
        (str(TENANT_A), "RLS-TEST-A7", "hidden"),
    )
    _set_tenant(cur, None)
    cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE product_id = 'RLS-TEST-A7'")
    assert cur.fetchone()[0] == 0


NEW_084 = (
    "cdm_ingest_calendar_shift",
    "cdm_ingest_calendar_exception",
    "cdm_ingest_employee",
    "cdm_ingest_employee_skill",
    "cdm_ingest_sales_order_line",
    "cdm_ingest_purchase_order_line",
    "cdm_ingest_execution_event",
)


def test_8_084_tables_force_rls(db):
    cur = db.cursor()
    for table in NEW_084:
        cur.execute(
            "SELECT c.relrowsecurity, c.relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relname = %s",
            (table,),
        )
        row = cur.fetchone()
        assert row is not None, f"missing {table} (apply alembic 084)"
        assert row[0] is True and row[1] is True, f"RLS not forced on {table}"
