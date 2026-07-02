"""Odoo 19 REST/JSON API adapter for IPE connector."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OdooAdapter:
    """Pull/push adapter calling Odoo ipe_connector REST API (/ipe/api/v1/*)."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        db: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (base_url or os.getenv("ODOO_URL", "http://host.docker.internal:8069")).rstrip("/")
        self.api_key = api_key or os.getenv("ODOO_API_KEY", "ipe-local-dev-key-change-in-production")
        self.db = db or os.getenv("ODOO_DB", "starttrans1")
        self.timeout = timeout or float(os.getenv("ODOO_TIMEOUT", "30"))
        self._headers = {"X-IPE-API-KEY": self.api_key, "Content-Type": "application/json"}

    async def _call(
        self,
        domain: str,
        action: str = "search",
        filters: dict | None = None,
        fields: list[str] | None = None,
        limit: int = 100,
        cursor: int | None = None,
        extra: dict | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"action": action, "filters": filters or {}, "limit": limit}
        if fields:
            payload["fields"] = fields
        if cursor is not None:
            payload["cursor"] = cursor
        if extra:
            payload.update(extra)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/ipe/api/v1/{domain}",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def health_check(self) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/ipe/api/v1/health", headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def pull_sales_orders(self, since: datetime | None = None, limit: int = 500) -> list[dict]:
        filters: dict = {"state": {"in": ["sale", "done"]}}
        if since:
            filters["write_date"] = {">=": since.isoformat()}
        result = await self._call("sales_orders", "search", filters, limit=limit)
        return self._transform_sales(result.get("data", []))

    async def pull_stock_levels(self, product_ids: list | None = None, limit: int = 1000) -> list[dict]:
        filters: dict = {}
        if product_ids:
            filters["product_id"] = {"in": product_ids}
        result = await self._call("stock_levels", "search", filters, limit=limit)
        return self._transform_stock(result.get("data", []))

    async def pull_products(self, since: datetime | None = None, limit: int = 500) -> list[dict]:
        filters: dict = {}
        if since:
            filters["write_date"] = {">=": since.isoformat()}
        result = await self._call("products", "search", filters, limit=limit)
        return self._transform_products(result.get("data", []))

    async def pull_boms(self, limit: int = 500) -> list[dict]:
        result = await self._call("bom", "search", {}, limit=limit)
        return self._transform_boms(result.get("data", []))

    async def pull_production_orders(self, since: datetime | None = None, limit: int = 500) -> list[dict]:
        filters: dict = {"state": {"in": ["confirmed", "progress", "draft", "to_close"]}}
        if since:
            filters["write_date"] = {">=": since.isoformat()}
        result = await self._call("production_orders", "search", filters, limit=limit)
        return self._transform_production(result.get("data", []))

    async def pull_purchase_orders(self, since: datetime | None = None, limit: int = 500) -> list[dict]:
        filters: dict = {"state": {"in": ["purchase", "done"]}}
        if since:
            filters["write_date"] = {">=": since.isoformat()}
        result = await self._call("purchase_orders", "search", filters, limit=limit)
        return self._transform_purchases(result.get("data", []))

    async def pull_suppliers(self, limit: int = 200) -> list[dict]:
        result = await self._call("suppliers", "search", {}, limit=limit)
        return self._transform_suppliers(result.get("data", []))

    async def pull_locations(self, limit: int = 200) -> list[dict]:
        result = await self._call("locations", "search", {}, limit=limit)
        return self._transform_locations(result.get("data", []))

    async def pull_cost_data(self, product_ids: list | None = None, limit: int = 1000) -> list[dict]:
        filters: dict = {}
        if product_ids:
            filters["id"] = {"in": product_ids}
        result = await self._call("cost_data", "search", filters, limit=limit)
        return [
            {
                "external_id": f"odoo_cost_{p['id']}",
                "product_id": p["id"],
                "cost": p.get("standard_price", 0),
                "synced_at": datetime.now(UTC).isoformat(),
            }
            for p in result.get("data", [])
        ]

    async def push_supply_plan(self, plan: dict) -> dict:
        return await self._call(
            "write_back",
            "update",
            extra={
                "action": "update",
                "model": "mrp.production",
                "ids": plan.get("production_order_ids", []),
                "values": {
                    "new_start_date": plan.get("new_start_date"),
                    "new_end_date": plan.get("new_end_date"),
                    "ipe_plan_id": plan.get("plan_id"),
                    "plan_source": "ipe",
                },
            },
        )

    async def push_procurement_recommendation(self, rec: dict) -> dict:
        return await self._call(
            "write_back",
            "create",
            extra={
                "action": "create",
                "model": "purchase.order",
                "values": {
                    "partner_id": rec.get("supplier_id"),
                    "order_line": rec.get("lines", []),
                    "origin": f"IPE-PROC-{rec.get('plan_id', 'auto')}",
                },
            },
        )

    async def push_resolution_notify(self, payload: dict) -> dict:
        """Post IPE resolution approval as Odoo chatter on mrp.production."""
        return await self._call(
            "write_back",
            "message_post",
            extra={
                "action": "message_post",
                "model": "mrp.production",
                "res_id": payload.get("erp_mo_id") or payload.get("odoo_production_id"),
                "body": payload.get("body", ""),
                "subject": payload.get("subject", "IPE Resolution Approved"),
            },
        )

    # --- transforms ---

    @staticmethod
    def _m2o(val) -> tuple[Any, str]:
        if isinstance(val, (list, tuple)) and len(val) >= 2:
            return val[0], val[1]
        if isinstance(val, (list, tuple)) and len(val) == 1:
            return val[0], str(val[0])
        return val, str(val) if val else ""

    def _transform_sales(self, raw_orders: list) -> list[dict]:
        out = []
        for o in raw_orders:
            lines = []
            for line in o.get("order_line") or []:
                if isinstance(line, dict):
                    pid, _ = self._m2o(line.get("product_id"))
                    lines.append({
                        "line_id": line.get("id"),
                        "product_id": pid,
                        "quantity": line.get("product_uom_qty", 0),
                        "unit_price": line.get("price_unit", 0),
                    })
            cid, cname = self._m2o(o.get("partner_id"))
            out.append({
                "external_id": f"odoo_so_{o['id']}",
                "source": "odoo",
                "order_number": o.get("name"),
                "customer_id": cid,
                "customer": cname,
                "order_date": o.get("date_order"),
                "state": o.get("state"),
                "total_amount": o.get("amount_total"),
                "lines": lines,
                "synced_at": datetime.now(UTC).isoformat(),
            })
        return out

    def _transform_stock(self, raw_quants: list) -> list[dict]:
        out = []
        for q in raw_quants:
            pid, pname = self._m2o(q.get("product_id"))
            lid, lname = self._m2o(q.get("location_id"))
            qty = float(q.get("quantity") or 0)
            reserved = float(q.get("reserved_quantity") or 0)
            out.append({
                "external_id": f"odoo_quant_{q['id']}",
                "product_id": pid,
                "product_sku": pname,
                "location_id": lid,
                "location_name": lname,
                "on_hand": qty,
                "reserved": reserved,
                "available": qty - reserved,
                "synced_at": datetime.now(UTC).isoformat(),
            })
        return out

    def _transform_products(self, raw_products: list) -> list[dict]:
        out = []
        for p in raw_products:
            cat_id, cat_name = self._m2o(p.get("categ_id"))
            uom_id, uom_name = self._m2o(p.get("uom_id"))
            out.append({
                "external_id": f"odoo_product_{p['id']}",
                "source": "odoo",
                "sku": p.get("default_code") or f"ODOO-{p['id']}",
                "name": p.get("name"),
                "category": cat_name,
                "type": p.get("type"),
                "uom": uom_name,
                "tracking": p.get("tracking"),
                "standard_cost": p.get("standard_price", 0),
                "list_price": p.get("list_price", 0),
                "qty_available": p.get("qty_available", 0),
                "synced_at": datetime.now(UTC).isoformat(),
            })
        return out

    def _transform_boms(self, raw_boms: list) -> list[dict]:
        out = []
        for b in raw_boms:
            pid, pname = self._m2o(b.get("product_id") or b.get("product_tmpl_id"))
            components = []
            for bl in b.get("bom_line_ids") or []:
                if isinstance(bl, dict):
                    cid, cname = self._m2o(bl.get("product_id"))
                    components.append({
                        "component_id": cid,
                        "component_name": cname,
                        "quantity": bl.get("product_qty", 0),
                    })
            out.append({
                "external_id": f"odoo_bom_{b['id']}",
                "product_id": pid,
                "product_name": pname,
                "quantity": b.get("product_qty", 1),
                "type": b.get("type"),
                "components": components,
                "operations": b.get("operation_ids") or [],
                "synced_at": datetime.now(UTC).isoformat(),
            })
        return out

    def _transform_production(self, raw_orders: list) -> list[dict]:
        out = []
        for p in raw_orders:
            pid, pname = self._m2o(p.get("product_id"))
            bid, _ = self._m2o(p.get("bom_id"))
            out.append({
                "external_id": f"odoo_mo_{p['id']}",
                "source": "odoo",
                "production_order": p.get("name"),
                "product_id": pid,
                "product_name": pname,
                "quantity": p.get("product_qty"),
                "state": p.get("state"),
                "scheduled_start": p.get("date_start") or p.get("date_planned_start"),
                "scheduled_end": p.get("date_finished") or p.get("date_planned_finished"),
                "bom_id": bid,
                "synced_at": datetime.now(UTC).isoformat(),
            })
        return out

    def _transform_purchases(self, raw_orders: list) -> list[dict]:
        out = []
        for o in raw_orders:
            sid, sname = self._m2o(o.get("partner_id"))
            out.append({
                "external_id": f"odoo_po_{o['id']}",
                "source": "odoo",
                "po_number": o.get("name"),
                "supplier_id": sid,
                "supplier_name": sname,
                "order_date": o.get("date_order"),
                "scheduled_date": o.get("date_planned"),
                "state": o.get("state"),
                "total_amount": o.get("amount_total"),
                "synced_at": datetime.now(UTC).isoformat(),
            })
        return out

    def _transform_suppliers(self, raw_suppliers: list) -> list[dict]:
        return [{
            "external_id": f"odoo_supplier_{s['id']}",
            "source": "odoo",
            "name": s.get("name"),
            "email": s.get("email", ""),
            "phone": s.get("phone", ""),
            "rank": s.get("supplier_rank", 0),
            "synced_at": datetime.now(UTC).isoformat(),
        } for s in raw_suppliers]

    def _transform_locations(self, raw_locations: list) -> list[dict]:
        out = []
        for loc in raw_locations:
            wh_id, wh_name = self._m2o(loc.get("warehouse_id"))
            out.append({
                "external_id": f"odoo_loc_{loc['id']}",
                "source": "odoo",
                "name": loc.get("name"),
                "full_path": loc.get("display_name"),
                "type": loc.get("usage"),
                "warehouse": wh_name,
                "synced_at": datetime.now(UTC).isoformat(),
            })
        return out
