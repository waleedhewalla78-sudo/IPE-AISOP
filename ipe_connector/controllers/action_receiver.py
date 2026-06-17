import json
import logging
import hmac
import hashlib

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class IpeActionReceiver(http.Controller):

    @http.route("/ipe/action", type="json", auth="none", methods=["POST"], csrf=False)
    def receive_action(self, **kwargs):
        headers = request.httprequest.headers
        raw_body = request.httprequest.get_data(as_text=True)

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON"}

        config = request.env["ipe.config"].sudo().search([("active", "=", True)], limit=1)
        if not config:
            return {"status": "error", "message": "IPE not configured"}

        signature = headers.get("X-IPE-Signature", "")
        expected = hmac.new(config.api_secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            _logger.warning("HMAC signature mismatch for IPE action")
            return {"status": "error", "message": "Invalid signature"}

        action_type = payload.get("action_type") or payload.get("event", "").replace("ipe.", "")
        data = payload.get("data", {})
        tenant_id = headers.get("X-Tenant-ID", "")

        log = request.env["ipe.import.log"].sudo().create({
            "action_type": action_type,
            "status": "received",
            "payload": raw_body,
            "tenant_id": tenant_id,
        })

        try:
            if action_type == "confirm_mo":
                result = self._handle_confirm_mo(data)
            elif action_type == "reschedule_mo":
                result = self._handle_reschedule_mo(data)
            elif action_type == "create_rfq":
                result = self._handle_create_rfq(data)
            elif action_type == "sync_feasibility":
                result = self._handle_sync_feasibility(data)
            elif action_type == "sync_reconciliation":
                result = self._handle_sync_reconciliation(data)
            elif action_type == "sync_demand_classification":
                result = self._handle_sync_demand_classification(data)
            else:
                result = {"status": "skipped", "message": f"Unknown action: {action_type}"}

            log.status = "completed"
            log.response = json.dumps(result)
            _logger.info("IPE action %s completed: %s", action_type, result)
            return {"status": "ok", "action": action_type, "result": result}

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            _logger.error("IPE action %s failed: %s", action_type, e)
            return {"status": "error", "message": str(e)}

    def _handle_confirm_mo(self, data):
        mo_id = data.get("mo_id")
        if not mo_id:
            raise ValueError("mo_id required")
        mo = request.env["mrp.production"].sudo().browse(mo_id)
        if not mo.exists():
            raise ValueError(f"MO {mo_id} not found")
        if mo.state == "draft":
            mo.action_confirm()
        return {"mo_id": mo_id, "state": mo.state}

    def _handle_reschedule_mo(self, data):
        mo_id = data.get("mo_id")
        new_date = data.get("planned_date_finished")
        if not mo_id or not new_date:
            raise ValueError("mo_id and planned_date_finished required")
        mo = request.env["mrp.production"].sudo().browse(mo_id)
        if not mo.exists():
            raise ValueError(f"MO {mo_id} not found")
        from datetime import datetime
        mo.date_planned_finished = datetime.fromisoformat(new_date.replace("Z", "+00:00"))
        return {"mo_id": mo_id, "new_planned_date_finished": new_date}

    def _handle_create_rfq(self, data):
        product_id = data.get("product_id")
        quantity = data.get("quantity")
        supplier_id = data.get("supplier_id")
        if not product_id or not quantity:
            raise ValueError("product_id and quantity required")

        partner = request.env["res.partner"].sudo().browse(supplier_id) if supplier_id else None
        if supplier_id and not partner.exists():
            raise ValueError(f"Supplier {supplier_id} not found")

        product = request.env["product.product"].sudo().browse(product_id)
        if not product.exists():
            raise ValueError(f"Product {product_id} not found")

        po = request.env["purchase.order"].sudo().create({
            "partner_id": partner.id if partner else False,
            "order_line": [(0, 0, {
                "product_id": product.id,
                "product_qty": quantity,
                "price_unit": product.standard_price or 0,
                "name": product.name,
            })],
        })
        return {"rfq_id": po.id, "rfq_name": po.name}

    def _handle_sync_feasibility(self, data):
        mo_id = data.get("mo_id")
        if not mo_id:
            raise ValueError("mo_id required")
        mo = request.env["mrp.production"].sudo().browse(mo_id)
        if not mo.exists():
            raise ValueError(f"MO {mo_id} not found")
        mo.write({
            "ipe_feasibility_score": data.get("overall_score", 0),
            "ipe_primary_constraint": data.get("primary_constraint") or "",
            "ipe_risk_level": data.get("risk_level", "medium"),
        })
        return {
            "mo_id": mo_id,
            "ipe_feasibility_score": data.get("overall_score", 0),
            "ipe_primary_constraint": data.get("primary_constraint"),
            "ipe_risk_level": data.get("risk_level"),
        }

    def _handle_sync_reconciliation(self, data):
        mo_id = data.get("mo_id")
        if not mo_id:
            raise ValueError("mo_id required")
        mo = request.env["mrp.production"].sudo().browse(mo_id)
        if not mo.exists():
            raise ValueError(f"MO {mo_id} not found")
        mo.write({
            "ipe_time_variance_pct": data.get("time_variance_pct", 0),
            "ipe_yield_variance_pct": data.get("yield_variance_pct", 0),
            "ipe_reconciled": True,
        })
        return {
            "mo_id": mo_id,
            "ipe_time_variance_pct": data.get("time_variance_pct"),
            "ipe_yield_variance_pct": data.get("yield_variance_pct"),
            "ipe_reconciled": True,
        }

    def _handle_sync_demand_classification(self, data):
        mo_id = data.get("mo_id")
        if not mo_id:
            raise ValueError("mo_id required")
        mo = request.env["mrp.production"].sudo().browse(mo_id)
        if not mo.exists():
            raise ValueError(f"MO {mo_id} not found")
        mo.write({
            "ipe_demand_type": data.get("demand_type", ""),
            "ipe_priority_score": data.get("priority_score", 0),
        })
        return {
            "mo_id": mo_id,
            "ipe_demand_type": data.get("demand_type"),
            "ipe_priority_score": data.get("priority_score"),
        }
