ODOO_TO_CDM_PRODUCT = {
    "id": ("erp_source_id", lambda v: str(v)),
    "name": ("name", lambda v: v),
    "default_code": ("internal_ref", lambda v: v),
    "type": ("source_type", lambda v: {
        "product": "manufactured", "consu": "purchased", "service": "subcontracted",
    }.get(v, "manufactured")),
    "uom_id": ("uom", lambda v: v[1] if isinstance(v, (list, tuple)) else str(v)),
    "standard_price": ("standard_cost", lambda v: float(v) if v else 0),
    "lead_time": ("lead_time_days", lambda v: int(v) if v else 0),
}

ODOO_TO_CDM_BOM = {
    "id": ("erp_source_id", lambda v: str(v)),
    "bom_line_ids": ("_bom_lines", lambda v: v if isinstance(v, list) else []),
}

ODOO_TO_CDM_DEMAND = {
    "id": ("erp_source_id", lambda v: str(v)),
    "product_id": ("product_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_uom_qty": ("quantity", lambda v: float(v)),
    "date_deadline": ("required_date", lambda v: v),
    "state": ("status", lambda v: v),
}

ODOO_TO_CDM_SUPPLY = {
    "id": ("erp_source_id", lambda v: str(v)),
    "product_id": ("product_erp_id", lambda v: str(v[0]) if isinstance(v, (list, tuple)) else str(v)),
    "product_qty": ("quantity_ordered", lambda v: float(v)),
    "date_planned": ("expected_date", lambda v: v),
    "state": ("status", lambda v: v),
}


def map_odoo_to_cdm(odoo_record: dict, mapping: dict) -> dict:
    result: dict = {}
    for odoo_field, (cdm_field, transform) in mapping.items():
        if odoo_field in odoo_record:
            try:
                result[cdm_field] = transform(odoo_record[odoo_field])
            except (ValueError, TypeError, KeyError):
                result[cdm_field] = None
    return result
