#!/usr/bin/env bash
# Seed HashiCorp Vault KV v2 secrets for IPE Release 1 (dev mode).
set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-ipe-dev-root}"
MOUNT="${VAULT_KV_MOUNT:-ipe}"

echo "Waiting for Vault at ${VAULT_ADDR} ..."
for i in $(seq 1 30); do
  if vault status >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

export VAULT_ADDR VAULT_TOKEN

vault secrets enable -path="${MOUNT}" kv-v2 2>/dev/null || true

vault kv put "${MOUNT}/database" \
  password="${IPE_DB_PASSWORD:-ipe_test_pass}" \
  user="${IPE_DB_USER:-ipe}" \
  host="${IPE_DB_HOST:-db}"

vault kv put "${MOUNT}/jwt" \
  secret="${IPE_JWT_SECRET_KEY:-dev-only-change-in-production-min-32-chars-long!!}"

vault kv put "${MOUNT}/odoo" \
  password="${ODOO_PASSWORD:-admin}" \
  url="${ODOO_URL:-http://host.docker.internal:8069}"

vault kv put "${MOUNT}/keycloak" \
  admin_password="${KEYCLOAK_ADMIN_PASSWORD:-admin}"

echo "Vault KV mount '${MOUNT}' seeded."
vault kv list "${MOUNT}/" || true
