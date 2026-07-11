#!/usr/bin/env bash
# Backup named Docker volumes (Vault, Keycloak, Grafana, Prometheus).
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/volumes}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-ipe}"

mkdir -p "$BACKUP_DIR"

VOLUMES=(
  "${COMPOSE_PROJECT}_vault-data"
  "${COMPOSE_PROJECT}_r1_keycloak_db"
  "${COMPOSE_PROJECT}_grafana_data"
  "${COMPOSE_PROJECT}_prometheus_data"
)

for vol in "${VOLUMES[@]}"; do
  if docker volume inspect "$vol" >/dev/null 2>&1; then
    safe_name="$(echo "$vol" | tr '/' '_')"
    docker run --rm \
      -v "${vol}:/source:ro" \
      -v "${BACKUP_DIR}:/backup" \
      alpine tar czf "/backup/${safe_name}_${TIMESTAMP}.tar.gz" -C /source .
    echo "Backed up volume: $vol"
  else
    echo "Skipping missing volume: $vol"
  fi
done
