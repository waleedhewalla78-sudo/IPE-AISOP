"""IPE REST API for Odoo 19 — read/search domains + write-back."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# domain_key -> (model, default_fields, base_domain)
DOMAIN_REGISTRY: dict[str, tuple[str, list[str], list]] = {
    "sales_orders": (
        "sale.order",
        ["id", "name", "partner_id", "date_order", "state", "amount_total", "currency_id", "order_line"],
        [],
    ),
    "stock_levels": (
        "stock.quant",
        ["id", "product_id", "location_id", "quantity", "reserved_quantity", "lot_id", "package_id"],
        [("location_id.usage", "=", "internal")],
    ),
    "products": (
        "product.product",
        [
            "id", "name", "default_code", "categ_id", "type", "uom_id", "tracking",
            "bom_ids", "seller_ids", "standard_price", "list_price", "qty_available", "write_date",
        ],
        [("active", "=", True)],
    ),
    "bom": (
        "mrp.bom",
        ["id", "product_id", "product_tmpl_id", "bom_line_ids", "product_qty", "type", "operation_ids", "write_date"],
        [("active", "=", True)],
    ),
    "production_orders": (
        "mrp.production",
        [
            "id", "name", "product_id", "product_qty", "state", "date_start", "date_finished",
            "bom_id", "move_raw_ids", "move_finished_ids", "write_date",
        ],
        [("state", "not in", ["cancel"])],
    ),
    "purchase_orders": (
        "purchase.order",
        ["id", "name", "partner_id", "date_order", "date_planned", "state", "order_line", "amount_total", "currency_id"],
        [("state", "in", ["purchase", "done"])],
    ),
    "suppliers": (
        "res.partner",
        ["id", "name", "country_id", "email", "phone", "supplier_rank"],
        [("supplier_rank", ">", 0)],
    ),
    "locations": (
        "stock.location",
        ["id", "name", "display_name", "location_id", "usage", "warehouse_id", "company_id"],
        [("usage", "=", "internal")],
    ),
    "manufacturing_routes": (
        "stock.route",
        [],
        [],
    ),
    "cost_data": (
        "product.product",
        ["id", "name", "standard_price", "write_date"],
        [("active", "=", True)],
    ),
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get_api_key() -> str | None:
    return request.env["ir.config_parameter"].sudo().get_param("ipe.api.key")


def _validate_api_key() -> bool:
    expected = _get_api_key()
    if not expected:
        return False
    provided = request.httprequest.headers.get("X-IPE-API-KEY", "")
    if not provided:
        return False
    try:
        return hmac.compare_digest(
            hashlib.sha256(expected.encode()).hexdigest(),
            hashlib.sha256(provided.encode()).hexdigest(),
        )
    except Exception:
        return hmac.compare_digest(expected, provided)


def _parse_body() -> dict:
    raw = request.httprequest.get_data(as_text=True) or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _build_domain(base: list, filters: dict, cursor: int | None) -> list:
    domain = list(base)
    for field, spec in (filters or {}).items():
        if isinstance(spec, dict):
            for op, val in spec.items():
                domain.append((field, op, val))
        else:
            domain.append((field, "=", spec))
    if cursor:
        domain.append(("id", ">", int(cursor)))
    return domain


def _serialize_records(model: str, records: list) -> list:
    """Expand x2many ids to nested read where useful."""
    env = request.env
    out = []
    for rec in records:
        row = dict(rec)
        if model == "mrp.bom" and rec.get("bom_line_ids"):
            lines = env["mrp.bom.line"].sudo().browse(rec["bom_line_ids"]).read(
                ["id", "product_id", "product_qty", "product_uom_id"]
            )
            row["bom_line_ids"] = lines
        if model == "mrp.bom" and rec.get("operation_ids"):
            ops = env["mrp.routing.workcenter"].sudo().browse(rec["operation_ids"]).read(
                ["id", "name", "sequence", "workcenter_id", "time_cycle_manual"]
            )
            row["operation_ids"] = ops
        if model in ("sale.order", "purchase.order") and rec.get("order_line"):
            line_model = "sale.order.line" if model == "sale.order" else "purchase.order.line"
            lines = env[line_model].sudo().browse(rec["order_line"]).read(
                ["id", "product_id", "product_uom_qty", "product_qty", "price_unit", "date_planned", "partner_id"]
            )
            row["order_line"] = lines
        out.append(row)
    return out


class IpeApiController(http.Controller):

    @http.route("/ipe/api/v1/health", type="http", auth="none", methods=["GET"], csrf=False)
    def health(self, **kwargs):
        if not _validate_api_key():
            return request.make_json_response({"status": "unauthorized"}, status=401)
        modules = ["sale", "stock", "mrp", "purchase", "ipe_connector"]
        installed = []
        Mod = request.env["ir.module.module"].sudo()
        for name in modules:
            if Mod.search([("name", "=", name), ("state", "=", "installed")], limit=1):
                installed.append(name)
        try:
            from odoo.release import version as odoo_version
            ver = odoo_version
        except Exception:
            ver = "19.0"
        return request.make_json_response({
            "status": "healthy",
            "odoo_version": ver,
            "modules_installed": installed,
            "sync_ts": _utc_now_iso(),
        })

    @http.route("/ipe/api/v1/<string:domain>", type="http", auth="none", methods=["POST"], csrf=False)
    def domain_api(self, domain, **kwargs):
        if not _validate_api_key():
            return request.make_json_response({"status": "error", "message": "Invalid API key"}, status=401)

        body = _parse_body()
        action = body.get("action", "search")

        if domain == "write_back":
            return request.make_json_response(self._write_back(body))

        if domain not in DOMAIN_REGISTRY:
            return request.make_json_response({"status": "error", "message": f"Unknown domain: {domain}"}, status=404)

        model, default_fields, base_domain = DOMAIN_REGISTRY[domain]
        env = request.env

        if action == "read":
            ids = body.get("ids") or []
            if not ids:
                return request.make_json_response({"status": "error", "message": "ids required for read"}, status=400)
            fields = body.get("fields") or default_fields
            data = env[model].sudo().browse(ids).read(fields)
            data = _serialize_records(model, data)
            return request.make_json_response({
                "status": "success", "data": data, "count": len(data), "next_cursor": None, "sync_ts": _utc_now_iso(),
            })

        if action != "search":
            return request.make_json_response({"status": "error", "message": f"Unknown action: {action}"}, status=400)

        limit = min(int(body.get("limit") or 100), 1000)
        cursor = body.get("cursor")
        fields = body.get("fields") or default_fields
        domain_filter = _build_domain(base_domain, body.get("filters") or {}, cursor)

        Model = env[model].sudo()
        ids = Model.search(domain_filter, limit=limit, order="id asc")
        data = ids.read(fields) if ids else []
        data = _serialize_records(model, data)
        next_cursor = str(data[-1]["id"]) if data and len(data) >= limit else None

        return request.make_json_response({
            "status": "success",
            "data": data,
            "count": len(data),
            "next_cursor": next_cursor,
            "sync_ts": _utc_now_iso(),
        })

    @http.route("/ipe/api/v1/write_back/status", type="http", auth="none", methods=["GET"], csrf=False)
    def write_back_status(self, **kwargs):
        if not _validate_api_key():
            return request.make_json_response({"status": "unauthorized"}, status=401)
        logs = request.env["ipe.import.log"].sudo().search([], limit=20, order="create_date desc")
        return request.make_json_response({
            "status": "success",
            "data": [{
                "id": log.id,
                "action_type": log.action_type,
                "status": log.status,
                "created": log.create_date.isoformat() if log.create_date else None,
            } for log in logs],
            "sync_ts": _utc_now_iso(),
        })

    def _write_back(self, body: dict) -> dict:
        action = body.get("action", "create")
        model_name = body.get("model")
        env = request.env.sudo()

        if action == "update" and model_name == "mrp.production":
            ids = body.get("ids") or []
            values = body.get("values") or {}
            write_vals = {}
            if values.get("date_planned_start"):
                write_vals["date_start"] = values["date_planned_start"]
            elif values.get("new_start_date"):
                write_vals["date_start"] = values["new_start_date"]
            if values.get("date_planned_finished"):
                write_vals["date_finished"] = values["date_planned_finished"]
            elif values.get("new_end_date"):
                write_vals["date_finished"] = values["new_end_date"]
            if values.get("ipe_plan_id") and "ipe_plan_id" in env["mrp.production"]._fields:
                write_vals["ipe_plan_id"] = values["ipe_plan_id"]
            if values.get("plan_source") and "plan_source" in env["mrp.production"]._fields:
                write_vals["plan_source"] = values["plan_source"]
            env["mrp.production"].browse(ids).write(write_vals)
            return {"status": "success", "updated": len(ids), "sync_ts": _utc_now_iso()}

        if action == "create" and model_name == "purchase.order":
            values = body.get("values") or {}
            po = env["purchase.order"].create(values)
            return {"status": "success", "id": po.id, "name": po.name, "sync_ts": _utc_now_iso()}

        if action == "create" and model_name == "ipe.forecast":
            if "ipe.forecast" not in env:
                return {"status": "error", "message": "ipe.forecast model not installed"}
            rec = env["ipe.forecast"].create(body.get("values") or {})
            return {"status": "success", "id": rec.id, "sync_ts": _utc_now_iso()}

        if action == "message_post" and model_name == "mrp.production":
            res_id = body.get("res_id")
            if not res_id:
                return {"status": "error", "message": "res_id required for message_post"}
            prod = env["mrp.production"].browse(int(res_id))
            if not prod.exists():
                return {"status": "error", "message": f"mrp.production {res_id} not found"}
            body_html = body.get("body") or ""
            prod.message_post(
                body=body_html,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                subject=body.get("subject") or "IPE Resolution",
            )
            return {"status": "success", "res_id": int(res_id), "sync_ts": _utc_now_iso()}

        return {"status": "error", "message": f"Unsupported write_back: {action} {model_name}"}
