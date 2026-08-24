"""Wave 1 Odoo master adapters — mocked XML-RPC + orchestrator."""

from __future__ import annotations

from uuid import UUID

from app.wave1.base import (
    ADAPTER_ORDER,
    BomAdapter,
    CustomerAdapter,
    MaterialAdapter,
    PlantAdapter,
    ProductAdapter,
    SupplierAdapter,
    WorkCenterAdapter,
)
from app.wave1.orchestrator import sync_all_master_data

TENANT = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


class FakeOdoo:
    def __init__(self, data: dict[str, list[dict]] | None = None, fail_model: str | None = None):
        self.data = data or {}
        self.fail_model = fail_model
        self.authenticated = False
        self.calls: list[str] = []

    def authenticate(self) -> int:
        self.authenticated = True
        return 1

    def search_read(self, model, domain=None, fields=None, limit=None):
        self.calls.append(model)
        if self.fail_model and model == self.fail_model:
            raise RuntimeError(f"forced fail {model}")
        rows = list(self.data.get(model, []))
        if domain:
            for clause in domain:
                if len(clause) == 3 and clause[0] == "supplier_rank" and clause[1] == ">":
                    rows = [r for r in rows if int(r.get("supplier_rank") or 0) > int(clause[2])]
                if len(clause) == 3 and clause[0] == "customer_rank" and clause[1] == ">":
                    rows = [r for r in rows if int(r.get("customer_rank") or 0) > int(clause[2])]
                if len(clause) == 3 and clause[0] == "type" and clause[1] == "=":
                    rows = [r for r in rows if r.get("type") == clause[2]]
                if len(clause) == 3 and clause[0] == "type" and clause[1] == "in":
                    rows = [r for r in rows if r.get("type") in clause[2]]
        return rows[: limit or 500]


SAMPLE = {
    "stock.warehouse": [{"id": 1, "name": "Cairo WH", "code": "CAI01", "company_id": [1, "ST"]}],
    "mrp.workcenter": [
        {"id": 1, "name": "Core Cut", "code": "CORE-CUT", "time_efficiency": 85.0, "capacity": 8.0}
    ],
    "resource.calendar": [{"id": 1, "name": "Standard"}],
    "product.template": [
        {
            "id": 10,
            "name": "TX 500kVA",
            "default_code": "DIST-500",
            "type": "product",
            "uom_id": [1, "unit"],
        },
        {
            "id": 11,
            "name": "Copper wire",
            "default_code": "CU-W-6",
            "type": "consu",
            "uom_id": [1, "kg"],
        },
    ],
    "mrp.bom": [{"id": 20, "code": "BOM-500", "product_tmpl_id": [10, "TX"], "product_qty": 1.0}],
    "mrp.routing.workcenter": [
        {"id": 30, "name": "Cut", "workcenter_id": [1, "Core Cut"], "bom_id": [20, "BOM"]}
    ],
    "res.partner": [
        {"id": 40, "name": "Midwest Copper", "supplier_rank": 1, "customer_rank": 0},
        {"id": 41, "name": "EEHC", "supplier_rank": 0, "customer_rank": 2},
        {"id": 42, "name": "Neither", "supplier_rank": 0, "customer_rank": 0},
    ],
    "hr.employee": [
        {"id": 50, "name": "Mohamed Ali", "barcode": "E0001", "department_id": [1, "Winding"]}
    ],
}


def test_1_authenticate():
    c = FakeOdoo()
    assert c.authenticate() == 1
    assert c.authenticated is True


def test_2_plants_transform():
    rec = PlantAdapter(FakeOdoo(SAMPLE), {}).transform_to_canonical(SAMPLE["stock.warehouse"][0])
    assert rec is not None
    assert rec.natural_key == "CAI01"
    assert rec.fields["name"] == "Cairo WH"
    assert rec.payload["source_system"] == "odoo"


def test_3_work_centers_efficiency_factor():
    rec = WorkCenterAdapter(FakeOdoo(SAMPLE), {}).transform_to_canonical(SAMPLE["mrp.workcenter"][0])
    assert rec is not None
    assert rec.payload["efficiency_factor"] == 0.85


def test_4_products_vs_materials():
    pa = ProductAdapter(FakeOdoo(SAMPLE), {})
    goods = pa.transform_to_canonical(SAMPLE["product.template"][0])
    raw = pa.transform_to_canonical(SAMPLE["product.template"][1])
    assert goods is not None and goods.table == "cdm_ingest_product"
    assert raw is None
    mat = MaterialAdapter(FakeOdoo(SAMPLE), {}).transform_to_canonical(SAMPLE["product.template"][1])
    assert mat is not None and mat.table == "cdm_ingest_material"


def test_5_bom_qty():
    rec = BomAdapter(FakeOdoo(SAMPLE), {}).transform_to_canonical(SAMPLE["mrp.bom"][0])
    assert rec is not None
    assert rec.payload["output_qty"] == 1.0
    assert rec.natural_key == "BOM-500"


def test_6_suppliers_rank_filter():
    rows = SupplierAdapter(FakeOdoo(SAMPLE), {}).fetch_from_odoo()
    assert [r["id"] for r in rows] == [40]


def test_7_customers_rank_filter():
    rows = CustomerAdapter(FakeOdoo(SAMPLE), {}).fetch_from_odoo()
    assert [r["id"] for r in rows] == [41]


def test_8_orchestrator_order():
    names = [cls.entity for cls in ADAPTER_ORDER]
    assert names == [
        "plants",
        "calendars",
        "work_centers",
        "products",
        "materials",
        "boms",
        "routings",
        "suppliers",
        "customers",
        "employees",
    ]
    c = FakeOdoo(SAMPLE)
    report = sync_all_master_data(TENANT, c)
    assert [a["entity"] for a in report.adapters] == names
    assert c.calls[0] == "stock.warehouse"


def test_9_orchestrator_isolates_failure():
    c = FakeOdoo(SAMPLE, fail_model="mrp.bom")
    report = sync_all_master_data(TENANT, c)
    bom = next(a for a in report.adapters if a["entity"] == "boms")
    emp = next(a for a in report.adapters if a["entity"] == "employees")
    assert bom["failed"] >= 1
    assert emp["upserted"] == 1


def test_10_idempotent_upsert():
    store: dict = {}
    r1 = sync_all_master_data(TENANT, FakeOdoo(SAMPLE), store=store)
    n1 = len(store)
    r2 = sync_all_master_data(TENANT, FakeOdoo(SAMPLE), store=store)
    assert len(store) == n1
    assert r1.adapters[0]["upserted"] >= 1
    assert r2.adapters[0]["upserted"] >= 1
