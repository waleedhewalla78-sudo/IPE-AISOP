#!/bin/bash
# IPE Health Check — runs every 5 minutes via cron
# Usage: ./ipe-health-check.sh [/path/to/logfile]
LOG="${1:-/var/log/ipe-health.log}"
SERVICES="dpe-svc:8001 fea-svc:8004 res-svc:8005 cap-svc:8003 mat-svc:8002 connector:8009"
FAIL=0
TS=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

for entry in $SERVICES; do
    name="${entry%%:*}"
    port="${entry##*:}"
    # Prefer /api/v1/health (compose healthcheck path); fall back to /healthz
    code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}/api/v1/health" --max-time 5 2>/dev/null)
    if [ "$code" != "200" ]; then
        code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}/healthz" --max-time 5 2>/dev/null)
    fi
    if [ "$code" != "200" ]; then
        echo "[${TS}] WARN: ${name} HTTP ${code}" >> "$LOG"
        FAIL=$((FAIL+1))
    fi
done

# DB check — prefer star-trans compose if present
COMPOSE_FILE="${COMPOSE_FILE:-}"
if [ -z "$COMPOSE_FILE" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  if [ -f "${SCRIPT_DIR}/../../deploy/star-trans/docker-compose.yml" ]; then
    COMPOSE_FILE="${SCRIPT_DIR}/../../deploy/star-trans/docker-compose.yml"
  else
    COMPOSE_FILE="docker-compose.yml"
  fi
fi

docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U ipe > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[${TS}] WARN: PostgreSQL down" >> "$LOG"
    FAIL=$((FAIL+1))
fi

# Optional: last sync freshness (connector) — warn only if endpoint responds with stale flag
# Left as soft check; does not invent WhatsApp without webhook URL
if [ -n "${IPE_HEALTH_WEBHOOK:-}" ] && [ "$FAIL" -gt 0 ]; then
    curl -s -X POST "$IPE_HEALTH_WEBHOOK" -H "Content-Type: application/json" \
      -d "{\"text\":\"IPE health WARN failures=${FAIL} at ${TS}\"}" >/dev/null 2>&1 || true
fi

[ $FAIL -eq 0 ] && echo "[${TS}] OK" >> "$LOG"
exit $FAIL
