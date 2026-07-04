#!/usr/bin/env bash
# Gate 4: Odoo Bidirectional Sync verification (Phase 2)
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IPE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MO_ID="${MO_ID:-d1eebc99-9c0b-4ef8-bb6d-6bb9bd380002}"
ERP_MO_ID="${ERP_MO_ID:-5}"

PASS=true

echo "=== Gate 4: Odoo Bidirectional Sync Verification ==="

echo ""
echo "--- Step 1: Live bidirectional sync smoke test ---"
if MO_ID="$MO_ID" ERP_MO_ID="$ERP_MO_ID" bash "$IPE_ROOT/scripts/odoo/test-bidirectional-sync.sh" auto; then
  echo "  ✅ Bidirectional sync smoke test passed"
else
  echo "  ❌ Bidirectional sync smoke test failed"
  PASS=false
fi

echo ""
echo "--- Step 2: Conflict resolution unit tests ---"
if (cd "$IPE_ROOT/services/shared" && uv run pytest tests/test_odoo_conflict_resolver.py -v --tb=short 2>/dev/null); then
  echo "  ✅ Conflict resolver tests passed"
else
  echo "  ❌ Conflict resolver tests failed"
  PASS=false
fi

echo ""
echo "--- Step 3: Odoo sync integration tests ---"
if (cd "$IPE_ROOT/services/connector" && uv run pytest tests/test_odoo_sync_integration.py -v --tb=short 2>/dev/null); then
  echo "  ✅ Odoo sync integration tests passed (includes conflict detection)"
else
  echo "  ❌ Odoo sync integration tests failed"
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
