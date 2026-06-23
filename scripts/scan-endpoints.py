#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.28",
# ]
# ///
"""Endpoint Auth Scanner — TASK-P1-009

Connects to each running IPE service, fetches its OpenAPI spec, discovers all
path+method endpoints, and verifies that non-excluded endpoints require
authentication (401/403) when called WITHOUT JWT or X-Tenant-ID headers.

Excluded endpoints (expected to be public):
    /health, /ready, /metrics, /docs, /redoc, /openapi.json

Exit codes:
    0 — all non-excluded endpoints correctly require auth
    1 — one or more non-excluded endpoints are accessible without auth
    2 — connection / parsing error

Usage:
    python scripts/scan-endpoints.py
    python scripts/scan-endpoints.py --scheme http --timeout 10
    IPE_SERVICES='{"dpe-svc":8002}' python scripts/scan-endpoints.py
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass

import requests

DEFAULT_SERVICES = {
    "dpe-svc": 8002,
    "mat-svc": 8003,
    "cap-svc": 8004,
    "res-svc": 8005,
    "fea-svc": 8006,
    "del-svc": 8007,
    "rec-svc": 8008,
    "nlp-svc": 8009,
    "alert-svc": 8010,
    "connector": 8011,
}

EXCLUDED_PATHS = {
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}

EXCLUDED_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json")

UNAUTH_EXPECTED_STATUS_CODES = {401, 403}

BANNER = "=" * 72
SECTION = "-" * 72


@dataclass
class EndpointResult:
    service: str
    method: str
    path: str
    status_code: int
    is_excluded: bool
    is_secured: bool

    @property
    def label(self) -> str:
        if self.is_excluded:
            return "EXCLUDED"
        if self.is_secured:
            return "SECURED"
        return "UNSECURED"


def parse_service_overrides(raw: str) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): int(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        pass
    result = {}
    for pair in raw.split(","):
        if "=" in pair:
            name, port = pair.split("=", 1)
            result[name.strip()] = int(port.strip())
    return result


def get_services(args) -> dict:
    services = dict(DEFAULT_SERVICES)
    env_override = os.environ.get("IPE_SERVICES")
    if env_override:
        services.update(parse_service_overrides(env_override))
    if args.services:
        services.update(parse_service_overrides(args.services))
    return services


def is_excluded_path(path: str) -> bool:
    normalized = path.rstrip("/")
    if normalized in EXCLUDED_PATHS:
        return True
    for prefix in EXCLUDED_PATH_PREFIXES:
        if normalized.startswith(prefix):
            return True
    return False


def fetch_openapi(base_url: str, timeout: int) -> dict | None:
    url = f"{base_url}/openapi.json"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"  [ERROR] Failed to fetch {url}: {exc}")
        return None


def extract_endpoints(spec: dict) -> list[tuple[str, str]]:
    paths = spec.get("paths", {})
    endpoints = []
    for path, methods in paths.items():
        for method in methods:
            if method.lower() in ("get", "post", "put", "patch", "delete"):
                endpoints.append((method.upper(), path))
    return endpoints


def test_endpoint(
    base_url: str,
    method: str,
    path: str,
    timeout: int,
) -> int:
    url = f"{base_url}{path}"
    try:
        resp = requests.request(
            method=method,
            url=url,
            timeout=timeout,
            headers={},
        )
        return resp.status_code
    except requests.exceptions.ConnectionError:
        return 0
    except requests.exceptions.Timeout:
        return -1
    except Exception:
        return -2


def scan_service(
    service_name: str,
    port: int,
    base_url_scheme: str,
    timeout: int,
) -> list[EndpointResult]:
    base_url = f"{base_url_scheme}://localhost:{port}"
    print(f"\n{SECTION}")
    print(f"  Scanning {service_name} ({base_url})")
    print(f"{SECTION}")

    spec = fetch_openapi(base_url, timeout)
    if spec is None:
        return []

    endpoints = extract_endpoints(spec)
    if not endpoints:
        print("  No endpoints found in OpenAPI spec.")
        return []

    results = []
    for method, path in endpoints:
        excluded = is_excluded_path(path)
        status_code = test_endpoint(base_url, method, path, timeout)

        secured = False
        if excluded:
            secured = True
        elif status_code in UNAUTH_EXPECTED_STATUS_CODES:
            secured = True
        elif status_code in (0, -1, -2):
            pass
        else:
            secured = False

        result = EndpointResult(
            service=service_name,
            method=method,
            path=path,
            status_code=status_code,
            is_excluded=excluded,
            is_secured=secured,
        )
        results.append(result)

        if status_code == 0:
            status_str = "CONN_ERR"
        elif status_code == -1:
            status_str = "TIMEOUT"
        elif status_code == -2:
            status_str = "ERROR"
        else:
            status_str = str(status_code)

        icon = {
            "EXCLUDED": "\u2713",
            "SECURED": "\u2713",
            "UNSECURED": "\u2717",
        }[result.label]
        print(f"  {icon} {method:6s} {path:45s} {status_str:>7s}  [{result.label}]")

    return results


def generate_report(all_results: list[EndpointResult]) -> None:
    secured = [r for r in all_results if not r.is_excluded and r.is_secured]
    unsecured = [r for r in all_results if not r.is_excluded and not r.is_secured]
    excluded = [r for r in all_results if r.is_excluded]

    print(f"\n{BANNER}")
    print("  ENDPOINT AUTH SCAN REPORT")
    print(f"{BANNER}")

    print(f"\n  Endpoints correctly requiring auth:    {len(secured)}")
    print(f"  Endpoints accessible without auth:     {len(unsecured)}")
    print(f"  Endpoints excluded from auth check:     {len(excluded)}")

    if secured:
        print(f"\n{SECTION}")
        print("  AUTH-REQUIRED ENDPOINTS (correctly secured)")
        print(f"{SECTION}")
        for r in secured:
            print(f"    \u2713 {r.service:12s} {r.method:6s} {r.path}")

    if unsecured:
        print(f"\n{SECTION}")
        print("  UNSECURED ENDPOINTS (SECURITY VIOLATION)")
        print(f"{SECTION}")
        for r in unsecured:
            status_str = str(r.status_code) if r.status_code > 0 else "ERR"
            print(f"    \u2717 {r.service:12s} {r.method:6s} {r.path:40s} got {status_str}")

    if excluded:
        print(f"\n{SECTION}")
        print("  EXCLUDED ENDPOINTS (health/docs/openapi)")
        print(f"{SECTION}")
        for r in excluded:
            print(f"    \u2713 {r.service:12s} {r.method:6s} {r.path}")

    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan IPE service endpoints for auth enforcement (TASK-P1-009)"
    )
    parser.add_argument(
        "--scheme",
        default="http",
        choices=["http", "https"],
        help="URL scheme for service connections (default: http)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--services",
        default="",
        help="Override/add services as JSON '{\"name\":port}' or CSV 'name=port,name2=port2'",
    )
    parser.add_argument(
        "--no-exit-on-violation",
        action="store_true",
        default=False,
        help="Exit with code 0 even if unsecured endpoints found",
    )
    args = parser.parse_args()

    services = get_services(args)
    print(f"\n{BANNER}")
    print("  IPE Endpoint Auth Scanner — TASK-P1-009")
    print(f"{BANNER}")
    print(f"  Services to scan: {len(services)}")
    print(f"  Excluded paths: {', '.join(sorted(EXCLUDED_PATHS))}")
    print(f"  Timeout: {args.timeout}s")

    all_results: list[EndpointResult] = []
    errors = 0
    for service_name, port in sorted(services.items(), key=lambda x: x[1]):
        try:
            results = scan_service(service_name, port, args.scheme, args.timeout)
            all_results.extend(results)
        except Exception as exc:
            print(f"  [ERROR] Failed to scan {service_name}: {exc}")
            errors += 1

    generate_report(all_results)

    unsecured = [r for r in all_results if not r.is_excluded and not r.is_secured]
    if unsecured:
        print(f"  \u2717 SECURITY VIOLATION: {len(unsecured)} endpoint(s) accessible without auth!")
        if not args.no_exit_on_violation:
            return 1

    if errors:
        print(f"  \u26a0 {errors} service(s) could not be scanned (connection errors).")
        if not args.no_exit_on_violation:
            return 2

    print("  \u2713 All non-excluded endpoints correctly require authentication.")
    return 0


if __name__ == "__main__":
    sys.exit(main())