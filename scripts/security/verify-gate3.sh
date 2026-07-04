#!/usr/bin/env bash
# Gate 3: Multi-Tenant Quotas verification (Phase 2)
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IPE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python
TENANT_ID="${GATE3_TENANT_ID:-a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11}"

PASS=true

echo "=== Gate 3: Multi-Tenant Quotas Verification ==="

echo ""
echo "--- Step 1a: Quota unit tests (429) ---"
if (cd "$IPE_ROOT/services/shared" && uv run pytest tests/test_tenant_quotas.py -v --tb=short 2>/dev/null); then
  echo "  ✅ Quota unit tests passed"
elif (cd "$IPE_ROOT/services/shared" && "$PY" -m pytest tests/test_tenant_quotas.py -v --tb=short); then
  echo "  ✅ Quota unit tests passed"
else
  echo "  ❌ Quota unit tests failed"
  PASS=false
fi

echo ""
echo "--- Step 1b: Live quota enforcement (SCIM create until 429) ---"
if (cd "$IPE_ROOT/services/res-svc" && uv run python "$IPE_ROOT/scripts/security/quota-probe.py"); then
  echo "  ✅ Quota enforcement returned HTTP 429 at limit"
else
  echo "  ❌ Quota probe did not observe 429"
  PASS=false
fi

echo ""
echo "--- Step 2a: Consumer group unit tests ---"
if (cd "$IPE_ROOT/services/shared" && uv run pytest tests/test_consumer_group.py -v --tb=short 2>/dev/null); then
  echo "  ✅ Consumer group unit tests passed"
elif (cd "$IPE_ROOT/services/shared" && "$PY" -m pytest tests/test_consumer_group.py -v --tb=short); then
  echo "  ✅ Consumer group unit tests passed"
else
  echo "  ❌ Consumer group unit tests failed"
  PASS=false
fi

echo ""
echo "--- Step 2b: Live Kafka consumer group listing ---"
if docker ps --format '{{.Names}}' | grep -qx docker-kafka-1; then
  if (cd "$IPE_ROOT/services/res-svc" && uv run python "$IPE_ROOT/scripts/security/kafka-groups-check.py"); then
    echo "  ✅ Tenant-scoped Kafka consumer groups registered"
  else
    FEA_TENANT=$(docker exec docker-fea-svc-1 printenv IPE_KAFKA_CONSUMER_TENANT_ID 2>/dev/null | tr -d '\r' || true)
    if [[ -z "$FEA_TENANT" ]]; then
      echo "  ❌ IPE_KAFKA_CONSUMER_TENANT_ID not set on fea-svc"
    else
      echo "  ❌ Expected ipe.${FEA_TENANT}.* groups not found in Kafka"
      echo "     Rebuild fea-svc/res-svc/cap-svc and ensure kafka is on ipe-data network"
    fi
    PASS=false
  fi
else
  echo "  ⚠️  docker-kafka-1 not running — skipping live Kafka listing"
  echo "  (consumer group scoping verified via unit tests)"
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
