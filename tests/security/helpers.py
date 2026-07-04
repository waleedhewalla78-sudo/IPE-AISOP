"""Shared helpers for cross-tenant security tests."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import psycopg2
import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_ROOT = ROOT / "services" / "shared"
if str(SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(SHARED_ROOT))

TENANT_A = "aaaaaaaa-1111-4111-8111-111111111111"
TENANT_B = "bbbbbbbb-2222-4222-8222-222222222222"

DB_HOST = os.environ.get("TEST_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("TEST_DB_PORT", "5433"))
DB_USER = os.environ.get("TEST_DB_USER", "ipe_app")
DB_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "ipe_app_pass")
DB_NAME = os.environ.get("TEST_DB_NAME", "ipe_test")
ASYNC_DB_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def connect_db():
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


def set_tenant(cur, tenant_id: str) -> None:
    cur.execute("SET LOCAL app.current_tenant_id = %s", (tenant_id,))


def ensure_tenants(cur, tenant_a: str = TENANT_A, tenant_b: str = TENANT_B) -> None:
    for tid, name in ((tenant_a, "Isolation Tenant A"), (tenant_b, "Isolation Tenant B")):
        cur.execute(
            """
            INSERT INTO cdm_tenant (id, name, erp_type)
            VALUES (%s, %s, 'odoo')
            ON CONFLICT (id) DO NOTHING
            """,
            (tid, name),
        )


def seed_tenant_b_catalog(cur) -> dict[str, str]:
    ensure_tenants(cur)
    set_tenant(cur, TENANT_B)
    product_id = str(uuid.uuid4())
    bom_id = str(uuid.uuid4())
    wc_id = str(uuid.uuid4())
    routing_id = str(uuid.uuid4())
    inventory_id = str(uuid.uuid4())
    mo_id = str(uuid.uuid4())

    suffix = uuid.uuid4().hex[:8]
    product_erp = f"PROD-TEST-{suffix}"
    wc_erp = f"WC-TEST-{suffix}"
    mo_erp = f"MO-TENANT-B-{suffix}"

    cur.execute(
        """
        INSERT INTO cdm_product (id, tenant_id, erp_source_id, name, source_type)
        VALUES (%s, %s, %s, 'Tenant B Product', 'manufactured')
        """,
        (product_id, TENANT_B, product_erp),
    )
    cur.execute(
        """
        INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, is_active)
        VALUES (%s, %s, %s, true)
        """,
        (bom_id, TENANT_B, product_id),
    )
    cur.execute(
        """
        INSERT INTO cdm_work_center (id, tenant_id, erp_source_id, name, capacity_hours_per_day)
        VALUES (%s, %s, %s, 'Tenant B WC', 8.0)
        """,
        (wc_id, TENANT_B, wc_erp),
    )
    cur.execute(
        """
        INSERT INTO cdm_routing_operation
            (id, tenant_id, bom_id, sequence, work_center_id, duration_planned_mins)
        VALUES (%s, %s, %s, 10, %s, 60.0)
        """,
        (routing_id, TENANT_B, bom_id, wc_id),
    )
    cur.execute(
        """
        INSERT INTO cdm_inventory_position (id, tenant_id, product_id, qty_on_hand)
        VALUES (%s, %s, %s, 100)
        """,
        (inventory_id, TENANT_B, product_id),
    )
    cur.execute(
        """
        INSERT INTO cdm_manufacturing_order
            (id, tenant_id, product_id, bom_id, quantity, status, erp_mo_id)
        VALUES (%s, %s, %s, %s, 50, 'planned', %s)
        """,
        (mo_id, TENANT_B, product_id, bom_id, mo_erp),
    )
    return {
        "product_id": product_id,
        "bom_id": bom_id,
        "routing_id": routing_id,
        "inventory_id": inventory_id,
        "mo_id": mo_id,
    }
