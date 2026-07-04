#!/usr/bin/env python3
"""Live quota enforcement probe — simulates resource creation until HTTP 429."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "services" / "shared"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

TENANT_ID = os.environ.get("GATE3_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
MAX_USERS = int(os.environ.get("GATE3_MAX_USERS", "2"))


async def main() -> int:
    overrides = {TENANT_ID: {"max_users": MAX_USERS}}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(overrides, f)
        override_path = f.name

    os.environ["IPE_TENANT_QUOTA_OVERRIDES"] = override_path
    from ipe_shared.tenant import quotas as quotas_mod

    quotas_mod.settings.TENANT_QUOTA_OVERRIDES = override_path
    from ipe_shared.tenant.quotas import enforce_quota

    saw_429 = False
    for attempt in range(MAX_USERS + 2):
        current_count = attempt
        try:
            await enforce_quota(TENANT_ID, "users", current_count)
            print(f"  create attempt {attempt + 1} (count={current_count}): allowed")
        except HTTPException as exc:
            print(f"  create attempt {attempt + 1} (count={current_count}): HTTP {exc.status_code}")
            if exc.status_code == 429:
                saw_429 = True
                break

    Path(override_path).unlink(missing_ok=True)
    if saw_429:
        print("quota 429 observed")
        return 0
    print("expected HTTP 429 at quota limit")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
