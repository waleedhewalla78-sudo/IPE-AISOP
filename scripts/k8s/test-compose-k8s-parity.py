"""Compare Docker Compose vs K8s Ingress API response structure (Phase 3 Gate 8)."""

from __future__ import annotations

import asyncio
import os
import sys

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

COMPOSE_BASE = os.getenv("COMPOSE_BASE", "http://localhost:8000/api/v1")
K8S_BASE = os.getenv("K8S_BASE", "http://localhost/api/v1")
TOKEN = os.getenv("IPE_TOKEN", "")
TENANT = os.getenv("IPE_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

ENDPOINTS = [
    "/health",
    "/feasibility/queue",
    "/feasibility/kpis",
]


async def check_parity() -> int:
    headers = {"X-Tenant-ID": TENANT}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    failures = 0
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        for endpoint in ENDPOINTS:
            compose_url = f"{COMPOSE_BASE}{endpoint}"
            k8s_url = f"{K8S_BASE}{endpoint}"
            try:
                compose_resp = await client.get(compose_url, headers=headers)
                k8s_resp = await client.get(k8s_url, headers=headers)
            except Exception as exc:
                print(f"ERR {endpoint}: {exc}")
                failures += 1
                continue

            if compose_resp.status_code != k8s_resp.status_code:
                print(
                    f"FAIL {endpoint}: Compose {compose_resp.status_code} != K8s {k8s_resp.status_code}"
                )
                failures += 1
                continue

            try:
                compose_data = compose_resp.json()
                k8s_data = k8s_resp.json()
                compose_keys = set(compose_data.keys()) if isinstance(compose_data, dict) else set()
                k8s_keys = set(k8s_data.keys()) if isinstance(k8s_data, dict) else set()
                if compose_keys == k8s_keys:
                    print(f"OK   {endpoint}: equivalent structure ({compose_resp.status_code})")
                else:
                    print(f"WARN {endpoint}: key mismatch Compose={compose_keys} K8s={k8s_keys}")
                    failures += 1
            except Exception:
                print(f"WARN {endpoint}: could not compare JSON")
                failures += 1

    return failures


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check_parity()))
