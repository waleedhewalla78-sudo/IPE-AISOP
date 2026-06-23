#!/usr/bin/env bash
# Verify Airflow in default docker-compose (R4 T043)
set -euo pipefail
URL="${AIRFLOW_URL:-http://localhost:8080}"
REPORT="${AIRFLOW_EVIDENCE_PATH:-specs/003-autonomous-planning-v5/evidence/r4/airflow-verify-report.txt}"
mkdir -p "$(dirname "$REPORT")"

pass=0
total=0

check() {
  total=$((total + 1))
  if eval "$2"; then
    echo "[PASS] $1" | tee -a "$REPORT"
    pass=$((pass + 1))
  else
    echo "[FAIL] $1" | tee -a "$REPORT"
  fi
}

: > "$REPORT"
echo "IPE Airflow Verification" | tee -a "$REPORT"
echo "URL: $URL" | tee -a "$REPORT"
echo "" | tee -a "$REPORT"

check "Health endpoint" "curl -sf \"$URL/health\" >/dev/null"
check "Web UI reachable" "curl -sf -o /dev/null \"$URL/\""

echo "" | tee -a "$REPORT"
echo "DAGs: ipe_daily_sop_pipeline, ipe_hourly_schedule_pipeline, ipe_retention_enforcement" | tee -a "$REPORT"
echo "RESULT: $pass / $total" | tee -a "$REPORT"

test "$pass" -eq "$total"
