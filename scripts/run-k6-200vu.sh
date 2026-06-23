#!/usr/bin/env bash
# k6 200 VU re-certification (R4 T044 / SC-012)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
REPORT="${K6_SUMMARY_PATH:-specs/003-autonomous-planning-v5/evidence/r4/k6-200vu-summary.txt}"
mkdir -p "$(dirname "$REPORT")"
export BASE_URL="${BASE_URL:-http://localhost:8000}"
export K6_SUMMARY_PATH="$REPORT"
echo "Running k6 200 VU test against $BASE_URL ..."
k6 run tests/performance/k6/load-test-200vu.js
