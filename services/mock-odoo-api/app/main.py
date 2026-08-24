"""Mock Odoo API — XML-RPC + REST for connector integration testing.

Provides:
  GET  /health
  POST /xmlrpc/2/common  — authenticate / version (OdooClient)
  POST /xmlrpc/2/object  — execute_kw search_read / write / read
  POST /ipe/action       — HMAC action receiver
"""

from __future__ import annotations

import hashlib
import hmac
import json
import xmlrpc.client
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock Odoo API", version="1.1.0")

IPE_HMAC_SECRET = "test-hmac-secret-key"


def _xml_response(result) -> Response:
    payload = xmlrpc.client.dumps((result,), methodresponse=True, allow_none=True)
    return Response(content=payload, media_type="text/xml")


def _sample_products() -> list[dict]:
    return [
        {
            "id": 1,
            "default_code": "WGT-A",
            "name": "Widget A",
            "type": "product",
            "uom_id": [1, "Units"],
            "standard_price": 10.0,
            "qty_available": 100.0,
        },
        {
            "id": 2,
            "default_code": "WGT-B",
            "name": "Widget B",
            "type": "product",
            "uom_id": [1, "Units"],
            "standard_price": 20.0,
            "qty_available": 50.0,
        },
    ]


def _sample_boms() -> list[dict]:
    return [
        {
            "id": 11,
            "product_id": [1, "Widget A"],
            "product_tmpl_id": [1, "Widget A"],
            "product_qty": 1.0,
            "active": True,
            "bom_line_ids": [],
            "operation_ids": [],
        },
        {
            "id": 12,
            "product_id": [2, "Widget B"],
            "product_tmpl_id": [2, "Widget B"],
            "product_qty": 1.0,
            "active": True,
            "bom_line_ids": [],
            "operation_ids": [],
        },
    ]


def _sample_mos() -> list[dict]:
    start = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    due = (datetime.now(UTC) + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    return [
        {
            "id": 101,
            "name": "MO-R2-001",
            "product_id": [1, "Widget A"],
            "bom_id": [11, "BOM Widget A"],
            "product_qty": 50.0,
            "state": "confirmed",
            "date_start": start,
            "date_finished": due,
            "write_date": start,
        },
        {
            "id": 102,
            "name": "MO-R2-002",
            "product_id": [2, "Widget B"],
            "bom_id": [12, "BOM Widget B"],
            "product_qty": 25.0,
            "state": "confirmed",
            "date_start": start,
            "date_finished": due,
            "write_date": start,
        },
    ]


def _sample_workcenters() -> list[dict]:
    return [
        {"id": 1, "name": "Assembly Line 1", "active": True, "time_efficiency": 100.0, "capacity": 8.0},
    ]


def _sample_quants() -> list[dict]:
    """Internal stock.quant rows for connector sync_inventory E2E against mock Odoo."""
    return [
        {
            "id": 501,
            "product_id": [1, "Widget A"],
            "quantity": 120.0,
            "reserved_quantity": 20.0,
            "location_id": [8, "WH/Stock"],
        },
        {
            "id": 502,
            "product_id": [2, "Widget B"],
            "quantity": 75.0,
            "reserved_quantity": 5.0,
            "location_id": [8, "WH/Stock"],
        },
    ]


def _execute_kw(model: str, method: str, args: list, kwargs: dict):
    if method == "search_read":
        if model == "product.product":
            return _sample_products()
        if model == "mrp.production":
            return _sample_mos()
        if model == "mrp.bom":
            return _sample_boms()
        if model == "mrp.workcenter":
            return _sample_workcenters()
        if model == "stock.quant":
            return _sample_quants()
        if model == "sale.order":
            return [
                {
                    "id": 1,
                    "name": "SO001",
                    "partner_id": [1, "Acme Corp"],
                    "date_order": "2026-06-01 00:00:00",
                    "state": "sale",
                    "product_id": [1, "Widget A"],
                    "product_uom_qty": 10.0,
                    "scheduled_date": "2026-06-15 00:00:00",
                }
            ]
        if model == "stock.warehouse":
            return [{"id": 1, "name": "Mock WH", "code": "WH01", "company_id": [1, "IPE Mock"]}]
        if model == "product.template":
            return [
                {
                    "id": 1,
                    "default_code": "WGT-A",
                    "name": "Widget A",
                    "type": "product",
                    "uom_id": [1, "Units"],
                },
                {
                    "id": 3,
                    "default_code": "RAW-1",
                    "name": "Raw Input",
                    "type": "consu",
                    "uom_id": [1, "kg"],
                },
            ]
        if model == "resource.calendar":
            return [{"id": 1, "name": "Standard Calendar"}]
        if model == "hr.employee":
            return [{"id": 1, "name": "Mock Operator", "barcode": "E001", "department_id": [1, "Shop"]}]
        if model == "res.partner":
            return [
                {"id": 1, "name": "Acme Corp", "supplier_rank": 0, "customer_rank": 1, "email": "a@x"},
                {"id": 2, "name": "Copper Co", "supplier_rank": 1, "customer_rank": 0, "email": "c@x"},
            ]
        if model in ("purchase.order", "mrp.bom.line", "mrp.routing.workcenter"):
            return []
        return []
    if method == "read":
        ids = args[0] if args else []
        if model == "mrp.production":
            return [m for m in _sample_mos() if m["id"] in ids]
        if model == "product.product":
            return [p for p in _sample_products() if p["id"] in ids]
        if model == "mrp.bom":
            return [b for b in _sample_boms() if b["id"] in ids]
        return []
    if method == "write":
        return True
    if method == "search":
        if model == "mrp.production":
            return [m["id"] for m in _sample_mos()]
        if model == "product.product":
            return [p["id"] for p in _sample_products()]
        if model == "mrp.bom":
            return [b["id"] for b in _sample_boms()]
        return []
    if method == "create":
        return 999
    return []


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mock-odoo-api"}


@app.post("/xmlrpc/2/common")
async def xmlrpc_common(request: Request):
    body = await request.body()
    params, method = xmlrpc.client.loads(body)
    if method in ("authenticate", "login"):
        # db, username, password, context
        return _xml_response(1)
    if method == "version":
        return _xml_response({"server_version": "17.0", "server_serie": "17.0", "protocol_version": 1})
    return _xml_response(False)


@app.post("/xmlrpc/2/object")
async def xmlrpc_object(request: Request):
    body = await request.body()
    params, method = xmlrpc.client.loads(body)
    if method != "execute_kw":
        return _xml_response(False)
    # db, uid, password, model, method, args, kwargs?
    model = params[3]
    meth = params[4]
    args = params[5] if len(params) > 5 else []
    kwargs = params[6] if len(params) > 6 else {}
    if not isinstance(kwargs, dict):
        kwargs = {}
    return _xml_response(_execute_kw(model, meth, list(args), kwargs))


@app.post("/web/session/authenticate")
async def authenticate():
    return {
        "id": 1,
        "jsonrpc": "2.0",
        "result": {
            "uid": 1,
            "name": "IPE Connector User",
            "session_id": str(uuid4()),
        },
    }


@app.post("/web/dataset/call_kw")
async def call_kw(request: Request):
    body = await request.json()
    params = body.get("params", {})
    model = params.get("model", "")
    method = params.get("method", "")
    args = params.get("args", [])
    kwargs = params.get("kwargs", {})
    result = _execute_kw(model, method, args, kwargs)
    return {"id": body.get("id", 1), "jsonrpc": "2.0", "result": result}


@app.post("/ipe/action")
async def ipe_action(request: Request):
    signature = request.headers.get("X-IPE-Signature", "")
    body_bytes = await request.body()
    expected_sig = hmac.new(
        IPE_HMAC_SECRET.encode(),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "HMAC signature mismatch"},
        )

    body = json.loads(body_bytes)
    action = body.get("action_type") or body.get("action", "unknown")

    if action == "confirm_mo":
        return {"status": "ok", "data": {"mo_id": body.get("data", {}).get("mo_id", body.get("mo_id")), "state": "confirmed"}}
    if action == "reschedule_mo":
        return {
            "status": "ok",
            "data": {
                "mo_id": body.get("data", {}).get("mo_id", body.get("mo_id")),
                "rescheduled_date": body.get("data", {}).get("new_date"),
            },
        }
    if action == "create_rfq":
        data = body.get("data", {})
        return {
            "status": "ok",
            "data": {
                "rfq_id": str(uuid4()),
                "product_id": data.get("product_id"),
                "supplier_id": data.get("supplier_id"),
                "quantity": data.get("order_quantity"),
            },
        }
    if action in ("sync_feasibility", "sync_reconciliation", "sync_demand_classification"):
        return {"status": "ok", "data": {"synced": True, "action": action}}

    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": f"Unknown action: {action}"},
    )
