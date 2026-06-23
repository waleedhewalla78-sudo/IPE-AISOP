#!/usr/bin/env bash
# SAP sandbox integration test (R4 T041)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python scripts/integration/sap_sandbox_validate.py "$@"
