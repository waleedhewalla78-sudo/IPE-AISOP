#!/usr/bin/env python3
"""Verify tenant-scoped Kafka consumer groups are registered."""

from __future__ import annotations

import subprocess
import sys

TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


def main() -> int:
    try:
        proc = subprocess.run(
            [
                "docker",
                "exec",
                "docker-kafka-1",
                "kafka-consumer-groups",
                "--bootstrap-server",
                "localhost:9092",
                "--list",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"  Kafka list failed: {exc}")
        return 1

    if proc.returncode != 0:
        print(proc.stderr.strip() or "  kafka-consumer-groups failed")
        return 1

    groups = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    scoped = [g for g in groups if g.startswith("ipe.")]

    for g in groups:
        print(f"  group: {g}")

    if not scoped:
        print("  no tenant-scoped groups found")
        return 1

    tenant_groups = [g for g in scoped if TENANT_ID in g]
    if not tenant_groups:
        print(f"  no groups for tenant {TENANT_ID}")
        return 1

    print(f"  scoped groups: {len(scoped)} ({len(tenant_groups)} for tenant)")
    for g in tenant_groups:
        print(f"  OK {g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
