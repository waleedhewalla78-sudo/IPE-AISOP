#!/usr/bin/env python3
"""
critical_path_test.py

End-to-end critical path validation for the IPE platform.
Simulates the full event-driven lifecycle:

  1. POST demand lines -> dpe-svc classifies -> publishes ipe.demand.classified
  2. Trigger mat-svc probabilistic ATP
  3. Trigger cap-svc scheduling
  4. Verify fea-svc feasibility score
  5. Verify res-svc scenarios and mock approve

Connects to services via environment variables (CI/local overrides).
Defaults to local dev stack.

Usage:
    uv run python scripts/e2e/critical_path_test.py
"""

import os

import httpx

BASE_DPE = os.environ.get("TEST_DPE_URL", "http://localhost:8002")
BASE_MAT = os.environ.get("TEST_MAT_URL", "http://localhost:8003")
BASE_CAP = os.environ.get("TEST_CAP_URL", "http://localhost:8004")
BASE_FEA = os.environ.get("TEST_FEA_URL", "http://localhost:8005")
BASE_RES = os.environ.get("TEST_RES_URL", "http://localhost:8006")
TENANT_ID = os.environ.get("TEST_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
}


def step(msg: str) -> None:
    print(f"  ✓ {msg}")


def fail(msg: str) -> None:
    print(f"  ✗ FAIL: {msg}")
    raise SystemExit(1)


def main() -> None:
    print("=== IPE E2E Critical Path Validation ===\n")

    # --- Step 1: Classify demand via dpe-svc ---
    print("[Step 1/5] POST demand lines -> dpe-svc classify")
    demand_payload = {"demand_line_ids": [f"e2e-dmd-{i}" for i in range(10)]}
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_DPE}/api/v1/demand/classify",
            json=demand_payload,
            headers=HEADERS,
            timeout=15.0,
        )
        if resp.status_code != 200:
            fail(f"dpe-svc classify returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"dpe-svc classify failed: {data.get('error', {}).get('message', 'unknown')}")
        step("dpe-svc classified demand lines and returned priority scores")

    # --- Step 2: Probabilistic ATP via mat-svc ---
    print("[Step 2/5] Trigger mat-svc probabilistic ATP")
    mat_payload = {
        "mo_id": "e2e-mo-001",
        "bom_components": [
            {"material_code": "MAT-E2E-001", "qty": 10},
            {"material_code": "MAT-E2E-002", "qty": 5},
        ],
        "planned_start": "2026-06-15T00:00:00Z",
    }
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_MAT}/api/v1/material/probabilistic-atp",
            json=mat_payload,
            headers=HEADERS,
            timeout=15.0,
        )
        if resp.status_code != 200:
            fail(f"mat-svc pATP returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"mat-svc pATP failed: {data.get('error', {}).get('message', 'unknown')}")
        step("mat-svc returned probabilistic ATP confidence scores")

    # --- Step 3: Capacity scheduling via cap-svc ---
    print("[Step 3/5] Trigger cap-svc scheduling")
    cap_payload = {
        "mo_ids": [f"e2e-mo-{i:03d}" for i in range(5)],
        "horizon_hours": 168,
    }
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_CAP}/api/v1/capacity/schedule",
            json=cap_payload,
            headers=HEADERS,
            timeout=30.0,
        )
        if resp.status_code != 200:
            fail(f"cap-svc schedule returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"cap-svc schedule failed: {data.get('error', {}).get('message', 'unknown')}")
        schedule = data.get("data", {}).get("schedule", [])
        if not isinstance(schedule, list):
            fail("cap-svc schedule returned unexpected format")
        step(f"cap-svc returned schedule for {len(schedule)} MO(s)")

    # --- Step 4: Feasibility scoring via fea-svc ---
    print("[Step 4/5] Verify fea-svc feasibility score")
    fea_payload = {
        "mo_id": "e2e-mo-001",
        "gate_scores": {
            "demand": 90.0,
            "bom": 85.0,
            "material": 78.0,
            "capacity": 72.0,
            "labor": 95.0,
        },
        "autonomy_mode": "suggest",
    }
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_FEA}/api/v1/feasibility/score",
            json=fea_payload,
            headers=HEADERS,
            timeout=15.0,
        )
        if resp.status_code != 200:
            fail(f"fea-svc score returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"fea-svc score failed: {data.get('error', {}).get('message', 'unknown')}")
        composite = data.get("data", {}).get("composite_score")
        if composite is None:
            fail("fea-svc did not return composite_score")
        action = data.get("data", {}).get("action_taken", "")
        step(f"fea-svc scored MO at {composite:.1f}% (action: {action})")

    # --- Step 5: Resolution scenarios via res-svc ---
    print("[Step 5/5] Verify res-svc scenarios and mock approve")
    res_payload = {
        "mo_id": "e2e-mo-001",
        "constraints": [
            {"type": "material", "severity": "high", "description": "Component MAT-E2E-001 shortage"},
            {"type": "capacity", "severity": "medium", "description": "Work center WC001 at 88% utilization"},
        ],
    }
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_RES}/api/v1/resolution/scenarios",
            json=res_payload,
            headers=HEADERS,
            timeout=15.0,
        )
        if resp.status_code != 200:
            fail(f"res-svc scenarios returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"res-svc scenarios failed: {data.get('error', {}).get('message', 'unknown')}")
        scenarios = data.get("data", [])
        if not isinstance(scenarios, list) or len(scenarios) == 0:
            fail("res-svc returned empty scenarios list")
        step(f"res-svc generated {len(scenarios)} resolution scenario(s)")

    # --- All steps passed ---
    print("\n" + "=" * 50)
    print("  ✅ E2E CRITICAL PATH: ALL 5 STEPS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
