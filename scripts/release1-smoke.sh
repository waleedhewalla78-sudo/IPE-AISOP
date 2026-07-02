#!/usr/bin/env bash
# Release 1 smoke test (CI-friendly bash port of release1-smoke.ps1)
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
TENANT_ID="${TENANT_ID:-a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11}"
EMAIL="${EMAIL:-Ahmed@nour}"
PASSWORD="${PASSWORD:-admin}"

pass=0
fail=0

assert() {
  local name="$1"
  local cond="$2"
  if [[ "$cond" == "true" ]]; then
    echo "[PASS] $name"
    pass=$((pass + 1))
  else
    echo "[FAIL] $name"
    fail=$((fail + 1))
  fi
}

echo "=== Release 1 smoke test ==="

login_resp=$(curl -sf -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" || echo "")
token=$(echo "$login_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token',''))" 2>/dev/null || echo "")
assert "Login" "$([[ -n \"$token\" ]] && echo true || echo false)"

if [[ -z "$token" ]]; then
  echo "Login failed — aborting"
  exit 1
fi

hdr=(-H "Authorization: Bearer $token" -H "X-Tenant-ID: $TENANT_ID")

health=$(curl -sf "$BASE_URL/api/v1/health" "${hdr[@]}" || echo "")
assert "Health" "$([[ \"$health\" == *'\"status\":\"ok\"'* ]] || [[ \"$health\" == *'\"status\": \"ok\"'* ]] && echo true || echo false)"

sync=$(curl -sf "$BASE_URL/api/v1/sync/status" "${hdr[@]}" || echo "")
assert "Sync status endpoint" "$([[ \"$sync\" == *'\"success\":true'* ]] || [[ \"$sync\" == *'\"success\": true'* ]] && echo true || echo false)"

queue=$(curl -sf "$BASE_URL/api/v1/feasibility/queue" "${hdr[@]}" || echo "")
assert "Feasibility queue" "$([[ \"$queue\" == *'\"success\":true'* ]] || [[ \"$queue\" == *'\"success\": true'* ]] && echo true || echo false)"

kpis=$(curl -sf "$BASE_URL/api/v1/feasibility/kpis" "${hdr[@]}" || echo "")
assert "Feasibility KPIs" "$([[ \"$kpis\" == *'\"success\":true'* ]] || [[ \"$kpis\" == *'\"success\": true'* ]] && echo true || echo false)"

echo ""
echo "Result: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
