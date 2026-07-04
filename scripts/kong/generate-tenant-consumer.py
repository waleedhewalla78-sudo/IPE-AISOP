#!/usr/bin/env python3
"""Emit a Kong declarative consumer block for per-tenant rate limiting."""

from __future__ import annotations

import argparse

REDIS_RATE_LIMIT = """      - name: rate-limiting
        config:
          minute: {minute}
          limit_by: consumer
          policy: redis
          redis_host: redis
          redis_port: 6379
          redis_database: 2
          fault_tolerant: true"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True, help="Kong consumer username (e.g. tenant-aaa-111)")
    parser.add_argument("--custom-id", required=True, help="Tenant UUID; must match JWT tenant_id claim")
    parser.add_argument("--minute", type=int, default=200, help="Requests per minute (default: 200)")
    args = parser.parse_args()

    print(f"  - username: {args.username}")
    print(f"    custom_id: {args.custom_id}")
    print("    plugins:")
    print(REDIS_RATE_LIMIT.format(minute=args.minute))


if __name__ == "__main__":
    main()
