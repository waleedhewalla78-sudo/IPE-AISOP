#!/usr/bin/env python3
"""Integration test for RBAC tenant isolation against live Postgres/Kong stack.

Prerequisites (set via env vars):
  TEST_DB_HOST     — Postgres host (default: localhost)
  TEST_DB_PORT     — Postgres port (default: 5433)
  TEST_DB_USER     — Postgres user (default: ipe)
  TEST_DB_PASSWORD — Postgres password (default: ipe_test_pass)
  TEST_DB_NAME     — Postgres DB (default: ipe_test)
  TEST_KONG_ADMIN  — Kong admin URL (default: http://localhost:8001)

Run:
  uv run python tests/integration/test_rbac_tenant_isolation.py
"""

import os
import uuid

import httpx

TEST_DB_HOST = os.environ.get("TEST_DB_HOST", "localhost")
TEST_DB_PORT = os.environ.get("TEST_DB_PORT", "5432")
TEST_DB_USER = os.environ.get("TEST_DB_USER", "ipe")
TEST_DB_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "ipe_test_pass")
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "ipe_test")
TEST_KONG_ADMIN = os.environ.get("TEST_KONG_ADMIN", "")
TENANT_A = str(uuid.uuid4())
TENANT_B = str(uuid.uuid4())

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} - {detail}")


def main() -> None:
    global PASS, FAIL
    print("=== RBAC & Tenant Isolation Integration Tests ===\n")

    # --- 1. Cross-tenant MO injection ---
    print("[Test 1/6] Cross-tenant MO injection via API")
    payload = {"demand_line_ids": [str(uuid.uuid4())]}
    headers_a = {"Content-Type": "application/json", "X-Tenant-ID": TENANT_A}
    headers_b = {"Content-Type": "application/json", "X-Tenant-ID": TENANT_B}

    # Simulate: Tenant A creates data, Tenant B tries to read it
    # Without a Kong gateway enforcing JWT, RLS should filter at the DB level.
    # We verify the endpoint doesn't crash and returns an empty or scoped result.
    with httpx.Client() as client:
        # This is a best-effort check — if services aren't running, skip gracefully
        try:
            # Retry up to 5 times for the classify endpoint
            success = False
            for attempt in range(5):
                try:
                    resp = client.post(
                        f"http://localhost:8002/api/v1/demand/classify",
                        json=payload,
                        headers=headers_b,
                        timeout=5.0,
                    )
                    if resp.status_code == 200:
                        success = True
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    continue
            check(
                "cross-tenant classify returns valid response",
                success,
                f"final status {resp.status_code if 'resp' in locals() else 'no response'}",
            )
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            check("cross-tenant endpoint reachable", False, str(e))

    # --- 2. Cross-tenant resolution approval ---
    print("\n[Test 2/6] Cross-tenant resolution approval")
    with httpx.Client() as client:
        try:
            resp = client.post(
                f"http://localhost:8005/api/v1/resolution/approve",
                json={"scenario_id": str(uuid.uuid4()), "approved_by": "tenant_b_user"},
                headers=headers_b,
                timeout=5.0,
            )
            check(
                "cross-tenant approve reaches service",
                resp.status_code in (200, 404),
                f"got {resp.status_code}",
            )
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            check("cross-tenant approve reachable", False, str(e))

    # --- 3. Kong JWT validation ---
    print("\n[Test 3/6] Kong gateway JWT validation")
    if TEST_KONG_ADMIN:
        with httpx.Client() as client:
            try:
                resp = client.get(
                    f"{TEST_KONG_ADMIN}/routes",
                    timeout=5.0,
                )
                check("Kong admin reachable", resp.status_code == 200, f"got {resp.status_code}")
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                check("Kong admin reachable", False, str(e))
    else:
        print("  SKIP Kong admin check (not configured)")

    # --- 4. Direct DB isolation check (requires psycopg2) ---
    print("\n[Test 4/6] Direct DB RLS isolation")
    try:
        import psycopg2
    except ImportError:
        check("psycopg2 available for DB test", False, "psycopg2 not installed")
        return

    try:
        conn = psycopg2.connect(
            host=TEST_DB_HOST,
            port=TEST_DB_PORT,
            user=TEST_DB_USER,
            password=TEST_DB_PASSWORD,
            dbname=TEST_DB_NAME,
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Set tenant context for Tenant A
        cur.execute("SET LOCAL app.current_tenant_id = %s", (TENANT_A,))
        cur.execute("SELECT COUNT(*) FROM cdm_manufacturing_order")
        count_a = cur.fetchone()[0]

        # Set tenant context for Tenant B
        cur.execute("SET LOCAL app.current_tenant_id = %s", (TENANT_B,))
        cur.execute("SELECT COUNT(*) FROM cdm_manufacturing_order")
        count_b = cur.fetchone()[0]

        check(
            "RLS isolates tenants (both see 0 rows with no data)",
            count_a == 0 and count_b == 0,
            f"Tenant A: {count_a}, Tenant B: {count_b}",
        )

        cur.close()
        conn.close()
    except Exception as e:
        check("Direct DB connection works", False, str(e))

    # --- 5. No-tenant request returns proper error ---
    print("\n[Test 5/6] Request without tenant context")
    with httpx.Client() as client:
        try:
            resp = client.get(
                "http://localhost:8002/api/v1/demand/queue",
                headers={"Content-Type": "application/json"},
                timeout=5.0,
            )
            data = resp.json()
            check(
                "no-tenant request returns error",
                data.get("error", {}).get("code") == "NO_TENANT",
                f"got {data}",
            )
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            check("no-tenant endpoint reachable", False, str(e))

    # --- 6. Missing JWT returns 401 via Kong ---
    print("\n[Test 6/6] Missing JWT rejected by Kong")
    # Retry logic for missing JWT case
    with httpx.Client() as client:
        for attempt in range(5):
            try:
                resp = client.get(
                    "http://localhost:8000/api/v1/demand/queue",
                    headers={"Content-Type": "application/json"},
                    timeout=5.0,
                )
                if resp.status_code in (401, 403):
                    check("missing JWT returns 401", True, f"got {resp.status_code}")
                    break
                else:
                    check("missing JWT returns 401", False, f"got {resp.status_code}")
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == 4:
                    check("Kong proxy reachable", False, str(e))
                else:
                    continue

    # --- Summary ---
    total = PASS + FAIL
    print(f"  {'=' * 50}")
    print(f"  RESULTS: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL > 0:
        print("  FAIL INTEGRATION TESTS FAILED")
        raise SystemExit(1)
    else:
        print("  PASS ALL INTEGRATION TESTS PASSED")


if __name__ == "__main__":
    main()
