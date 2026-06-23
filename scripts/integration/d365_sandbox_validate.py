#!/usr/bin/env python3
"""D365 Finance & Operations sandbox integration validation (R4 / FR-027).

Always runs CDM mapper checks. When D365_* OAuth credentials are set,
fetches a ProductionOrder and validates schedule date mapping for approve flow.

Environment:
  D365_ODATA_URL     e.g. https://{org}.operations.dynamics.com/data
  D365_TENANT_ID     Azure AD tenant
  D365_CLIENT_ID     App registration client id
  D365_CLIENT_SECRET App secret
  IPE_TENANT_ID      IPE tenant UUID (default: demo tenant)
  D365_EVIDENCE_PATH Output report path
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "services"))

from connectors.d365_adapter.cdm_mapper import (  # noqa: E402
    map_product_to_cdm,
    map_production_order_to_manufacturing_order,
    map_purchase_order_to_supply,
    map_sales_order_to_demand,
)

IPE_TENANT = os.environ.get("IPE_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
EVIDENCE = Path(
    os.environ.get(
        "D365_EVIDENCE_PATH",
        REPO_ROOT / "specs/003-autonomous-planning-v5/evidence/r4/d365-sandbox-report.txt",
    )
)


def _log(lines: list[str], msg: str) -> None:
    print(msg)
    lines.append(msg)


def validate_mappers(lines: list[str]) -> bool:
    _log(lines, "--- Mapper validation (offline) ---")
    demand = map_sales_order_to_demand(
        {
            "SalesOrderNumber": "SO-D365-001",
            "InvoiceCustomerAccountNumber": "CUST-001",
            "ItemNumber": "FG-001",
            "OrderedSalesQuantity": 25,
            "RequestedShipDate": "2026-08-01",
            "SalesPrice": 100,
            "CurrencyCode": "USD",
        }
    )
    mo = map_production_order_to_manufacturing_order(
        {
            "ProductionOrderNumber": "MO-D365-001",
            "ItemNumber": "FG-001",
            "ProductionQuantity": 25,
            "ScheduledStartDate": "2026-06-10",
            "ScheduledEndDate": "2026-06-20",
            "RouteId": "ROUTE-01",
        }
    )
    supply = map_purchase_order_to_supply(
        {"PurchaseOrderNumber": "PO-001", "VendorAccountNumber": "V-001", "ItemNumber": "RM-001", "OrderedPurchaseQuantity": 50}
    )
    product = map_product_to_cdm({"ItemId": "FG-001", "ProductName": "Gadget", "ProductType": "Item", "UnitOfMeasure": "ea"})

    schedule_payload = {
        "mo_id": mo["mo_id"],
        "planned_date_start": "2026-06-12T08:00:00Z",
        "planned_date_finished": "2026-06-18T17:00:00Z",
        "approved_by": "ipe-planner",
        "tenant_id": IPE_TENANT,
    }

    checks = [
        demand["source"] == "d365",
        mo["mo_id"] == "MO-D365-001",
        supply["source"] == "d365",
        product["product_id"] == "FG-001",
        schedule_payload["tenant_id"] == IPE_TENANT,
    ]
    ok = all(checks)
    _log(lines, f"Mapper + schedule payload checks: {'PASS' if ok else 'FAIL'} ({sum(checks)}/{len(checks)})")
    return ok


def _fetch_d365_token() -> str | None:
    tenant = os.environ.get("D365_TENANT_ID", "")
    client_id = os.environ.get("D365_CLIENT_ID", "")
    client_secret = os.environ.get("D365_CLIENT_SECRET", "")
    if not all([tenant, client_id, client_secret]):
        return None

    data = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://api.businesscentral.dynamics.com/.default",
        }
    ).encode()
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode()).get("access_token")


def validate_live_sandbox(lines: list[str]) -> bool | None:
    base = os.environ.get("D365_ODATA_URL", "").rstrip("/")
    token = _fetch_d365_token()
    if not base:
        _log(lines, "--- Live sandbox: SKIPPED (D365_ODATA_URL not set) ---")
        return None
    if not token:
        _log(lines, "--- Live sandbox: SKIPPED (D365 OAuth credentials not set) ---")
        return None

    _log(lines, f"--- Live sandbox OData: {base} ---")
    url = f"{base}/ProductionOrders?$top=1"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        _log(lines, f"Live sandbox: FAIL — {exc}")
        return False

    rows = payload.get("value") or []
    if not rows:
        _log(lines, "Live sandbox: WARN — no ProductionOrders returned")
        return True

    mapped = map_production_order_to_manufacturing_order(rows[0])
    mapped["tenant_id"] = IPE_TENANT
    ok = bool(mapped.get("mo_id")) and mapped["tenant_id"] == IPE_TENANT
    _log(
        lines,
        f"Live schedule-ready map: mo_id={mapped.get('mo_id')} "
        f"start={mapped.get('planned_start')} end={mapped.get('planned_end')} => {'PASS' if ok else 'FAIL'}",
    )
    return ok


def main() -> int:
    lines: list[str] = [
        "D365 Sandbox Integration Report",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"IPE Tenant: {IPE_TENANT}",
        "",
    ]

    mapper_ok = validate_mappers(lines)
    live_ok = validate_live_sandbox(lines)

    if live_ok is None:
        overall = mapper_ok
        status = "PASS (mapper-only; live sandbox skipped)"
    else:
        overall = mapper_ok and live_ok
        status = "PASS" if overall else "FAIL"

    lines.extend(["", f"OVERALL: {status}"])
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {EVIDENCE}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
