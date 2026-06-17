"""D365 (Dataverse) to IPE CDM Mapper.

Transforms Microsoft Dataverse entities (salesorders, workorders) into the
IPE Canonical Data Model entities.
"""

from datetime import datetime
from uuid import UUID, uuid4

SALES_ORDER_STATUS_MAP = {
    1: "new",
    2: "confirmed",
    3: "completed",
    4: "cancelled",
}

WORK_ORDER_STATUS_MAP = {
    1: "draft",
    2: "planned",
    3: "in_progress",
    4: "completed",
    5: "cancelled",
}


def map_sales_order_to_demand_line(row: dict, tenant_id: str) -> dict:
    """Map D365 Dataverse salesorder/salesorderdetail to cdm_demand_line.

    Expected input keys:
        - salesorderid (GUID)
        - salesorderdetailid (GUID)
        - name / ordernumber
        - productid (product GUID)
        - quantity
        - uomname / uomid
        - requestdeliveryby (datetime)
        - customerid (account GUID)
        - totalamount
        - statecode (int: 0=Active, 1=Submitted, 2=Canceled, 3=Fulfilled)
        - createdon (datetime)
    Returns:
        dict matching the IPE cdm_demand_line schema.
    """
    erp_id = row.get("salesorderdetailid") or row.get("salesorderid", "")
    qty = float(row.get("quantity", 0) or 0)
    req_date_str = row.get("requestdeliveryby", "")
    req_date = datetime.fromisoformat(req_date_str.replace("Z", "+00:00")) if req_date_str else datetime.utcnow()
    state = row.get("statecode", 0)
    status = SALES_ORDER_STATUS_MAP.get(state + 1, "new")

    return {
        "id": uuid4(),
        "tenant_id": UUID(tenant_id),
        "erp_source_id": str(erp_id),
        "erp_source_type": "d365_sales_order",
        "product_erp_id": str(row.get("productid", "")),
        "quantity": qty,
        "uom": row.get("uomname", "unit"),
        "required_date": req_date,
        "demand_type": "MTO",
        "customer_erp_id": str(row.get("customerid", "")),
        "customer_tier": 3,
        "margin_pct": None,
        "penalty_cost": 0,
        "priority_score": 0,
        "status": status,
        "created_at": datetime.utcnow(),
    }


def map_work_order_to_cdm(row: dict, tenant_id: str, mo_erp_id: str) -> dict:
    """Map D365 Dataverse workorder to cdm_work_order.

    Expected input keys:
        - workorderid (GUID)
        - workordertype (int)
        - serviceaddress (string)
        - productid (product GUID)
        - estimateddurationminutes (int)
        - startdatetime (datetime)
        - enddatetime (datetime)
        - statecode (int: 0=Scheduled, 1=InProgress, 2=Completed, 3=Canceled)
        - msdyn_systemstatus (int)
    Returns:
        dict matching the IPE cdm_work_order schema.
    """
    op_id = str(row.get("workorderid", ""))
    duration = float(row.get("estimateddurationminutes", 0) or 0)
    start_str = row.get("startdatetime", "")
    end_str = row.get("enddatetime", "")
    start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00")) if start_str else None
    end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else None
    state = row.get("statecode", 0)
    status = WORK_ORDER_STATUS_MAP.get(state + 1, "pending")

    return {
        "id": uuid4(),
        "tenant_id": UUID(tenant_id),
        "mo_erp_id": mo_erp_id,
        "operation_erp_id": op_id,
        "sequence": 1,
        "work_center_erp_id": str(row.get("serviceaddress", "")),
        "planned_start": start_date,
        "planned_end": end_date,
        "duration_planned_mins": duration,
        "status": status,
        "created_at": datetime.utcnow(),
    }
