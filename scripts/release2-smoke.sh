#!/usr/bin/env bash
# Release 2 smoke test — R1 APIs + nlp/demand/scenario health and Kong routes
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

assert_health() {
  local name="$1"
  local url="$2"
  local body
  body=$(curl -sf "$url" 2>/dev/null || echo "")
  if [[ "$body" == *'"status":"ok"'* ]] || [[ "$body" == *'"status": "ok"'* ]] \
    || [[ "$body" == *'"status":"degraded"'* ]] || [[ "$body" == *'"status": "degraded"'* ]]; then
    assert "$name" true
  else
    assert "$name" false
  fi
}

echo "=== Release 2 smoke test ==="

assert_health "nlp-svc container" "http://localhost:8007/api/v1/health"
assert_health "demand-svc container" "http://localhost:8040/api/v1/health"
assert_health "scenario-svc container" "http://localhost:8050/api/v1/health"
assert_health "dpe-svc container" "http://localhost:8020/api/v1/health"
assert_health "fea-svc container" "http://localhost:8004/api/v1/health"
assert_health "res-svc container" "http://localhost:8005/api/v1/health"
assert_health "cap-svc container" "http://localhost:8003/api/v1/health"
assert_health "connector container" "http://localhost:8016/api/v1/health"

login_resp=$(curl -sf -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" || echo "")
token=$(echo "$login_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token',''))" 2>/dev/null || echo "")
assert "Login via Kong" "$([[ -n \"$token\" ]] && echo true || echo false)"

if [[ -z "$token" ]]; then
  echo "Login failed — aborting Kong route checks"
  echo "Result: $pass passed, $fail failed"
  exit 1
fi

hdr=(-H "Authorization: Bearer $token" -H "X-Tenant-ID: $TENANT_ID")

health=$(curl -sf "$BASE_URL/api/v1/health" "${hdr[@]}" || echo "")
assert "Kong health" "$([[ \"$health\" == *'\"status\":\"ok\"'* ]] || [[ \"$health\" == *'\"status\": \"ok\"'* ]] && echo true || echo false)"

sync=$(curl -sf "$BASE_URL/api/v1/sync/status" "${hdr[@]}" || echo "")
assert "Sync status (R1)" "$([[ \"$sync\" == *'\"success\":true'* ]] || [[ \"$sync\" == *'\"success\": true'* ]] && echo true || echo false)"

queue=$(curl -sf "$BASE_URL/api/v1/feasibility/queue" "${hdr[@]}" || echo "")
assert "Feasibility queue (R1)" "$([[ \"$queue\" == *'\"success\":true'* ]] || [[ \"$queue\" == *'\"success\": true'* ]] && echo true || echo false)"

scenarios=$(curl -sf "$BASE_URL/api/v1/scenario" "${hdr[@]}" || echo "")
assert "Kong scenario route" "$([[ \"$scenarios\" == *'\"success\":true'* ]] || [[ \"$scenarios\" == *'\"success\": true'* ]] && echo true || echo false)"

accuracy=$(curl -sf "$BASE_URL/api/v1/demand/accuracy" "${hdr[@]}" || echo "")
assert "Kong demand route" "$([[ \"$accuracy\" == *'\"success\":true'* ]] || [[ \"$accuracy\" == *'\"success\": true'* ]] && echo true || echo false)"

echo ""
echo "Result: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
