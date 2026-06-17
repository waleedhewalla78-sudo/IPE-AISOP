"""Mock Odoo API — simulates Odoo XML-RPC and IPE action endpoints.

Endpoints:
  POST /web/session/authenticate  — authenticates and returns a session
  POST /web/dataset/call_kw      — simulates Odoo model method calls (sale.order, mrp.production)
  POST /ipe/action                — receives IPE auto-confirm/reschedule actions, validates HMAC
  GET  /health                    — health check

All endpoints return deterministic JSON responses for connector integration testing.
"""

import hashlib
import hmac
import json
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock Odoo API", version="1.0.0")

IPE_HMAC_SECRET = "test-hmac-secret-key"


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mock-odoo-api"}


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

    if model == "sale.order" and method == "search_read":
        # Return a deterministic sale order
        return {
            "id": body.get("id", 1),
            "jsonrpc": "2.0",
            "result": [
                {
                    "id": 1,
                    "name": "SO001",
                    "partner_id": [1, "Acme Corp"],
                    "date_order": "2026-06-01T00:00:00Z",
                    "order_line": [
                        [1, {"product_id": [1, "Widget A"], "product_uom_qty": 10.0}],
                    ],
                    "state": "sale",
                }
            ],
        }

    if model == "mrp.production" and method == "write":
        return {"id": body.get("id", 1), "jsonrpc": "2.0", "result": True}

    if model == "mrp.production" and method == "search_read":
        return {
            "id": body.get("id", 1),
            "jsonrpc": "2.0",
            "result": [
                {
                    "id": 1,
                    "name": "MO001",
                    "product_id": [1, "Widget A"],
                    "product_qty": 100.0,
                    "state": "confirmed",
                }
            ],
        }

    return {"id": body.get("id", 1), "jsonrpc": "2.0", "result": []}


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
    action = body.get("action", "unknown")

    if action == "confirm_mo":
        return {"status": "ok", "data": {"mo_id": body.get("mo_id"), "state": "confirmed"}}
    if action == "reschedule_mo":
        return {"status": "ok", "data": {"mo_id": body.get("mo_id"), "rescheduled_date": body.get("new_date")}}
    if action == "create_rfq":
        return {"status": "ok", "data": {"rfq_id": str(uuid4())}}

    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": f"Unknown action: {action}"},
    )
