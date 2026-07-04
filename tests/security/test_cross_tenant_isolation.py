"""
Cross-tenant data isolation test.

Verifies that tenant A cannot access tenant B's data through PostgreSQL RLS
and Release 1 API endpoints (res-svc resolution).
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

_SECURITY_DIR = Path(__file__).resolve().parent
if str(_SECURITY_DIR) not in sys.path:
    sys.path.insert(0, str(_SECURITY_DIR))

from helpers import (
    ASYNC_DB_URL,
    TENANT_A,
    TENANT_B,
    ensure_tenants,
    seed_tenant_b_catalog,
    set_tenant,
)

pytestmark = [pytest.mark.integration, pytest.mark.security]


class TestCrossTenantIsolation:
    """Each test creates data in tenant B, then queries as tenant A — must return empty."""

    async def test_bom_isolation(self, db_conn, auth_headers_a, auth_headers_b):
        cur = db_conn.cursor()
        ids = seed_tenant_b_catalog(cur)
        bom_id = ids["bom_id"]

        set_tenant(cur, TENANT_A)
        cur.execute("SELECT id FROM cdm_bill_of_material WHERE id = %s", (bom_id,))
        assert cur.fetchone() is None

        cur.execute("SELECT id FROM cdm_bill_of_material")
        visible = {str(row[0]) for row in cur.fetchall()}
        assert bom_id not in visible

    async def test_routing_isolation(self, db_conn, auth_headers_a, auth_headers_b):
        cur = db_conn.cursor()
        ids = seed_tenant_b_catalog(cur)
        routing_id = ids["routing_id"]

        set_tenant(cur, TENANT_A)
        cur.execute("SELECT id FROM cdm_routing_operation WHERE id = %s", (routing_id,))
        assert cur.fetchone() is None

    async def test_inventory_isolation(self, db_conn, auth_headers_a, auth_headers_b):
        cur = db_conn.cursor()
        ids = seed_tenant_b_catalog(cur)
        product_id = ids["product_id"]

        set_tenant(cur, TENANT_A)
        cur.execute(
            "SELECT id FROM cdm_inventory_position WHERE product_id = %s",
            (product_id,),
        )
        assert cur.fetchall() == []

    async def test_mo_isolation(
        self,
        res_client: AsyncClient,
        db_conn,
        auth_headers_a,
        auth_headers_b,
    ):
        cur = db_conn.cursor()
        ids = seed_tenant_b_catalog(cur)
        mo_id = ids["mo_id"]
        db_conn.commit()

        set_tenant(cur, TENANT_A)
        cur.execute("SELECT id FROM cdm_manufacturing_order WHERE id = %s", (mo_id,))
        assert cur.fetchone() is None

        resp = await res_client.post(
            "/api/v1/resolution/scenarios",
            json={"mo_id": mo_id},
            headers=auth_headers_a,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"

    async def test_audit_log_tenant_scoping(self, db_conn, auth_headers_a):
        cur = db_conn.cursor()
        ensure_tenants(cur)
        entity_a = str(uuid.uuid4())
        entity_b = str(uuid.uuid4())

        set_tenant(cur, TENANT_A)
        cur.execute(
            """
            INSERT INTO cdm_audit_log
                (tenant_id, actor_type, actor_id, action, entity_type, entity_id)
            VALUES (%s, 'user', 'user-a', 'create', 'bom', %s)
            """,
            (TENANT_A, entity_a),
        )
        set_tenant(cur, TENANT_B)
        cur.execute(
            """
            INSERT INTO cdm_audit_log
                (tenant_id, actor_type, actor_id, action, entity_type, entity_id)
            VALUES (%s, 'user', 'user-b', 'create', 'bom', %s)
            """,
            (TENANT_B, entity_b),
        )
        db_conn.commit()

        set_tenant(cur, TENANT_A)
        cur.execute(
            """
            SELECT tenant_id::text FROM cdm_audit_log
            WHERE entity_id IN (%s, %s)
            """,
            (entity_a, entity_b),
        )
        rows = cur.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == TENANT_A

        from ipe_shared.audit.export import fetch_audit_rows
        from ipe_shared.database.connection import close_database, init_database
        from ipe_shared.database.session import get_session
        from ipe_shared.middleware.tenant_context import tenant_ctx

        await init_database(ASYNC_DB_URL)
        try:
            async for session in get_session():
                token = tenant_ctx.set(TENANT_A)
                try:
                    audit_rows = await fetch_audit_rows(session, TENANT_A, limit=100)
                finally:
                    tenant_ctx.reset(token)
                break
            for entry in audit_rows:
                assert str(entry["tenant_id"]) == TENANT_A
        finally:
            await close_database()

    async def test_jwt_tenant_overrides_spoofed_header(
        self,
        res_client: AsyncClient,
        db_conn,
        auth_headers_a,
    ):
        """JWT tenant A cannot read tenant B MO even if X-Tenant-ID is spoofed to B."""
        cur = db_conn.cursor()
        ids = seed_tenant_b_catalog(cur)
        mo_id = ids["mo_id"]
        db_conn.commit()

        spoofed = dict(auth_headers_a)
        spoofed["X-Tenant-ID"] = TENANT_B

        resp = await res_client.post(
            "/api/v1/resolution/scenarios",
            json={"mo_id": mo_id},
            headers=spoofed,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"
