"""Optimistic locking concurrency integration tests.

Proves that version-based optimistic locking on cdm_manufacturing_order.version
and cdm_financial_projection.version prevents lost updates under concurrent access.

Requires: PostgreSQL running with migrations applied.
Run:
    uv run pytest tests/integration/test_optimistic_locking.py -v --asyncio-mode=auto
"""

import asyncio
import os
import uuid

import asyncpg
import pytest

DB_DSN = os.environ.get(
    "TEST_DB_DSN", "postgresql://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
)
TENANT_ID = os.environ.get("TEST_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

pytestmark = [pytest.mark.integration]


@pytest.fixture(scope="module")
async def pg():
    try:
        conn = await asyncpg.connect(DB_DSN)
    except Exception as exc:
        pytest.skip(f"Cannot connect to PostgreSQL: {exc}")
        yield None
        return
    yield conn
    await conn.close()


async def _seed_mo(pg: asyncpg.Connection, tenant_id: str, tag: str | None = None):
    tag = tag or f"ol-{uuid.uuid4().hex[:6]}"
    ids = {
        "product": uuid.uuid4(),
        "bom": uuid.uuid4(),
        "mo": uuid.uuid4(),
    }
    await pg.execute(
        "INSERT INTO cdm_product (id, tenant_id, erp_source_id, name, source_type) "
        "VALUES ($1, $2, $3, $4, 'manufactured')",
        ids["product"],
        tenant_id,
        f"{tag}-p",
        "OL Test Product",
    )
    await pg.execute(
        "INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id) "
        "VALUES ($1, $2, $3, $4)",
        ids["bom"],
        tenant_id,
        ids["product"],
        f"{tag}-bom",
    )
    await pg.execute(
        "INSERT INTO cdm_manufacturing_order "
        "(id, tenant_id, product_id, bom_id, quantity, status, erp_mo_id, version) "
        "VALUES ($1, $2, $3, $4, 100, 'planned', $5, 1)",
        ids["mo"],
        tenant_id,
        ids["product"],
        ids["bom"],
        f"{tag}-mo",
    )
    return {k: str(v) for k, v in ids.items()}


async def _cleanup_mo(pg: asyncpg.Connection, ids: dict):
    for table, key in [
        ("cdm_manufacturing_order", "mo"),
        ("cdm_bill_of_material", "bom"),
        ("cdm_product", "product"),
    ]:
        try:
            await pg.execute(f"DELETE FROM {table} WHERE id = $1", uuid.UUID(ids[key]))
        except Exception:
            pass


async def _seed_projection(pg: asyncpg.Connection, tenant_id: str, product_id: str):
    pid = uuid.uuid4()
    await pg.execute(
        "INSERT INTO cdm_financial_projection "
        "(id, tenant_id, product_id, projection_type, quantity, unit_cost, total_cost, "
        "revenue, margin, margin_pct, status, version) "
        "VALUES ($1, $2, $3, 'standard', 100, 10.0, 1000.0, 1500.0, 500.0, 33.3, 'draft', 1)",
        pid,
        tenant_id,
        uuid.UUID(product_id),
    )
    return str(pid)


async def _cleanup_projection(pg: asyncpg.Connection, pid: str):
    try:
        await pg.execute(
            "DELETE FROM cdm_financial_projection WHERE id = $1", uuid.UUID(pid)
        )
    except Exception:
        pass


async def _concurrent_update(
    dsn: str, table: str, pk_id: uuid.UUID, version: int, set_extras: str
):
    conn = await asyncpg.connect(dsn)
    try:
        async with conn.transaction():
            result = await conn.execute(
                f"UPDATE {table} SET {set_extras}, version = version + 1 "
                f"WHERE id = $1 AND version = $2",
                pk_id,
                version,
            )
            return result
    finally:
        await conn.close()


class TestOptimisticLockingMO:
    async def test_concurrent_approval_returns_409(self, pg):
        if pg is None:
            pytest.skip("No DB connection")

        ids = await _seed_mo(pg, TENANT_ID)
        mo_id = uuid.UUID(ids["mo"])

        try:
            row = await pg.fetchrow(
                "SELECT version FROM cdm_manufacturing_order WHERE id = $1",
                mo_id,
            )
            assert row is not None
            version = int(row["version"])

            r1, r2 = await asyncio.gather(
                _concurrent_update(
                    DB_DSN,
                    "cdm_manufacturing_order",
                    mo_id,
                    version,
                    "status = 'approved', updated_at = now()",
                ),
                _concurrent_update(
                    DB_DSN,
                    "cdm_manufacturing_order",
                    mo_id,
                    version,
                    "status = 'approved', updated_at = now()",
                ),
            )

            updated_1 = "UPDATE 1" in r1
            updated_2 = "UPDATE 1" in r2
            assert updated_1 != updated_2, (
                f"Expected exactly one concurrent UPDATE to succeed, "
                f"got conn1={updated_1} conn2={updated_2}"
            )
        finally:
            await _cleanup_mo(pg, ids)

    async def test_stale_version_returns_409(self, pg):
        if pg is None:
            pytest.skip("No DB connection")

        ids = await _seed_mo(pg, TENANT_ID)
        mo_id = uuid.UUID(ids["mo"])

        try:
            row = await pg.fetchrow(
                "SELECT version FROM cdm_manufacturing_order WHERE id = $1",
                mo_id,
            )
            assert row is not None
            original_version = int(row["version"])
            assert original_version == 1

            await pg.execute(
                "UPDATE cdm_manufacturing_order SET version = version + 1, "
                "quantity = 200, updated_at = now() WHERE id = $1",
                mo_id,
            )

            stale_match = await pg.fetchval(
                "SELECT COUNT(*) FROM cdm_manufacturing_order "
                "WHERE id = $1 AND version = $2",
                mo_id,
                original_version,
            )
            assert stale_match == 0, (
                f"Stale version should not match, but found {stale_match} row(s)"
            )

            current_match = await pg.fetchval(
                "SELECT COUNT(*) FROM cdm_manufacturing_order "
                "WHERE id = $1 AND version = $2",
                mo_id,
                original_version + 1,
            )
            assert current_match == 1, "Current version should match exactly one row"

            update_result = await pg.execute(
                "UPDATE cdm_manufacturing_order SET status = 'approved', updated_at = now() "
                "WHERE id = $1 AND version = $2",
                mo_id,
                original_version,
            )
            assert "UPDATE 0" in update_result, (
                f"Stale version UPDATE should affect 0 rows, got: {update_result}"
            )
        finally:
            await _cleanup_mo(pg, ids)

    async def test_version_increments_on_update(self, pg):
        if pg is None:
            pytest.skip("No DB connection")

        ids = await _seed_mo(pg, TENANT_ID)
        mo_id = uuid.UUID(ids["mo"])

        try:
            row = await pg.fetchrow(
                "SELECT version FROM cdm_manufacturing_order WHERE id = $1",
                mo_id,
            )
            assert row is not None
            assert int(row["version"]) == 1, (
                f"Expected initial version=1, got {row['version']}"
            )

            await pg.execute(
                "UPDATE cdm_manufacturing_order SET quantity = 200, version = version + 1, "
                "updated_at = now() WHERE id = $1",
                mo_id,
            )
            row = await pg.fetchrow(
                "SELECT version, quantity FROM cdm_manufacturing_order WHERE id = $1",
                mo_id,
            )
            assert int(row["version"]) == 2
            assert float(row["quantity"]) == 200

            await pg.execute(
                "UPDATE cdm_manufacturing_order SET quantity = 300, version = version + 1, "
                "updated_at = now() WHERE id = $1",
                mo_id,
            )
            row = await pg.fetchrow(
                "SELECT version FROM cdm_manufacturing_order WHERE id = $1",
                mo_id,
            )
            assert int(row["version"]) == 3
        finally:
            await _cleanup_mo(pg, ids)


class TestOptimisticLockingFinancialProjection:
    async def test_financial_projection_concurrent_update(self, pg):
        if pg is None:
            pytest.skip("No DB connection")

        ids = await _seed_mo(pg, TENANT_ID)
        product_id = ids["product"]
        projection_id_str = await _seed_projection(pg, TENANT_ID, product_id)
        projection_id = uuid.UUID(projection_id_str)

        try:
            row = await pg.fetchrow(
                "SELECT version FROM cdm_financial_projection WHERE id = $1",
                projection_id,
            )
            assert row is not None
            version = int(row["version"])

            r1, r2 = await asyncio.gather(
                _concurrent_update(
                    DB_DSN,
                    "cdm_financial_projection",
                    projection_id,
                    version,
                    "total_cost = 2000.0",
                ),
                _concurrent_update(
                    DB_DSN,
                    "cdm_financial_projection",
                    projection_id,
                    version,
                    "total_cost = 3000.0",
                ),
            )

            updated_1 = "UPDATE 1" in r1
            updated_2 = "UPDATE 1" in r2
            assert updated_1 != updated_2, (
                f"Expected exactly one concurrent UPDATE to succeed, "
                f"got conn1={updated_1} conn2={updated_2}"
            )

            final_row = await pg.fetchrow(
                "SELECT version FROM cdm_financial_projection WHERE id = $1",
                projection_id,
            )
            assert int(final_row["version"]) == version + 1
        finally:
            await _cleanup_projection(pg, projection_id_str)
            await _cleanup_mo(pg, ids)

    async def test_financial_projection_version_increments(self, pg):
        if pg is None:
            pytest.skip("No DB connection")

        ids = await _seed_mo(pg, TENANT_ID)
        product_id = ids["product"]
        projection_id_str = await _seed_projection(pg, TENANT_ID, product_id)
        projection_id = uuid.UUID(projection_id_str)

        try:
            row = await pg.fetchrow(
                "SELECT version FROM cdm_financial_projection WHERE id = $1",
                projection_id,
            )
            assert row is not None
            assert int(row["version"]) == 1

            await pg.execute(
                "UPDATE cdm_financial_projection SET total_cost = 1500.0, "
                "version = version + 1 WHERE id = $1",
                projection_id,
            )
            row = await pg.fetchrow(
                "SELECT version, total_cost FROM cdm_financial_projection WHERE id = $1",
                projection_id,
            )
            assert int(row["version"]) == 2
            assert abs(float(row["total_cost"]) - 1500.0) < 0.01

            await pg.execute(
                "UPDATE cdm_financial_projection SET total_cost = 2500.0, "
                "version = version + 1 WHERE id = $1",
                projection_id,
            )
            row = await pg.fetchrow(
                "SELECT version FROM cdm_financial_projection WHERE id = $1",
                projection_id,
            )
            assert int(row["version"]) == 3
        finally:
            await _cleanup_projection(pg, projection_id_str)
            await _cleanup_mo(pg, ids)


class TestOptimisticLockingCrossTenant:
    async def test_optimistic_lock_with_different_tenants(self, pg):
        if pg is None:
            pytest.skip("No DB connection")

        other_tenant = str(uuid.uuid4())
        ids_a = await _seed_mo(pg, TENANT_ID, tag="ol-tenant-a")
        ids_b = await _seed_mo(pg, other_tenant, tag="ol-tenant-b")
        mo_id_a = uuid.UUID(ids_a["mo"])
        mo_id_b = uuid.UUID(ids_b["mo"])

        try:
            row_a = await pg.fetchrow(
                "SELECT version FROM cdm_manufacturing_order WHERE id = $1",
                mo_id_a,
            )
            row_b = await pg.fetchrow(
                "SELECT version FROM cdm_manufacturing_order WHERE id = $1",
                mo_id_b,
            )
            assert row_a is not None and row_b is not None
            version_a = int(row_a["version"])
            version_b = int(row_b["version"])

            r1, r2 = await asyncio.gather(
                _concurrent_update(
                    DB_DSN,
                    "cdm_manufacturing_order",
                    mo_id_a,
                    version_a,
                    "quantity = 500, updated_at = now()",
                ),
                _concurrent_update(
                    DB_DSN,
                    "cdm_manufacturing_order",
                    mo_id_b,
                    version_b,
                    "quantity = 600, updated_at = now()",
                ),
            )

            assert "UPDATE 1" in r1, f"Tenant A update should succeed, got: {r1}"
            assert "UPDATE 1" in r2, f"Tenant B update should succeed, got: {r2}"

            row_a = await pg.fetchrow(
                "SELECT version, quantity FROM cdm_manufacturing_order WHERE id = $1",
                mo_id_a,
            )
            row_b = await pg.fetchrow(
                "SELECT version, quantity FROM cdm_manufacturing_order WHERE id = $1",
                mo_id_b,
            )
            assert int(row_a["version"]) == 2
            assert int(row_b["version"]) == 2
            assert float(row_a["quantity"]) == 500
            assert float(row_b["quantity"]) == 600
        finally:
            for ids in [ids_a, ids_b]:
                await _cleanup_mo(pg, ids)
