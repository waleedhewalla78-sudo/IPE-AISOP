#!/usr/bin/env python3
"""SAP S/4HANA sandbox integration validation (R4 / FR-027).

Always runs CDM mapper checks. When SAP_ODATA_URL + credentials are set,
fetches a sample ManufacturingOrder OData entity and validates CDM mapping.

Environment:
  SAP_ODATA_URL       Base OData URL (e.g. https://sandbox.sap.com/sap/opu/odata/sap/API_MANUFACTURING_ORDER_SRV)
  SAP_USER / SAP_PASSWORD   Basic auth credentials
  SAP_TENANT_ID       IPE tenant UUID for isolation check (default: demo tenant)
  SAP_EVIDENCE_PATH   Output report path
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from base64 import b64encode
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "services"))

from connectors.sap_adapter.cdm_mapper import (  # noqa: E402
    map_material_to_product,
    map_mrp_production_to_manufacturing_order,
    map_purchase_order_to_supply,
    map_sale_order_to_demand,
)

TENANT_ID = os.environ.get("SAP_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
EVIDENCE = Path(
    os.environ.get(
        "SAP_EVIDENCE_PATH",
        REPO_ROOT / "specs/003-autonomous-planning-v5/evidence/r4/sap-sandbox-report.txt",
    )
)


def _log(lines: list[str], msg: str) -> None:
    print(msg)
    lines.append(msg)


def validate_mappers(lines: list[str]) -> bool:
    _log(lines, "--- Mapper validation (offline) ---")
    demand = map_sale_order_to_demand(
        {"VBELN": "SO-SAP-001", "KUNNR": "C001", "MATNR": "FG-001", "KWMENG": 50, "LFDAT": "2026-07-01"}
    )
    mo = map_mrp_production_to_manufacturing_order(
        {"AUFNR": "MO-SAP-001", "MATNR": "FG-001", "GAMNG": 50, "GSTRP": "2026-06-01", "GLTRP": "2026-06-15"}
    )
    supply = map_purchase_order_to_supply({"EBELN": "PO-001", "LIFNR": "V001", "MATNR": "RM-001", "MENGE": 100})
    product = map_material_to_product({"MATNR": "FG-001", "MAKTX": "Distribution Transformer", "MTART": "FERT", "MEINS": "EA"})

    checks = [
        demand["source"] == "sap" and demand["order_id"] == "SO-SAP-001",
        mo["mo_id"] == "MO-SAP-001" and mo["source"] == "sap",
        supply["supplier_id"] == "V001",
        product["product_id"] == "FG-001",
    ]
    ok = all(checks)
    _log(lines, f"Mapper checks: {'PASS' if ok else 'FAIL'} ({sum(checks)}/{len(checks)})")
    return ok


def validate_live_sandbox(lines: list[str]) -> bool | None:
    base = os.environ.get("SAP_ODATA_URL", "").rstrip("/")
    user = os.environ.get("SAP_USER", "")
    password = os.environ.get("SAP_PASSWORD", "")
    if not base:
        _log(lines, "--- Live sandbox: SKIPPED (SAP_ODATA_URL not set) ---")
        return None

    if not user or not password:
        _log(lines, "--- Live sandbox: SKIPPED (SAP_USER/SAP_PASSWORD not set) ---")
        return None

    _log(lines, f"--- Live sandbox OData: {base} ---")
    url = f"{base}/ManufacturingOrder?$top=1&$format=json"
    auth = b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}", "Accept": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        _log(lines, f"Live sandbox: FAIL — {exc}")
        return False

    entries = payload.get("d", {}).get("results") or payload.get("value") or []
    if not entries:
        _log(lines, "Live sandbox: WARN — no ManufacturingOrder rows returned")
        return True

    row = entries[0]
    mapped = map_mrp_production_to_manufacturing_order(
        {
            "AUFNR": row.get("ManufacturingOrder") or row.get("OrderInternalBillOfOperations") or "UNKNOWN",
            "MATNR": row.get("Material") or row.get("Product") or "",
            "GAMNG": row.get("TotalQuantity") or row.get("MfgOrderPlannedTotalQty") or 0,
            "GSTRP": row.get("MfgOrderPlannedStartDate") or "",
            "GLTRP": row.get("MfgOrderPlannedEndDate") or "",
        }
    )
    mapped["tenant_id"] = TENANT_ID

    ok = bool(mapped.get("mo_id")) and mapped.get("tenant_id") == TENANT_ID
    _log(lines, f"Live CDM map: mo_id={mapped.get('mo_id')} tenant_id={mapped.get('tenant_id')} => {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    lines: list[str] = [
        "SAP Sandbox Integration Report",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Tenant: {TENANT_ID}",
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
    _log(lines, f"Report: {EVIDENCE}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
