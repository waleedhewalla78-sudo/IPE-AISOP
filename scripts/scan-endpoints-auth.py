#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27",
#     "fastapi>=0.111",
# ]
# ///
"""IPE Endpoint Auth Scanner — In-Process ASGI Mode

Imports each IPE service's FastAPI app in-process, discovers all routes
from the OpenAPI spec, and verifies that non-excluded endpoints return
401/403 when called WITHOUT a valid JWT (no Authorization header,
no X-Tenant-ID header).

Uses httpx.ASGITransport so no running services are required.

Excluded endpoints (expected to be public):
    /health, /ready, /metrics, /docs, /redoc, /openapi.json

Exit codes:
    0 — all non-excluded endpoints correctly require auth
    1 — one or more non-excluded endpoints accessible without auth
    2 — import / scan error
"""

import asyncio
import importlib
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"
SHARED_DIR = SERVICES_DIR / "shared"

SERVICES = [
    "dpe-svc",
    "mat-svc",
    "cap-svc",
    "fea-svc",
    "res-svc",
    "del-svc",
    "nlp-svc",
    "rec-svc",
    "alert-svc",
    "connector",
    "sustain-svc",
    "quality-svc",
    "scn-svc",
    "network-svc",
    "ml-svc",
]

EXCLUDED_PATHS = {
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}

DUMMY_UUID = "00000000-0000-0000-0000-000000000000"
AUTH_EXPECTED = {401, 403}

BANNER = "=" * 80
SECTION = "-" * 80

logging.disable(logging.CRITICAL)
os.environ.setdefault("OTEL_TRACING_ENABLED", "False")
os.environ.setdefault("OTEL_LOGGING_ENABLED", "False")


@dataclass
class ScanResult:
    service: str
    method: str
    endpoint: str
    expected_status: str
    actual_status: int
    passed: bool

    @property
    def verdict(self) -> str:
        return "PASS" if self.passed else "FAIL"


def is_excluded(path: str) -> bool:
    normalized = path.rstrip("/")
    for ep in EXCLUDED_PATHS:
        if normalized == ep or normalized.endswith(ep):
            return True
    return False


def sanitize_path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", DUMMY_UUID, path)


def discover_routes(app) -> list[tuple[str, str]]:
    try:
        spec = app.openapi()
        paths = spec.get("paths", {})
        routes = []
        for path, methods in paths.items():
            for method in methods:
                if method.upper() in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    routes.append((method.upper(), path))
        return sorted(routes, key=lambda r: (r[1], r[0]))
    except Exception as exc:
        print(f"  [WARN] OpenAPI discovery failed: {exc}")
        return []


def _override_db_session(app) -> bool:
    try:
        from ipe_shared.database.session import get_session

        async def _mock_session():
            yield AsyncMock()

        app.dependency_overrides[get_session] = _mock_session

        try:
            from ipe_shared.database.connection import get_engine

            async def _mock_engine():
                yield AsyncMock()

            app.dependency_overrides[get_engine] = _mock_engine
        except ImportError:
            pass

        return True
    except ImportError:
        return False


def _clear_app_modules() -> None:
    to_remove = [
        k for k in list(sys.modules.keys())
        if k == "app" or k.startswith("app.")
    ]
    for m in to_remove:
        del sys.modules[m]


def load_service_app(service_name: str):
    service_dir = SERVICES_DIR / service_name
    main_py = service_dir / "app" / "main.py"
    if not main_py.exists():
        print(f"  [SKIP] no app/main.py found")
        return None

    service_str = str(service_dir)
    shared_str = str(SHARED_DIR)

    if shared_str not in sys.path:
        sys.path.insert(0, shared_str)
    sys.path.insert(0, service_str)

    _clear_app_modules()

    try:
        mod = importlib.import_module("app.main")
        app = getattr(mod, "app", None)
        if app is None:
            create_app = getattr(mod, "create_app", None)
            if create_app:
                app = create_app()

        if app is None:
            print(f"  [SKIP] no app or create_app() found")
            return None

        override_ok = _override_db_session(app)
        status = "OK" if override_ok else "WARN"
        print(f"  [{status}] DB session dependency overridden")

        routes = discover_routes(app)
        non_excluded = [r for r in routes if not is_excluded(r[1])]
        print(f"  Discovered {len(routes)} routes ({len(non_excluded)} non-excluded)")
        return app
    except Exception as exc:
        print(f"  [ERROR] Failed to import {service_name}: {exc}")
        return None
    finally:
        if service_str in sys.path:
            sys.path.remove(service_str)


async def scan_service(service_name: str, app) -> list[ScanResult]:
    results: list[ScanResult] = []
    routes = discover_routes(app)

    if not routes:
        print("  No routes found on app.")
        return results

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for method, path in routes:
            if is_excluded(path):
                continue

            test_path = sanitize_path(path)
            try:
                if method in ("GET", "DELETE", "HEAD", "OPTIONS"):
                    resp = await client.request(method, test_path)
                else:
                    resp = await client.request(method, test_path, json={})
                status = resp.status_code
            except Exception:
                status = -1

            passed = status in AUTH_EXPECTED
            result = ScanResult(
                service=service_name,
                method=method,
                endpoint=path,
                expected_status="401/403",
                actual_status=status,
                passed=passed,
            )
            results.append(result)

            if status == -1:
                status_str = "ERR"
            else:
                status_str = str(status)
            icon = "[OK]" if passed else "[!!]"
            print(f"  {icon} {method:6s} {path:55s} {status_str:>7s}  [{result.verdict}]")

    return results


def print_summary_table(all_results: list[ScanResult]) -> None:
    print(f"\n{BANNER}")
    print("  DETAILED RESULTS TABLE")
    print(f"{BANNER}")
    print(
        f"  {'Service':<14s} {'Method':<7s} {'Endpoint':<55s} "
        f"{'Expected':<10s} {'Actual':<7s} {'Result':<6s}"
    )
    print("  " + "-" * 101)
    for r in all_results:
        status_str = str(r.actual_status) if r.actual_status > 0 else "ERR"
        print(
            f"  {r.service:<14s} {r.method:<7s} {r.endpoint:<55s} "
            f"{r.expected_status:<10s} {status_str:<7s} {r.verdict:<6s}"
        )


def main() -> int:
    print(f"\n{BANNER}")
    print("  IPE Endpoint Auth Scanner (In-Process) — ASGITransport Mode")
    print(f"{BANNER}")
    print(f"  Services to scan: {len(SERVICES)}")
    print(f"  Excluded paths: {', '.join(sorted(EXCLUDED_PATHS))}")
    print(f"  Expected status codes (unauthenticated): {', '.join(str(s) for s in sorted(AUTH_EXPECTED))}")
    print()

    all_results: list[ScanResult] = []
    skipped = 0

    for service_name in SERVICES:
        print(f"\n{SECTION}")
        print(f"  Scanning {service_name}")
        print(f"{SECTION}")

        app = load_service_app(service_name)
        if app is None:
            skipped += 1
            continue

        try:
            results = asyncio.run(scan_service(service_name, app))
            all_results.extend(results)
        except Exception as exc:
            print(f"  [ERROR] Scan failed: {exc}")
            skipped += 1

    passed = [r for r in all_results if r.passed]
    failed = [r for r in all_results if not r.passed]

    print(f"\n{BANNER}")
    print("  ENDPOINT AUTH SCAN REPORT")
    print(f"{BANNER}")
    print(f"\n  Endpoints correctly requiring auth:   {len(passed)}")
    print(f"  Endpoints accessible without auth:    {len(failed)}")
    print(f"  Services skipped/errored:             {skipped}")

    if passed:
        print(f"\n{SECTION}")
        print("  AUTH-ENFORCED ENDPOINTS (correctly secured)")
        print(f"{SECTION}")
        for r in passed:
            print(f"    [PASS] {r.service:14s} {r.method:6s} {r.endpoint}")

    if failed:
        print(f"\n{SECTION}")
        print("  UNSECURED ENDPOINTS (SECURITY VIOLATION)")
        print(f"{SECTION}")
        for r in failed:
            status_str = str(r.actual_status) if r.actual_status > 0 else "ERR"
            print(
                f"    [FAIL] {r.service:14s} {r.method:6s} "
                f"{r.endpoint:55s} got {status_str}"
            )

    print_summary_table(all_results)

    print()
    if failed:
        print(
            f"  [!!] SECURITY VIOLATION: "
            f"{len(failed)} endpoint(s) accessible without auth!"
        )
        return 1

    if skipped:
        print(f"  [WARN] {skipped} service(s) could not be scanned.")
        return 2

    print("  [OK] All non-excluded endpoints correctly require authentication.")
    return 0


if __name__ == "__main__":
    sys.exit(main())