"""SAP ERP to IPE CDM Mapper.

Transforms native SAP schema objects (VBAK/VBAP, AFVC/AFVV) into the
IPE Canonical Data Model entities.
"""

from datetime import datetime
from uuid import UUID, uuid4

SALES_ORDER_STATUS_MAP = {
    "A": "new",
    "B": "confirmed",
    "C": "completed",
    "D": "cancelled",
}

PRODUCTION_ORDER_STATUS_MAP = {
    "CRTD": "draft",
    "REL": "planned",
    "PCNF": "in_progress",
    "DLV": "completed",
    "TECO": "completed",
    "CLSD": "completed",
}


def map_vbak_vbap_to_demand_line(row: dict, tenant_id: str) -> dict:
    """Map SAP VBAK (header) + VBAP (item) to cdm_demand_line.

    Expected input keys:
        - vbeln (sales order number)
        - posnr (item number)
        - matnr (material number)
        - kwmeng (order quantity)
        - vrkme (unit of measure)
        - edatu / bnddt (requested delivery date)
        - kunnr (customer number)
        - waerk / netwr (currency / net value)
        - audat (document date)
        - vkorg (sales organization)
        - vtweg (distribution channel)
        - spart (division)
        - abgru (rejection reason — indicates cancelled)
    Returns:
        dict matching the IPE cdm_demand_line schema.
    """
    erp_id = f"{row.get('vbeln', '')}-{row.get('posnr', '')}"
    qty = float(row.get("kwmeng", 0) or 0)
    req_date_str = row.get("edatu") or row.get("bnddt", "")
    req_date = datetime.strptime(req_date_str, "%Y-%m-%d") if req_date_str else datetime.utcnow()
    status = SALES_ORDER_STATUS_MAP.get(row.get("abgru", "B"), "new")
    if row.get("abgru"):
        status = "cancelled"

    return {
        "id": uuid4(),
        "tenant_id": UUID(tenant_id),
        "erp_source_id": erp_id,
        "erp_source_type": "sap_sales_order",
        "product_erp_id": row.get("matnr", ""),
        "quantity": qty,
        "uom": row.get("vrkme", "unit"),
        "required_date": req_date,
        "demand_type": "MTO",
        "customer_erp_id": row.get("kunnr", ""),
        "customer_tier": 3,
        "margin_pct": None,
        "penalty_cost": 0,
        "priority_score": 0,
        "status": status,
        "created_at": datetime.utcnow(),
    }


def map_afvc_afvv_to_work_order(row: dict, tenant_id: str, mo_erp_id: str) -> dict:
    """Map SAP AFVC (operation) + AFVV (operation qty/date) to cdm_work_order.

    Expected input keys:
        - aufpl (internal order number)
        - aplzl (internal counter for the operation)
        - vornr (operation number)
        - arbid (work center ID)
        - steus (control key)
        - ltxa1 (operation short text)
        - arbeit (standard operation time in work unit)
        - vge01 (basic start date)
        - vge02 (basic end date)
        - meinh (unit of measure for work)
        - anzkap (number of capacity units)
    Returns:
        dict matching the IPE cdm_work_order schema.
    """
    op_id = row.get("vornr", "")
    wc_erp_id = row.get("arbid", "")
    work_raw = float(row.get("arbeit", 0) or 0)
    unit = row.get("meinh", "MIN")
    start_str = row.get("vge01", "")
    end_str = row.get("vge02", "")
    start_date = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
    end_date = datetime.strptime(end_str, "%Y-%m-%d") if end_str else None

    duration_minutes = work_raw if unit == "MIN" else work_raw * 60

    return {
        "id": uuid4(),
        "tenant_id": UUID(tenant_id),
        "mo_erp_id": mo_erp_id,
        "operation_erp_id": op_id,
        "sequence": int(op_id) if op_id.isdigit() else 0,
        "work_center_erp_id": wc_erp_id,
        "planned_start": start_date,
        "planned_end": end_date,
        "duration_planned_mins": duration_minutes,
        "status": "pending",
        "created_at": datetime.utcnow(),
    }
