"""A15 Procurement Execution — MM-execution equivalent.

3-way match (PO ↔ receipt ↔ invoice), receipt confirmation, and invoice
verification / approval routing. Pure-logic core. Odoo PO write-back and live
invoice ingestion are PH1-02 OPEN — this agent evaluates supplied documents and
recommends actions; it does NOT post to a live ERP here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MatchLine:
    line_id: str
    material_id: str
    po_qty: float
    received_qty: float
    invoiced_qty: float
    po_unit_price: float
    invoice_unit_price: float
    qty_match: bool
    price_match: bool
    status: str


def three_way_match(
    *,
    po_id: str = "PO-2026-0451",
    invoice_id: str = "INV-CAIRO-8842",
    lines: list[dict[str, Any]] | None = None,
    qty_tolerance_pct: float = 2.0,
    price_tolerance_pct: float = 3.0,
    auto_approve_ceiling: float = 50_000.0,
) -> dict[str, Any]:
    """Match PO, goods receipt, and invoice line-by-line within tolerances.

    Returns an overall match verdict and a routing recommendation
    (auto_approve / route_for_approval / block_and_investigate).
    """
    lines = (
        lines
        if lines is not None
        else [
            {
                "line_id": "L1",
                "material_id": "RM-CW25",
                "po_qty": 200,
                "received_qty": 200,
                "invoiced_qty": 200,
                "po_unit_price": 12.0,
                "invoice_unit_price": 12.0,
            },
            {
                "line_id": "L2",
                "material_id": "RM-STL10",
                "po_qty": 500,
                "received_qty": 480,
                "invoiced_qty": 500,
                "po_unit_price": 3.5,
                "invoice_unit_price": 3.6,
            },
        ]
    )

    matched: list[MatchLine] = []
    invoice_total = 0.0
    exceptions: list[str] = []

    for ln in lines:
        po_qty = float(ln["po_qty"])
        recv_qty = float(ln["received_qty"])
        inv_qty = float(ln["invoiced_qty"])
        po_price = float(ln["po_unit_price"])
        inv_price = float(ln["invoice_unit_price"])
        invoice_total += inv_qty * inv_price

        qty_dev = abs(inv_qty - recv_qty) / recv_qty * 100 if recv_qty else 100.0
        price_dev = abs(inv_price - po_price) / po_price * 100 if po_price else 100.0
        qty_match = qty_dev <= qty_tolerance_pct
        price_match = price_dev <= price_tolerance_pct

        if qty_match and price_match:
            status = "matched"
        elif not qty_match and not price_match:
            status = "qty_and_price_mismatch"
        elif not qty_match:
            status = "qty_mismatch"
        else:
            status = "price_mismatch"

        if status != "matched":
            exceptions.append(
                f"{ln['line_id']} {ln['material_id']}: {status} "
                f"(qty dev {qty_dev:.1f}%, price dev {price_dev:.1f}%)"
            )

        matched.append(
            MatchLine(
                line_id=ln["line_id"],
                material_id=ln["material_id"],
                po_qty=po_qty,
                received_qty=recv_qty,
                invoiced_qty=inv_qty,
                po_unit_price=po_price,
                invoice_unit_price=inv_price,
                qty_match=qty_match,
                price_match=price_match,
                status=status,
            )
        )

    all_matched = all(m.status == "matched" for m in matched)
    if all_matched and invoice_total <= auto_approve_ceiling:
        routing = "auto_approve"
    elif all_matched:
        routing = "route_for_approval"
    else:
        routing = "block_and_investigate"

    return {
        "agent_id": "A15",
        "capability": "three_way_match",
        "po_id": po_id,
        "invoice_id": invoice_id,
        "invoice_total": round(invoice_total, 2),
        "auto_approve_ceiling": auto_approve_ceiling,
        "all_matched": all_matched,
        "routing": routing,
        "exceptions": exceptions,
        "lines": [m.__dict__ for m in matched],
        "erp_writeback": {
            "live": False,
            "blocker": "PH1-02 live Odoo OPEN — invoice posting not executed",
        },
    }


def confirm_receipt(
    *,
    po_id: str = "PO-2026-0451",
    material_id: str = "RM-CW25",
    ordered_qty: float = 200,
    received_qty: float = 200,
    inspection_passed: bool = True,
) -> dict[str, Any]:
    """Record a goods-receipt confirmation with over/under-delivery flag."""
    variance = round(received_qty - ordered_qty, 2)
    if not inspection_passed:
        status = "rejected_inspection"
    elif variance < 0:
        status = "partial_receipt"
    elif variance > 0:
        status = "over_receipt"
    else:
        status = "confirmed"
    return {
        "agent_id": "A15",
        "capability": "receipt_confirmation",
        "po_id": po_id,
        "material_id": material_id,
        "ordered_qty": ordered_qty,
        "received_qty": received_qty,
        "variance": variance,
        "inspection_passed": inspection_passed,
        "status": status,
    }


class ProcurementExecution:
    """A15 facade."""

    agent_id = "A15"
    name = "Procurement Execution"

    def match(self, **kwargs: Any) -> dict[str, Any]:
        return three_way_match(**kwargs)

    def receipt(self, **kwargs: Any) -> dict[str, Any]:
        return confirm_receipt(**kwargs)
