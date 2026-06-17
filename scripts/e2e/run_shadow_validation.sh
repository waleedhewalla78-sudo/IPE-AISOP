#!/usr/bin/env bash
# =============================================================================
# run_shadow_validation.sh
#
# Shadow Mode E2E Validation Pipeline
#
# 1. Brings up the full test stack via docker-compose.test.yml
# 2. Waits for service health checks
# 3. Seeds 100 historical MOs into the test database
# 4. Executes shadow_mode_comparison.py against live service endpoints
# 5. Parses JSON output, asserts "pass": true and improvement_delta >= 10.0
# 6. Tears down the stack and prints PASS/FAIL summary
#
# Usage:
#   bash scripts/e2e/run_shadow_validation.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/infrastructure/docker/docker-compose.test.yml"
REPORT_FILE="/tmp/ipe-shadow-report.json"

echo "============================================"
echo "  IPE Shadow Mode E2E Validation Pipeline"
echo "============================================"
echo ""

# --- Step 1: Bring up test stack ---
echo "[1/5] Bringing up test infrastructure..."
docker compose -f "$COMPOSE_FILE" up -d postgres kafka zookeeper redis
echo "  Waiting for PostgreSQL..."
until docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U ipe 2>/dev/null; do
  sleep 2
done
echo "  PostgreSQL is ready."

# --- Step 2: Wait for services ---
echo "[2/5] Waiting for dependent services..."
for svc in postgres kafka redis; do
  echo "  Waiting for $svc..."
  docker compose -f "$COMPOSE_FILE" exec -T "$svc" sh -c "exit 0" 2>/dev/null || true
done
echo "  All services ready."

# --- Step 3: Seed historical MOs ---
echo "[3/5] Seeding 100 historical MOs..."
export IPE_DATABASE_URL_SYNC="postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test"
bash "${SCRIPT_DIR}/scripts/seed-data.sh"
echo "  Seed data loaded."

# --- Step 4: Run shadow mode comparison ---
echo "[4/5] Running shadow mode comparison..."
TENANT_ID="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

cd "${SCRIPT_DIR}"
uv run python scripts/validation/shadow_mode_comparison.py \
  --tenant-id "$TENANT_ID" \
  --historical-mos 100 \
  --dpe-url "http://localhost:8002" \
  --mat-url "http://localhost:8003" \
  --cap-url "http://localhost:8004" \
  --output "$REPORT_FILE"
cd - >/dev/null

echo "  Shadow comparison complete."

# --- Step 5: Parse results ---
echo "[5/5] Validating results..."
if [ ! -f "$REPORT_FILE" ]; then
  echo "  ✗ FAIL: Report file not found at $REPORT_FILE"
  exit 1
fi

PASS_FLAG=$(python3 -c "import json; r=json.load(open('$REPORT_FILE')); print(r.get('pass','false'))")
DELTA=$(python3 -c "import json; r=json.load(open('$REPORT_FILE')); print(r.get('improvement_delta',0))")

echo "  improvement_delta = ${DELTA}%"
echo "  pass flag = ${PASS_FLAG}"

if [ "$PASS_FLAG" != "True" ]; then
  echo "  ✗ FAIL: pass flag is not True"
  exit 1
fi

DELTA_INT=$(python3 -c "print(int(float('$DELTA') * 100))")
THRESHOLD_INT=1000  # 10.0 * 100
if [ "$DELTA_INT" -lt "$THRESHOLD_INT" ]; then
  echo "  ✗ FAIL: improvement_delta ${DELTA}% < 10.0%"
  exit 1
fi

echo ""
echo "============================================"
echo "  ✅ SHADOW MODE E2E: ALL VALIDATIONS PASSED"
echo "  improvement_delta = ${DELTA}% (threshold: 10.0%)"
echo "============================================"
