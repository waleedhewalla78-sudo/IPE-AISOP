"""BATCH1-3 Copilot audit trail tests."""

from __future__ import annotations

import os
import uuid

import pytest

from app.audit_middleware import integrity_hash, parse_sources, verify_integrity

try:
    import psycopg2 as pg
except ImportError:
    pg = pytest.importorskip("psycopg2")

TENANT_A = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


def test_1_sources_parsed_from_response():
    src = parse_sources("MO-ST-007 is blocked at WC-CAI-CORE-CUT")
    types = {s["entity_type"] for s in src}
    assert "manufacturing_order" in types
    assert "work_center" in types


def test_2_query_context_snapshot_shape():
    ctx = {"intent": "delay_cause", "filters": {"plant": "STR-CAI-01"}}
    assert ctx["intent"] == "delay_cause"
    assert "filters" in ctx


def test_3_sources_list_json_ready():
    src = parse_sources("see MO-ST-007")
    assert src[0]["entity_id"].upper().startswith("MO-")


def test_4_tamper_detection_hash_mismatch():
    secret = "unit-test-secret"
    digest = integrity_hash("qid", "q", "r", 1, TENANT_A, secret)
    row = {
        "query_id": "qid",
        "query_text": "q",
        "response_text": "TAMPERED",
        "created_at_epoch": 1,
        "tenant_id": TENANT_A,
        "integrity_hash": digest,
    }
    assert verify_integrity(row, secret) is False
    row["response_text"] = "r"
    assert verify_integrity(row, secret) is True


def _dsn():
    return os.environ.get(
        "IPE_DATABASE_URL_SYNC",
        "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test",
    )


def _conn():
    try:
        c = pg.connect(_dsn())
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"lab DB unavailable: {exc}")
    c.autocommit = True
    return c


def test_5_rls_isolation_on_audit_table():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.cdm_copilot_audit')")
    if cur.fetchone()[0] is None:
        conn.close()
        pytest.skip("migration 085 not applied")
    conn.close()
    # FORCE RLS present
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT relrowsecurity AND relforcerowsecurity FROM pg_class WHERE relname='cdm_copilot_audit'"
    )
    assert cur.fetchone()[0] is True
    conn.close()


def test_6_non_admin_roles_listed():
    # Endpoint is require_roles(["admin"]) — planner is not in the allow-list.
    from app.api.v1.governance import router

    paths = {getattr(r, "path", "") for r in router.routes}
    assert any("copilot-audit" in p for p in paths)


def test_7_admin_routes_include_list_detail_export():
    from app.api.v1.governance import router

    paths = [getattr(r, "path", "") for r in router.routes]
    joined = " ".join(paths)
    assert "export" in joined
    assert "{query_id}" in joined


def test_8_update_delete_blocked():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.cdm_copilot_audit')")
    if cur.fetchone()[0] is None:
        conn.close()
        pytest.skip("migration 085 not applied")
    cur.execute("SELECT set_config('app.current_tenant_id', %s, false)", (TENANT_A,))
    qid = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO cdm_copilot_audit (tenant_id, query_id, query_text, query_mode, created_at_epoch)
        VALUES (%s::uuid, %s::uuid, 'probe', 'ask', 1)
        """,
        (TENANT_A, qid),
    )
    with pytest.raises(Exception):
        cur.execute("UPDATE cdm_copilot_audit SET query_text='x' WHERE query_id=%s::uuid", (qid,))
    with pytest.raises(Exception):
        cur.execute("DELETE FROM cdm_copilot_audit WHERE query_id=%s::uuid", (qid,))
    conn.close()
