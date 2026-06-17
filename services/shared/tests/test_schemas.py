import pytest
from uuid import uuid4
from datetime import datetime, timezone

from ipe_shared.schemas.auth import LoginRequest, LoginResponse, UserInfo
from ipe_shared.schemas.bom import BomLineSchema, BillOfMaterialResponse
from ipe_shared.schemas.common import APIResponse, APIError, APIMeta, HealthResponse, PaginationParams
from ipe_shared.schemas.demand import DemandLineCreate, DemandLineResponse, ClassifyRequest, ClassifyResponse
from ipe_shared.schemas.delay import DelayClassifyRequest, DelayClassifyResponse
from ipe_shared.schemas.feasibility import FeasibilityScoreRequest, FeasibilityScoreResponse
from ipe_shared.schemas.inventory import InventoryPositionResponse
from ipe_shared.schemas.manufacturing_order import ManufacturingOrderResponse
from ipe_shared.schemas.product import ProductResponse
from ipe_shared.schemas.resolution import ScenarioProposeRequest, ScenarioResponse, ApproveRequest
from ipe_shared.schemas.supply import SupplyOrderResponse
from ipe_shared.schemas.work_center import WorkCenterResponse


class TestAuthSchemas:
    def test_login_request(self):
        req = LoginRequest(email="user@test.com", password="secret")
        assert req.email == "user@test.com"

    def test_login_response(self):
        resp = LoginResponse(access_token="abc", refresh_token="def", expires_in=3600)
        assert resp.token_type == "bearer"

    def test_user_info(self):
        uid = uuid4()
        tid = uuid4()
        info = UserInfo(id=uid, email="a@b.com", full_name="Test", role="admin", tenant_id=tid)
        assert info.id == uid
        assert info.tenant_id == tid


class TestCommonSchemas:
    def test_api_response_success(self):
        resp = APIResponse(success=True, data={"key": "val"}, error=None)
        assert resp.success is True

    def test_api_response_error(self):
        err = APIError(code="NOT_FOUND", message="Not found")
        resp = APIResponse(success=False, data=None, error=err)
        assert resp.success is False
        assert resp.error.code == "NOT_FOUND"

    def test_api_error(self):
        err = APIError(code="ERR", message="msg", details={"k": "v"})
        assert err.details == {"k": "v"}

    def test_api_meta(self):
        meta = APIMeta(total=100, offset=0, limit=50, processing_time_ms=42)
        assert meta.total == 100

    def test_health_response(self):
        hr = HealthResponse(service="test", version="1.0", timestamp=datetime.now(timezone.utc))
        assert hr.status == "ok"

    def test_pagination_params_defaults(self):
        p = PaginationParams()
        assert p.offset == 0
        assert p.limit == 50


class TestBomSchemas:
    def test_bom_line_schema(self):
        cid = uuid4()
        line = BomLineSchema(component_id=cid, quantity_per=2.5)
        assert line.component_id == cid
        assert line.quantity_per == 2.5
        assert line.uom == "unit"

    def test_bom_response(self):
        bom = BillOfMaterialResponse(id=uuid4(), product_id=uuid4(), version="v1", is_active=True)
        assert bom.is_active is True


class TestDemandSchemas:
    def test_demand_line_create(self):
        d = DemandLineCreate(
            erp_source_id="SRC1", erp_source_type="odoo",
            product_id=uuid4(), quantity=100.0, uom="pcs",
            required_date=datetime.now(timezone.utc), demand_type="MTO"
        )
        assert d.quantity == 100.0

    def test_demand_line_response(self):
        d = DemandLineResponse(
            id=uuid4(), product_id=uuid4(), quantity=50.0,
            required_date=datetime.now(timezone.utc), demand_type="MTS",
            priority_score=0.9, status="open", created_at=datetime.now(timezone.utc)
        )
        assert d.status == "open"

    def test_classify_request(self):
        ids = [uuid4(), uuid4()]
        r = ClassifyRequest(demand_line_ids=ids)
        assert len(r.demand_line_ids) == 2

    def test_classify_response(self):
        r = ClassifyResponse(demand_line_id=uuid4(), priority_score=0.8, demand_type="MTO", confidence=0.95)
        assert r.confidence == 0.95


class TestDelaySchemas:
    def test_delay_classify_request(self):
        r = DelayClassifyRequest(source_text="Machine broke down")
        assert r.source_text == "Machine broke down"

    def test_delay_classify_response(self):
        r = DelayClassifyResponse(cause_category="equipment", confidence=0.9, delay_minutes=60)
        assert r.cause_category == "equipment"


class TestFeasibilitySchemas:
    def test_feasibility_request(self):
        r = FeasibilityScoreRequest(mo_id=uuid4())
        assert r.mo_id is not None

    def test_feasibility_response(self):
        r = FeasibilityScoreResponse(
            mo_id=uuid4(), feasibility_score=0.85,
            material_score=0.9, capacity_score=0.8, labor_score=None,
            primary_constraint="capacity"
        )
        assert r.feasibility_score == 0.85
        assert r.primary_constraint == "capacity"


class TestInventorySchemas:
    def test_inventory_response(self):
        r = InventoryPositionResponse(
            time=datetime.now(timezone.utc), product_id=uuid4(),
            location_id=uuid4(), qty_on_hand=100.0,
            qty_reserved=20.0, qty_in_transit=30.0
        )
        assert r.qty_on_hand == 100.0


class TestMOSchemas:
    def test_mo_response(self):
        r = ManufacturingOrderResponse(
            id=uuid4(), product_id=uuid4(), quantity=10.0, status="draft",
            planned_start=None, planned_end=None,
            feasibility_score=None, material_score=None,
            capacity_score=None, labor_score=None, primary_constraint=None,
            created_at=datetime.now(timezone.utc)
        )
        assert r.status == "draft"
        assert r.quantity == 10.0


class TestProductSchemas:
    def test_product_response(self):
        r = ProductResponse(
            id=uuid4(), erp_source_id="ERP1", name="Widget",
            source_type="odoo", uom="pcs", safety_stock=10.0,
            internal_ref=None, standard_cost=None, lead_time_days=None,
            created_at=datetime.now(timezone.utc)
        )
        assert r.name == "Widget"
        assert r.safety_stock == 10.0


class TestResolutionSchemas:
    def test_scenario_propose_request(self):
        r = ScenarioProposeRequest(mo_id=uuid4())
        assert r.mo_id is not None

    def test_scenario_response(self):
        r = ScenarioResponse(
            id=uuid4(), mo_id=uuid4(), strategy="reroute",
            description="Reroute to Line B", status="proposed",
            delivery_impact_days=None, cost_impact=None, business_score=None
        )
        assert r.strategy == "reroute"

    def test_approve_request(self):
        r = ApproveRequest(scenario_id=uuid4())
        assert r.scenario_id is not None


class TestSupplySchemas:
    def test_supply_order_response(self):
        r = SupplyOrderResponse(
            id=uuid4(), product_id=uuid4(), quantity_ordered=500.0,
            quantity_received=100.0, expected_date=datetime.now(timezone.utc),
            status="open", supplier_id=None, reliability_adjusted_date=None
        )
        assert r.quantity_ordered == 500.0


class TestWorkCenterSchemas:
    def test_work_center_response(self):
        r = WorkCenterResponse(
            id=uuid4(), name="Line 1", capacity_hours_per_day=16.0,
            oee=0.85, status="active", cost_per_hour=None
        )
        assert r.name == "Line 1"
        assert r.capacity_hours_per_day == 16.0
