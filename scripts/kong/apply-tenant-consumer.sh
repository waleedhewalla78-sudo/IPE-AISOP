#!/usr/bin/env bash
# Register a tenant consumer + Redis rate-limiting plugin via Kong Admin API.
# Use when Kong runs with a database (e.g. docker-compose.test.yml), not DB-less mode.
set -euo pipefail

KONG_ADMIN="${KONG_ADMIN:-http://localhost:8001}"
USERNAME="${1:?username required}"
CUSTOM_ID="${2:?custom_id (tenant UUID) required}"
MINUTE="${3:-200}"

consumer_id="$(curl -sf "${KONG_ADMIN}/consumers" \
  --data "username=${USERNAME}" \
  --data "custom_id=${CUSTOM_ID}" \
  | python -c "import sys,json; print(json.load(sys.stdin)['id'])")"

curl -sf -X POST "${KONG_ADMIN}/consumers/${consumer_id}/plugins" \
  --data name=rate-limiting \
  --data "config.minute=${MINUTE}" \
  --data config.limit_by=consumer \
  --data config.policy=redis \
  --data config.redis_host=redis \
  --data config.redis_port=6379 \
  --data config.redis_database=2 \
  --data config.fault_tolerant=true \
  >/dev/null

echo "Created consumer ${USERNAME} (${CUSTOM_ID}) with ${MINUTE} req/min Redis rate limit"
