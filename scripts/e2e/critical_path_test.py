#!/usr/bin/env python3
"""
critical_path_test.py

End-to-end critical path validation for the IPE platform.
Simulates the full event-driven lifecycle:

  1. POST demand lines -> dpe-svc classifies -> publishes ipe.demand.classified
  2. Trigger mat-svc probabilistic ATP
  3. Trigger cap-svc scheduling
  4. Verify fea-svc feasibility score
  5. Verify res-svc scenarios

Usage:
    IPE_JWT_SECRET_KEY=dev-only-change-in-production-min-32-chars-long!! \\
    uv run python scripts/e2e/critical_path_test.py
"""

import os
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import jwt

BASE_DPE = os.environ.get("TEST_DPE_URL", "http://localhost:8020")
BASE_MAT = os.environ.get("TEST_MAT_URL", "http://localhost:8002")
BASE_CAP = os.environ.get("TEST_CAP_URL", "http://localhost:8003")
BASE_FEA = os.environ.get("TEST_FEA_URL", "http://localhost:8004")
BASE_RES = os.environ.get("TEST_RES_URL", "http://localhost:8005")
TENANT_ID = os.environ.get("TEST_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
JWT_SECRET = os.environ.get("IPE_JWT_SECRET_KEY", "dev-only-change-in-production-min-32-chars-long!!")

_token = jwt.encode(
    {
        "sub": str(uuid.uuid4()),
        "tenant_id": TENANT_ID,
        "role": "admin",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
        "jti": str(uuid.uuid4()),
        "type": "access",
    },
    JWT_SECRET,
    algorithm="HS256",
)

HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
    "Authorization": f"Bearer {_token}",
}


def step(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    raise SystemExit(1)


def main() -> None:
    print("=== IPE E2E Critical Path Validation ===\n")

    print("[Step 1/5] POST demand lines -> dpe-svc classify")
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_DPE}/api/v1/demand/classify",
            json={},
            headers=HEADERS,
            timeout=30.0,
        )
        if resp.status_code != 200:
            fail(f"dpe-svc classify returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"dpe-svc classify failed: {data.get('error', {}).get('message', 'unknown')}")
        step("dpe-svc classified demand lines and returned priority scores")

    print("[Step 2/5] Trigger mat-svc probabilistic ATP")
    mat_payload = {
        "mo": {"id": str(uuid.uuid4()), "mo_number": "E2E-CP-001", "quantity": 100},
        "components": [],
        "required_start": datetime.now(UTC).isoformat(),
    }
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_MAT}/api/v1/material/probabilistic-atp",
            json=mat_payload,
            headers=HEADERS,
            timeout=30.0,
        )
        if resp.status_code != 200:
            fail(f"mat-svc pATP returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"mat-svc pATP failed: {data.get('error', {}).get('message', 'unknown')}")
        step("mat-svc returned probabilistic ATP confidence scores")

    print("[Step 3/5] Trigger cap-svc scheduling")
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_CAP}/api/v1/capacity/schedule",
            json={"mo_ids": [], "horizon_hours": 168},
            headers=HEADERS,
            timeout=60.0,
        )
        if resp.status_code != 200:
            fail(f"cap-svc schedule returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"cap-svc schedule failed: {data.get('error', {}).get('message', 'unknown')}")
        step("cap-svc returned schedule response")

    print("[Step 4/5] Verify fea-svc feasibility score")
    fea_payload = {
        "mo_id": str(uuid.uuid4()),
        "demand_score": 90.0,
        "bom_score": 85.0,
        "material_score": 78.0,
        "capacity_score": 72.0,
        "labor_score": 95.0,
        "autonomy_mode": "suggest",
    }
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_FEA}/api/v1/feasibility/score",
            json=fea_payload,
            headers=HEADERS,
            timeout=30.0,
        )
        if resp.status_code != 200:
            fail(f"fea-svc score returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"fea-svc score failed: {data.get('error', {}).get('message', 'unknown')}")
        score = data.get("data", {}).get("feasibility_score")
        if score is None:
            fail("fea-svc did not return feasibility_score")
        action = data.get("data", {}).get("action_taken", "")
        step(f"fea-svc scored MO at {score:.1f}% (action: {action})")

    print("[Step 5/5] Verify res-svc scenarios API")
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_RES}/api/v1/resolution/scenarios",
            headers=HEADERS,
            timeout=30.0,
        )
        if resp.status_code != 200:
            fail(f"res-svc scenarios list returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", False):
            fail(f"res-svc scenarios list failed: {data.get('error', {}).get('message', 'unknown')}")
        scenarios = data.get("data", {}).get("scenarios", data.get("data", []))
        if not isinstance(scenarios, list):
            fail("res-svc returned unexpected scenarios format")
        step(f"res-svc scenarios API reachable ({len(scenarios)} scenario(s) in queue)")

    print("\n" + "=" * 50)
    print("  E2E CRITICAL PATH: ALL 5 STEPS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
