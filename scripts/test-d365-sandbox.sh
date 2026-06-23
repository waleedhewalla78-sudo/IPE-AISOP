#!/usr/bin/env bash
# D365 sandbox integration test (R4 T042)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python scripts/integration/d365_sandbox_validate.py "$@"
