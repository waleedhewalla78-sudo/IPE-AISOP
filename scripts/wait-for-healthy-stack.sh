#!/usr/bin/env bash
# Waits for IPE stack health via Kong before demo or CI gates.
set -euo pipefail

KONG_URL="${1:-http://localhost:8000}"
MAX_WAIT="${2:-120}"
TENANT="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

echo "Waiting for IPE stack at ${KONG_URL} (max ${MAX_WAIT}s)..."
elapsed=0
while [ "$elapsed" -lt "$MAX_WAIT" ]; do
  token=$(curl -sf -X POST "${KONG_URL}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"Ahmed@nour","password":"admin"}' | jq -r '.data.access_token // empty' || true)
  if [ -n "$token" ]; then
    healthy=true
    for path in "/api/v1/demand/forecast?horizon=short" "/api/v1/supply/network" "/api/v1/scenario" "/api/v1/copilot/agents"; do
      code=$(curl -so /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer ${token}" -H "X-Tenant-ID: ${TENANT}" \
        "${KONG_URL}${path}" 2>/dev/null || echo "000")
      if [ "$code" != "200" ]; then healthy=false; break; fi
    done
    if $healthy; then
      echo "All services healthy after ${elapsed}s"
      exit 0
    fi
  fi
  sleep 3
  elapsed=$((elapsed + 3))
done
echo "Timeout — stack not healthy after ${MAX_WAIT}s"
exit 1
