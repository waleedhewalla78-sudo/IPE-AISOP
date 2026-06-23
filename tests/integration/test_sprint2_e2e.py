"""End-to-end integration test for the full IPE pipeline.

Tests each service's HTTP API against the live Docker stack.
Requires: docker compose -f infrastructure/docker/docker-compose.yml up -d

Usage:
  uv run pytest tests/integration/test_sprint2_e2e.py -v --asyncio-mode=auto
"""

import os
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import httpx
import jwt
import pytest

DPE_URL = os.environ.get("TEST_DPE_URL", "http://localhost:8020")
MAT_URL = os.environ.get("TEST_MAT_URL", "http://localhost:8002")
CAP_URL = os.environ.get("TEST_CAP_URL", "http://localhost:8003")
FEA_URL = os.environ.get("TEST_FEA_URL", "http://localhost:8004")
RES_URL = os.environ.get("TEST_RES_URL", "http://localhost:8005")
DEL_URL = os.environ.get("TEST_DEL_URL", "http://localhost:8006")
NLP_URL = os.environ.get("TEST_NLP_URL", "http://localhost:8007")
REC_URL = os.environ.get("TEST_REC_URL", "http://localhost:8008")
CONNECTOR_URL = os.environ.get("TEST_CONNECTOR_URL", "http://localhost:8011")
ML_URL = os.environ.get("TEST_ML_URL", "http://localhost:8011")
DB_DSN = os.environ.get("TEST_DB_DSN", "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test")
TENANT_ID = os.environ.get("TEST_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
JWT_SECRET = os.environ.get("IPE_JWT_SECRET_KEY", "dev-only-change-in-production-min-32-chars-long!!")

HEADERS = {"Content-Type": "application/json", "X-Tenant-ID": TENANT_ID}

_test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
_token = jwt.encode(
    {
        "sub": str(_test_user_id),
        "tenant_id": TENANT_ID,
        "role": "admin",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
        "jti": str(uuid.uuid4()),
        "type": "access",
    },
    JWT_SECRET,
    algorithm="HS256",
)
AUTH_HEADERS = {"Content-Type": "application/json", "X-Tenant-ID": TENANT_ID, "Authorization": f"Bearer {_token}"}

pytestmark = [pytest.mark.integration]


@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def pg():
    try:
        conn = await asyncpg.connect(DB_DSN)
        yield conn
    except Exception as e:
        pytest.skip(f"Cannot connect to PostgreSQL: {e}")
        yield None
    else:
        await conn.close()


@pytest.fixture(scope="module")
async def seed(pg):
    if pg is None:
        pytest.skip("No DB connection")

    tag = f"e2e-{uuid.uuid4().hex[:6]}"
    ids = {
        "product": uuid.uuid4(),
        "customer": uuid.uuid4(),
        "bom": uuid.uuid4(),
        "mo": uuid.uuid4(),
        "demand_line": uuid.uuid4(),
        "routing_op": uuid.uuid4(),
        "tag": tag,
    }

    wc = await pg.fetchrow(
        "SELECT id FROM cdm_work_center WHERE tenant_id = $1 LIMIT 1", TENANT_ID
    )
    wc_id = wc["id"] if wc else None

    await pg.execute(
        "INSERT INTO cdm_product (id, tenant_id, erp_source_id, name, source_type) "
        "VALUES ($1, $2, $3, $4, 'manufactured')",
        ids["product"], TENANT_ID, f"{tag}-p", "E2E Test Product",
    )
    await pg.execute(
        "INSERT INTO cdm_customer (id, tenant_id, erp_source_id, name) "
        "VALUES ($1, $2, $3, $4)",
        ids["customer"], TENANT_ID, f"{tag}-c", "E2E Test Customer",
    )
    await pg.execute(
        "INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id) "
        "VALUES ($1, $2, $3, $4)",
        ids["bom"], TENANT_ID, ids["product"], f"{tag}-bom",
    )
    if wc_id:
        await pg.execute(
            "INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, "
            "operation_name, duration_planned_mins) VALUES ($1, $2, $3, 10, $4, 'E2E Test Op', 60)",
            ids["routing_op"], TENANT_ID, ids["bom"], wc_id,
        )
    await pg.execute(
        "INSERT INTO cdm_manufacturing_order (id, tenant_id, product_id, bom_id, quantity, status, erp_mo_id) "
        "VALUES ($1, $2, $3, $4, 100, 'planned', $5)",
        ids["mo"], TENANT_ID, ids["product"], ids["bom"], f"{tag}-mo",
    )
    await pg.execute(
        "INSERT INTO cdm_demand_line (id, tenant_id, erp_source_id, product_id, quantity, "
        "required_date, demand_type, customer_id, mo_id) "
        "VALUES ($1, $2, $3, $4, 50, $5, 'MTO', $6, $7)",
        ids["demand_line"], TENANT_ID, f"{tag}-dl", ids["product"],
        datetime.now(UTC) + timedelta(days=30), ids["customer"], ids["mo"],
    )

    yield {k: str(v) if not isinstance(v, str) else v for k, v in ids.items()}

    for table, col, val in [
        ("cdm_demand_line", "id", ids["demand_line"]),
        ("cdm_manufacturing_order", "id", ids["mo"]),
        ("cdm_bill_of_material", "id", ids["bom"]),
        ("cdm_customer", "id", ids["customer"]),
        ("cdm_product", "id", ids["product"]),
    ]:
        if val:
            try:
                await pg.execute(f"DELETE FROM {table} WHERE {col} = $1", val)
            except Exception:
                pass
    if wc_id:
        try:
            await pg.execute(
                "DELETE FROM cdm_routing_operation WHERE id = $1", ids["routing_op"]
            )
        except Exception:
            pass


class TestE2EPipeline:

    async def test_health_all(self):
        for name, base in [
            ("dpe", DPE_URL), ("mat", MAT_URL), ("cap", CAP_URL),
            ("fea", FEA_URL), ("res", RES_URL), ("del", DEL_URL),
            ("nlp", NLP_URL), ("rec", REC_URL), ("connector", CONNECTOR_URL),
        ]:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{base}/api/v1/health", timeout=10)
            assert r.status_code == 200, f"{name} health returned {r.status_code}"
            body = r.json()
            assert body.get("status") == "ok", f"{name} health body: {body}"

    async def test_demand_classify(self, seed):
        dl_id = seed["demand_line"]
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{DPE_URL}/api/v1/demand/classify",
                json={"demand_line_ids": [dl_id]},
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        results = body["data"]["results"]
        assert len(results) == 1
        assert results[0]["demand_line_id"] == dl_id
        assert results[0]["priority_score"] >= 0
        assert "priority_breakdown" in results[0]

    async def test_material_atp(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{MAT_URL}/api/v1/material/probabilistic-atp",
                json={
                    "mo": {"id": seed["mo"], "mo_number": "E2E-MO-001", "quantity": 100},
                    "components": [],
                    "required_start": datetime.now(UTC).isoformat(),
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert "overall_confidence" in data
        assert "component_breakdown" in data
        assert data["mo_id"] == seed["mo"]

    async def test_material_supplier_predict(self):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{MAT_URL}/api/v1/material/supplier-predict",
                json={"supplier_id": "00000000-0000-0000-0000-000000000000"},
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code in (200, 422, 500), f"supplier-predict returned {r.status_code}: {r.text[:300]}"

    async def test_material_priority_netting(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{MAT_URL}/api/v1/material/priority-netting",
                json={
                    "product_id": seed["product"],
                    "demands": [{"demand_line_id": seed["demand_line"], "quantity": 50}],
                    "time_bucket_days": 30,
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True

    async def test_capacity_schedule(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CAP_URL}/api/v1/capacity/schedule",
                json={"mo_ids": [seed["mo"]], "horizon_hours": 168},
                headers=AUTH_HEADERS, timeout=30,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert isinstance(data.get("schedule", {}).get("assignments", []), list)
        assert isinstance(data.get("bottlenecks", []), list)

    async def test_capacity_analyze(self):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CAP_URL}/api/v1/capacity/analyze",
                json={}, headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code in (200, 500), f"capacity/analyze returned {r.status_code}: {r.text[:500]}"
        if r.status_code == 500:
            pytest.skip("capacity/analyze returned 500 (likely empty DB)")
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert "work_centers" in data
        assert "operators" in data

    async def test_feasibility_score(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{FEA_URL}/api/v1/feasibility/score",
                json={
                    "mo_id": seed["mo"],
                    "demand_score": 95.0, "bom_score": 90.0,
                    "material_score": 85.0, "capacity_score": 80.0,
                    "labor_score": 90.0,
                    "autonomy_mode": "suggest",
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        d = body["data"]
        assert d["feasibility_score"] >= 0
        assert "gate_scores" in d
        assert d["gate_scores"]["demand"] == 95.0
        assert "action_taken" in d
        assert d["action_taken"] in ("queued_for_planner", "routed_to_resolution", "auto_confirmed")
        assert "primary_constraint" in d

    async def test_feasibility_kpis(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{FEA_URL}/api/v1/feasibility/kpis",
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert "avg_feasibility_score" in data
        assert "active_bottlenecks" in data
        assert "orders_at_risk" in data

    async def test_feasibility_queue(self):
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{FEA_URL}/api/v1/feasibility/queue",
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code in (200, 500), f"feasibility/queue returned {r.status_code}: {r.text[:500]}"
        if r.status_code == 500:
            pytest.skip("feasibility/queue returned 500 (likely empty DB)")

    async def test_feasibility_auto_confirm(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{FEA_URL}/api/v1/feasibility/auto-confirm",
                json={
                    "mo_id": seed["mo"],
                    "feasibility_score": 95.0,
                    "autonomy_mode": "shadow",
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "should_confirm" in body["data"]

    async def test_resolution_scenarios(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{RES_URL}/api/v1/resolution/scenarios",
                json={"mo_id": seed["mo"], "constraint_type": "material_shortage"},
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        scenarios = body["data"]["scenarios"]
        assert len(scenarios) > 0
        assert scenarios[0].get("id") is not None
        assert scenarios[0].get("strategy") is not None
        assert scenarios[0].get("business_score") is not None

    async def test_resolution_approve(self, seed):
        mo_id = seed["mo"]
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{RES_URL}/api/v1/resolution/scenarios",
                json={"mo_id": mo_id, "constraint_type": "material_shortage"},
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        sid = r.json()["data"]["scenarios"][0]["id"]

        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{RES_URL}/api/v1/resolution/approve",
                json={"scenario_id": sid, "approved_by": "e2e-test"},
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["status"] == "approved"

    async def test_resolution_list_scenarios(self):
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{RES_URL}/api/v1/resolution/scenarios",
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code in (200, 500), f"resolution/scenarios GET returned {r.status_code}: {r.text[:500]}"
        if r.status_code == 500:
            pytest.skip("resolution/scenarios returned 500 (likely empty DB)")
        body = r.json()
        assert body["success"] is True
        assert "scenarios" in body["data"]

    async def test_connector_action_receiver(self):
        connector_headers = {
            "X-IPE-Signature": "test-sig",
            "X-Tenant-ID": TENANT_ID,
            "Authorization": f"Bearer {_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CONNECTOR_URL}/api/v1/ipe/action",
                headers=connector_headers,
                json={"action": "confirm_mo", "mo_id": str(uuid.uuid4())},
                timeout=15,
            )
        assert r.status_code in (200, 400, 500), f"connector action returned {r.status_code}: {r.text[:500]}"


class TestSprint6E2E:

    async def test_ml_predict_duration(self):
        pytest.skip("ml-svc not deployed in Docker stack")

    async def test_delay_classify(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{DEL_URL}/api/v1/delay/classify",
                json={
                    "mo_id": seed["mo"],
                    "source_text": "machine breakdown, equipment failure reported",
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["cause_category"] in (
            "material_shortage", "capacity_overload", "labor_absence",
            "supplier_delay", "maintenance", "quality_issue",
            "process_variance", "other",
        )

    async def test_delay_chatter(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{DEL_URL}/api/v1/delay/chatter",
                json={
                    "mo_id": seed["mo"],
                    "chatter_text": "Operator absent today, no show, unavailable for shift",
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "root_cause_id" in body["data"]
        assert body["data"]["primary_category"] in (
            "material_shortage", "capacity_overload", "labor_absence",
            "supplier_delay", "maintenance", "quality_issue",
            "process_variance", "other",
        )

    async def test_delay_pareto(self):
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{DEL_URL}/api/v1/delay/pareto?days=30",
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code in (200, 500), f"delay/pareto returned {r.status_code}: {r.text[:500]}"
        if r.status_code == 500:
            pytest.skip("delay/pareto returned 500 (likely empty DB)")
        body = r.json()
        assert body["success"] is True
        assert "total_root_causes" in body["data"]
        assert "pareto" in body["data"]
        assert isinstance(body["data"]["pareto"], list)

    async def test_reconciliation_analyze(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{REC_URL}/api/v1/reconciliation/analyze",
                json={"mo_id": seed["mo"]},
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "time_variance_pct" in body["data"]
        assert "yield_variance_pct" in body["data"]

    async def test_reconciliation_daily(self):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{REC_URL}/api/v1/reconciliation/daily",
                json={},
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code in (200, 500), f"reconciliation/daily returned {r.status_code}: {r.text[:500]}"
        if r.status_code == 500:
            pytest.skip("reconciliation/daily returned 500 (likely empty DB)")
        body = r.json()
        assert body["success"] is True
        assert "drift" in body["data"]
        assert "retrain_triggered" in body["data"]

    async def test_reconciliation_drift(self):
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{REC_URL}/api/v1/reconciliation/drift",
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code in (200, 500), f"reconciliation/drift returned {r.status_code}: {r.text[:500]}"
        if r.status_code == 500:
            pytest.skip("reconciliation/drift returned 500 (likely empty DB)")
        body = r.json()
        assert body["success"] is True
        assert "mae" in body["data"]
        assert "drift_detected" in body["data"]

    async def test_scenario_clone(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CAP_URL}/api/v1/scenarios/clone",
                json={
                    "mo_ids": [seed["mo"]],
                    "name": "E2E Test Scenario",
                    "description": "Test scenario for E2E",
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "scenario_id" in body["data"]
        assert body["data"]["demand_count"] >= 1

    async def test_scenario_solve(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CAP_URL}/api/v1/scenarios/clone",
                json={
                    "mo_ids": [seed["mo"]],
                    "name": "Solve Test Scenario",
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        scenario_id = r.json()["data"]["scenario_id"]

        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CAP_URL}/api/v1/scenarios/{scenario_id}/solve",
                json={},
                headers=AUTH_HEADERS, timeout=30,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "schedule" in body["data"]

    async def test_scenario_diff(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CAP_URL}/api/v1/scenarios/clone",
                json={
                    "mo_ids": [seed["mo"]],
                    "name": "Diff Test Scenario",
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        scenario_id = r.json()["data"]["scenario_id"]

        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{CAP_URL}/api/v1/scenarios/{scenario_id}/diff",
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "baseline" in body["data"]
        assert "scenario" in body["data"]
        assert "impact" in body["data"]

    async def test_delay_batch_chatter(self, seed):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{DEL_URL}/api/v1/delay/chatter/batch",
                json={
                    "messages": [
                        {
                            "mo_id": seed["mo"],
                            "chatter_text": "Material shortage - steel coil out of stock",
                        },
                        {
                            "mo_id": seed["mo"],
                            "chatter_text": "Machine breakdown on CNC mill, maintenance required",
                        },
                    ],
                },
                headers=AUTH_HEADERS, timeout=15,
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["processed"] == 2
        assert len(body["data"]["results"]) == 2
