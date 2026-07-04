#!/usr/bin/env bash
# Provision / verify Grafana for IPE Phase 2 monitoring stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKER_DIR="${ROOT}/infrastructure/docker"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_ADMIN_USER:-admin}"
GRAFANA_PASS="${GRAFANA_ADMIN_PASSWORD:-admin}"

echo "=== IPE Grafana setup (Phase 2) ==="

if ! docker network inspect ipe-network >/dev/null 2>&1; then
  echo "Creating docker network ipe-network..."
  docker network create ipe-network
fi

cd "${DOCKER_DIR}"
docker compose -f docker-compose.monitoring.yml up -d

echo "Waiting for Grafana..."
for _ in $(seq 1 30); do
  if curl -sf "${GRAFANA_URL}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sf "${GRAFANA_URL}/api/health" >/dev/null 2>&1; then
  echo "ERROR: Grafana not healthy at ${GRAFANA_URL}" >&2
  exit 1
fi

echo "Grafana health: OK"
echo "Datasources:"
curl -sf -u "${GRAFANA_USER}:${GRAFANA_PASS}" "${GRAFANA_URL}/api/datasources" | \
  python3 -c "import sys,json; ds=json.load(sys.stdin); print('\n'.join(f\"  - {d['name']} ({d['type']})\" for d in ds))" 2>/dev/null || \
  echo "  (login required — default admin/admin)"

echo ""
echo "Dashboards folder: ${DOCKER_DIR}/grafana/dashboards"
echo "  - api-latency.json"
echo "  - api-error-rate.json"
echo "  - kafka-lag.json"
echo "  - db-pool.json"
echo "  - mdr-scores.json"
echo ""
echo "Grafana UI: ${GRAFANA_URL} (${GRAFANA_USER} / ${GRAFANA_PASS})"
echo "Prometheus: http://localhost:9090"
echo "Alertmanager: http://localhost:9093"
