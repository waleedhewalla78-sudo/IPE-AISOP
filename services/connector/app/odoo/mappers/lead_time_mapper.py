"""Odoo 19 lead-time history mapper — PO + incoming picking → cdm_lead_time_history."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.planning_intelligence import LeadTimeHistory
from ipe_shared.models.product import Product
from ipe_shared.models.supplier import Supplier

from app.core.mapper import parse_odoo_datetime

logger = logging.getLogger(__name__)


def _as_date(value: Any) -> date | None:
    dt = parse_odoo_datetime(value)
    if dt is None:
        return None
    return dt.date() if isinstance(dt, datetime) else dt


def compute_lead_time_days(order_date: date | None, receipt_date: date | None) -> int | None:
    if order_date is None or receipt_date is None:
        return None
    return (receipt_date - order_date).days


def compute_lead_time_variance_days(
    expected_date: date | None, receipt_date: date | None
) -> int | None:
    if expected_date is None or receipt_date is None:
        return None
    return (receipt_date - expected_date).days


class LeadTimeMapper:
    """Sync purchase.order + stock.picking (incoming) into cdm_lead_time_history."""

    def __init__(self, client: Any, tenant_id: UUID, session: AsyncSession):
        self.client = client
        self.tenant_id = tenant_id
        self.session = session

    async def sync(self) -> dict[str, Any]:
        try:
            pos = self.client.search_read(
                "purchase.order",
                [("state", "in", ["purchase", "done"])],
                fields=["id", "name", "date_order", "date_planned", "partner_id", "order_line"],
            )
        except Exception as exc:
            logger.error("Lead time PO fetch failed: %s", exc)
            return {"synced": 0, "skipped": 0, "errors": 1, "error": str(exc)}

        synced = 0
        skipped = 0
        for po in pos:
            po_name = po.get("name")
            order_date = _as_date(po.get("date_order"))
            expected_date = _as_date(po.get("date_planned"))
            if order_date is None:
                skipped += 1
                logger.warning("Skipping PO %s — missing date_order", po_name)
                continue

            try:
                pickings = self.client.search_read(
                    "stock.picking",
                    [
                        ("origin", "=", po_name),
                        ("picking_type_code", "=", "incoming"),
                        ("state", "=", "done"),
                    ],
                    fields=["date_done"],
                )
            except Exception as exc:
                logger.warning("Picking fetch failed for PO %s: %s", po_name, exc)
                skipped += 1
                continue

            if not pickings:
                skipped += 1
                continue

            receipt_dates = [_as_date(p.get("date_done")) for p in pickings]
            receipt_dates = [d for d in receipt_dates if d is not None]
            if not receipt_dates:
                skipped += 1
                continue
            receipt_date = min(receipt_dates)

            line_ids = po.get("order_line") or []
            if not line_ids:
                skipped += 1
                continue

            try:
                lines = self.client.read(
                    "purchase.order.line",
                    line_ids if isinstance(line_ids, list) else [line_ids],
                    fields=["product_id", "product_qty", "date_planned"],
                )
            except Exception as exc:
                logger.warning("PO line fetch failed for %s: %s", po_name, exc)
                skipped += 1
                continue

            supplier_id = await self._resolve_supplier(po.get("partner_id"))
            lt_days = compute_lead_time_days(order_date, receipt_date)
            lt_var = compute_lead_time_variance_days(expected_date, receipt_date)

            for line in lines:
                product_id = await self._resolve_product(line.get("product_id"))
                if product_id is None:
                    logger.warning("Skipping PO line — unknown product on %s", po_name)
                    skipped += 1
                    continue

                existing = await self.session.execute(
                    select(LeadTimeHistory).where(
                        LeadTimeHistory.tenant_id == self.tenant_id,
                        LeadTimeHistory.po_erp_id == str(po.get("id")),
                        LeadTimeHistory.product_id == product_id,
                    )
                )
                row = existing.scalar_one_or_none()
                if row:
                    row.order_date = order_date
                    row.expected_date = expected_date
                    row.actual_receipt_date = receipt_date
                    row.lead_time_days = lt_days
                    row.lead_time_variance_days = lt_var
                    row.supplier_id = supplier_id
                else:
                    self.session.add(
                        LeadTimeHistory(
                            tenant_id=self.tenant_id,
                            product_id=product_id,
                            supplier_id=supplier_id,
                            po_erp_id=str(po.get("id")),
                            order_date=order_date,
                            expected_date=expected_date,
                            actual_receipt_date=receipt_date,
                            lead_time_days=lt_days,
                            lead_time_variance_days=lt_var,
                        )
                    )
                synced += 1

        await self.session.flush()
        return {"synced": synced, "skipped": skipped, "errors": 0, "total_pos": len(pos)}

    async def _resolve_product(self, product_ref: Any) -> UUID | None:
        if product_ref in (None, False):
            return None
        erp_id = str(product_ref[0] if isinstance(product_ref, (list, tuple)) else product_ref)
        result = await self.session.execute(
            select(Product).where(
                Product.tenant_id == self.tenant_id,
                Product.erp_source_id == erp_id,
            )
        )
        product = result.scalar_one_or_none()
        return product.id if product else None

    async def _resolve_supplier(self, partner_ref: Any) -> UUID | None:
        if partner_ref in (None, False):
            return None
        erp_id = str(partner_ref[0] if isinstance(partner_ref, (list, tuple)) else partner_ref)
        result = await self.session.execute(
            select(Supplier).where(
                Supplier.tenant_id == self.tenant_id,
                Supplier.erp_source_id == erp_id,
            )
        )
        supplier = result.scalar_one_or_none()
        return supplier.id if supplier else None
