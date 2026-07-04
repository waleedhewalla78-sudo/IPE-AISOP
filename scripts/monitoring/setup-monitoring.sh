#!/usr/bin/env bash
set -euo pipefail
echo "=== IPE Monitoring Stack Setup ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MONITORING_DIR="$PROJECT_ROOT/infrastructure/monitoring"
DOCKER_DIR="$PROJECT_ROOT/infrastructure/docker"

# Ensure config directories exist
mkdir -p "$MONITORING_DIR"/{prometheus,grafana/{provisioning/{datasources,dashboards},dashboards},alertmanager}

COMPOSE=(docker compose
  -f "$DOCKER_DIR/docker-compose.release1.yml"
  -f "$DOCKER_DIR/docker-compose.network.yml"
  -f "$DOCKER_DIR/docker-compose.monitoring.yml")

# Start monitoring stack (requires Release 1 app stack on segmented networks)
echo "Starting Prometheus + Grafana + Alertmanager..."
MONITORING_SERVICES=(prometheus grafana alertmanager postgres-exporter redis-exporter node-exporter)
# Kafka exporter only when kafka is defined in the merged compose project
if docker compose "${COMPOSE[@]}" config --services 2>/dev/null | grep -qx kafka; then
  MONITORING_SERVICES+=(kafka-exporter)
else
  echo "  (skipping kafka-exporter — no kafka service in compose profile)"
fi
"${COMPOSE[@]}" up -d "${MONITORING_SERVICES[@]}"

echo "Waiting for services to start..."
sleep 10

# Verify
echo ""
echo "=== Verification ==="
curl -sf http://localhost:9090/-/healthy && echo "Prometheus: OK" || echo "Prometheus: FAIL"
curl -sf http://localhost:3000/api/health && echo "Grafana: OK" || echo "Grafana: FAIL"
curl -sf http://localhost:9093/-/ready && echo "Alertmanager: OK" || echo "Alertmanager: FAIL"

echo ""
echo "=== Access Points ==="
echo "  Prometheus:   http://localhost:9090"
echo "  Grafana:      http://localhost:3000 (admin/admin — change in production)"
echo "  Alertmanager: http://localhost:9093"
echo ""
echo "=== Next Steps ==="
echo "  1. Verify /metrics on each service: curl http://localhost:8000/api/v1/<svc>/metrics"
echo "  2. Check Prometheus targets: http://localhost:9090/targets"
echo "  3. Import dashboards or verify auto-provisioning in Grafana"
