"""Odoo 17 → CDM field mappers for Release 1 sync."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def parse_odoo_datetime(value: Any) -> datetime | None:
    if value is None or value is False:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).replace("T", " ").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(
                text[:19] if fmt.startswith("%Y-%m-%d %H") else text[:10],
                fmt,
            )
            return parsed.replace(tzinfo=UTC)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


ODOO_TO_CDM_PRODUCT = {
    "id": ("erp_source_id", lambda v: str(v)),
    "name": ("name", lambda v: v),
    "default_code": ("internal_ref", lambda v: str(v) if v not in (None, False, "") else None),
    "type": ("source_type", lambda v: {
        "product": "manufactured", "consu": "purchased", "service": "subcontracted",
    }.get(v, "manufactured")),
    "uom_id": ("uom", lambda v: v[1] if isinstance(v, (list, tuple)) else str(v)),
    "standard_price": ("standard_cost", lambda v: float(v) if v else 0),
    "list_price": ("list_price", lambda v: float(v) if v else None),
    "weight": ("weight", lambda v: float(v) if v else None),
    "qty_available": ("qty_available", lambda v: float(v) if v else 0),
}

ODOO_TO_CDM_DEMAND = {
    "id": ("erp_source_id", lambda v: str(v)),
    "product_id": ("product_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_uom_qty": ("quantity", lambda v: float(v)),
    "price_subtotal": ("revenue", lambda v: float(v) if v not in (None, False) else None),
    "scheduled_date": ("required_date", parse_odoo_datetime),
    "order_partner_id": ("customer_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v) if v else None),
    "state": ("status", lambda v: v),
}

ODOO_TO_CDM_SUPPLY = {
    "id": ("erp_source_id", lambda v: str(v)),
    "product_id": ("product_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_qty": ("quantity_ordered", lambda v: float(v)),
    "qty_received": ("quantity_received", lambda v: float(v) if v else 0),
    "date_planned": ("expected_date", parse_odoo_datetime),
    "partner_id": ("supplier_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v) if v else None),
    "state": ("status", lambda v: v),
}

ODOO_TO_CDM_WC = {
    "id": ("erp_source_id", lambda v: str(v)),
    "name": ("name", lambda v: v or "Work Center"),
    "code": ("code", lambda v: v),
    "time_efficiency": ("time_efficiency", lambda v: float(v) if v else 100.0),
}

ODOO_TO_CDM_BOM = {
    "id": ("erp_source_id", lambda v: str(v)),
    "product_id": ("product_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_tmpl_id": ("product_tmpl_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_qty": ("product_qty", lambda v: float(v) if v else 1.0),
    "bom_line_ids": ("bom_line_ids", lambda v: v or []),
    "operation_ids": ("operation_ids", lambda v: v or []),
}

ODOO_TO_CDM_BOM_LINE = {
    "id": ("erp_source_id", lambda v: str(v)),
    "bom_id": ("bom_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_id": ("component_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_qty": ("quantity_per", lambda v: float(v) if v else 1.0),
    "product_uom_id": ("uom", lambda v: v[1] if isinstance(v, (list, tuple)) else str(v)),
}

ODOO_TO_CDM_ROUTING_OP = {
    "id": ("erp_source_id", lambda v: str(v)),
    "bom_id": ("bom_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "sequence": ("sequence", lambda v: int(v) if v is not None else 100),
    "name": ("operation_name", lambda v: v or "Operation"),
    "workcenter_id": ("work_center_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "time_cycle_manual": ("duration_planned_mins", lambda v: float(v) if v else 60.0),
}

ODOO_TO_CDM_PARTNER = {
    "id": ("erp_source_id", lambda v: str(v)),
    "name": ("name", lambda v: v or "Partner"),
    "customer_rank": ("customer_rank", lambda v: int(v or 0)),
    "supplier_rank": ("supplier_rank", lambda v: int(v or 0)),
}

ODOO_MO_STATE_MAP = {
    "draft": "draft",
    "confirmed": "confirmed",
    "progress": "in_progress",
    "to_close": "in_progress",
    "done": "completed",
    "cancel": "cancelled",
}


def map_odoo_mo_state(value: Any) -> str:
    if not value:
        return "draft"
    return ODOO_MO_STATE_MAP.get(str(value), "draft")


ODOO_TO_CDM_MO = {
    "id": ("erp_mo_id", lambda v: str(v)),
    "name": ("mo_name", lambda v: v),
    "product_id": ("product_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "bom_id": ("bom_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v) if v else None),
    "product_qty": ("quantity", lambda v: float(v) if v else 0),
    "date_start": ("planned_start", parse_odoo_datetime),
    "date_finished": ("planned_end", parse_odoo_datetime),
    "date_planned_start": ("planned_start_alt", parse_odoo_datetime),
    "date_planned_finished": ("planned_end_alt", parse_odoo_datetime),
    "state": ("status", map_odoo_mo_state),
    "write_date": ("erp_last_update", parse_odoo_datetime),
}


def normalize_mo_mapped(mapped: dict) -> dict:
    """Odoo 17 uses date_planned_*; Odoo 19 uses date_start/date_finished."""
    if not mapped.get("planned_start") and mapped.get("planned_start_alt"):
        mapped["planned_start"] = mapped["planned_start_alt"]
    if not mapped.get("planned_end") and mapped.get("planned_end_alt"):
        mapped["planned_end"] = mapped["planned_end_alt"]
    mapped.pop("planned_start_alt", None)
    mapped.pop("planned_end_alt", None)
    return mapped


def map_odoo_to_cdm(odoo_record: dict, mapping: dict) -> dict:
    result: dict = {}
    for odoo_field, (cdm_field, transform) in mapping.items():
        if odoo_field in odoo_record:
            try:
                result[cdm_field] = transform(odoo_record[odoo_field])
            except (ValueError, TypeError, KeyError):
                result[cdm_field] = None
    return result
