#!/usr/bin/env bash
# Deploy IPE Release 2 stack (R1 + nlp-svc, demand-svc, scenario-svc)
set -euo pipefail

ENVIRONMENT="${1:-staging}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_DIR="$ROOT/infrastructure/docker"

echo "=== IPE Release 2 deploy ($ENVIRONMENT) ==="
cd "$COMPOSE_DIR"

docker compose -f docker-compose.release2.yml pull 2>/dev/null || true
docker compose -f docker-compose.release2.yml up -d --build

echo "Waiting for Kong..."
deadline=$((SECONDS + 480))
until curl -sf "http://localhost:8000/api/v1/health" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "Kong health timeout"
    exit 1
  fi
  sleep 3
done

echo "Waiting for R2 services..."
for url in \
  "http://localhost:8007/api/v1/health" \
  "http://localhost:8040/api/v1/health" \
  "http://localhost:8050/api/v1/health"; do
  svc_deadline=$((SECONDS + 180))
  until curl -sf "$url" >/dev/null 2>&1; do
    if (( SECONDS >= svc_deadline )); then
      echo "Timeout waiting for $url"
      exit 1
    fi
    sleep 3
  done
done

echo "Release 2 stack up. Web UI: http://localhost:8082"
echo "Smoke: ./scripts/release2-smoke.ps1 or bash ./scripts/release2-smoke.sh"
