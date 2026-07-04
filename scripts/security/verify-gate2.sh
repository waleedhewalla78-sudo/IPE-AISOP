#!/usr/bin/env bash
# Gate 2: Security Hardening verification (Phase 2)
set -eo pipefail

KONG="${KONG_URL:-http://localhost:8000}"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python
BASH_BIN="${BASH:-bash}"

echo "=== Gate 2: Security Hardening Verification ==="

# Obtain JWT for rate-limit test (protected route)
LOGIN=$(curl -sf -X POST "$KONG/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"Ahmed@nour","password":"admin"}' 2>/dev/null || echo "{}")
TOKEN=$("$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token',''))" <<<"$LOGIN" 2>/dev/null || echo "")
AUTH="Authorization: Bearer $TOKEN"

# R1 has no /api/v1/bom — use dpe-svc demand route (Kong-protected)
API_PATH="${GATE2_API_PATH:-/api/v1/demand}"
INTERNAL_SVC="${GATE2_INTERNAL_SVC:-docker-dpe-svc-1}"

PASS=true

echo ""
echo "--- Step 1: CORS rejection (evil origin) ---"
CORS_OUT=$(curl -sv -X OPTIONS "$KONG$API_PATH" \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: GET" 2>&1 || true)
echo "$CORS_OUT" | grep -i "access-control-allow-origin" || echo "  (no Access-Control-Allow-Origin header — good)"
if echo "$CORS_OUT" | grep -qi "access-control-allow-origin:.*evil.com"; then
  echo "  ❌ CORS leaked evil.com origin"
  PASS=false
else
  echo "  ✅ CORS does not allow http://evil.com"
fi

echo ""
echo "--- Step 2: Rate limiting (burst >500 req/min, global IP limit) ---"
# Clear prior window counters so burst is not diluted by timeouts/partial windows
if docker ps --format '{{.Names}}' | grep -qx 'docker-redis-1'; then
  docker exec docker-redis-1 redis-cli -n 2 FLUSHDB >/dev/null 2>&1 || true
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RATE_OK=false
BURST_SCRIPT="$SCRIPT_DIR/rate-limit-burst.sh"
# Fast thread burst first; fall back to k6-stress (setupTimeout 120s) if window not hit
if [[ -f "$BURST_SCRIPT" ]]; then
  echo "Burst probe: rate-limit-burst.sh"
  if bash "$BURST_SCRIPT" "$KONG/api/v1/health" 800 120; then
    RATE_OK=true
  fi
fi
if [[ "$RATE_OK" != true ]] && command -v k6 >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/scripts/perf/k6-stress.js" ]]; then
  echo "Fallback: k6-stress.js"
  if docker ps --format '{{.Names}}' | grep -qx 'docker-redis-1'; then
    docker exec docker-redis-1 redis-cli -n 2 FLUSHDB >/dev/null 2>&1 || true
  fi
  if (cd "$PROJECT_ROOT" && KONG_URL="$KONG" k6 run --quiet scripts/perf/k6-stress.js); then
    RATE_OK=true
  fi
fi
if [[ "$RATE_OK" == true ]]; then
  echo "  ✅ Rate limiting returned 429"
else
  echo "  ❌ Expected 429 after exceeding 500 requests/minute"
  PASS=false
fi

echo ""
echo "--- Step 3: Cross-tenant isolation tests ---"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export TEST_DB_HOST="${TEST_DB_HOST:-localhost}"
export TEST_DB_PORT="${TEST_DB_PORT:-5433}"
export TEST_DB_USER="${TEST_DB_USER:-ipe_app}"
export TEST_DB_PASSWORD="${TEST_DB_PASSWORD:-ipe_app_pass}"
export TEST_DB_NAME="${TEST_DB_NAME:-ipe_test}"
# Host-side pytest inherits enterprise RS256 default; point at repo key (containers use /app/...)
export IPE_JWT_SIGNING_MODE="${IPE_JWT_SIGNING_MODE:-rs256}"
export IPE_JWT_PUBLIC_KEY_PATH="${IPE_JWT_PUBLIC_KEY_PATH:-$PROJECT_ROOT/config/keys/jwt-public.pem}"
export JWT_PUBLIC_KEY_PATH="${JWT_PUBLIC_KEY_PATH:-$IPE_JWT_PUBLIC_KEY_PATH}"

PYTEST_CMD=(uv run pytest ../../tests/security/test_cross_tenant_isolation.py -v --tb=short)
if ! command -v uv >/dev/null 2>&1; then
  PYTEST_CMD=("$PY" -m pytest "$PROJECT_ROOT/tests/security/test_cross_tenant_isolation.py" -v --tb=short)
fi

if (cd "$PROJECT_ROOT/services/res-svc" && "${PYTEST_CMD[@]}"); then
  echo "  ✅ Cross-tenant isolation tests passed"
else  echo "  ❌ Cross-tenant isolation tests failed"
  PASS=false
fi

echo ""
echo "--- Step 4: Network isolation ---"
if docker ps --format '{{.Names}}' | grep -qx "$INTERNAL_SVC"; then
  if docker exec "$INTERNAL_SVC" python -c "import socket; s=socket.create_connection(('db',5432),3); s.close(); print('ok')" 2>/dev/null | grep -q ok; then
    echo "  ✅ Internal service can reach db:5432"
  else
    echo "  ❌ Cannot reach db:5432 from $INTERNAL_SVC"
    PASS=false
  fi

  EXT_RESULT=$(docker exec "$INTERNAL_SVC" python -c "
import urllib.request
try:
    urllib.request.urlopen('http://google.com', timeout=5)
    print('REACHABLE')
except Exception:
    print('BLOCKED')
" 2>/dev/null || echo "BLOCKED")
  if [[ "$EXT_RESULT" == "BLOCKED" ]]; then
    echo "  ✅ External access blocked from internal network"
  else
    echo "  ❌ External access allowed from $INTERNAL_SVC (remove ipe-monitoring from backend networks)"
    PASS=false
  fi
else
  echo "  ⚠️  Container $INTERNAL_SVC not running — skip network isolation"
  PASS=false
fi

echo ""
echo "============================================="
if [[ "$PASS" == true ]]; then
  echo "  RESULT: PASS"
else
  echo "  RESULT: FAIL (see items above)"
fi
echo "============================================="

[[ "$PASS" == true ]]
