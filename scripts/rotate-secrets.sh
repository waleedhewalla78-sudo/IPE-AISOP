#!/usr/bin/env bash
# Rotate dev secrets in Vault (manual trigger; production uses Vault policies + automation).
set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-ipe-dev-root}"
MOUNT="${VAULT_KV_MOUNT:-ipe}"

export VAULT_ADDR VAULT_TOKEN

NEW_DB_PASS="${1:-ipe_test_pass_$(date +%s)}"
vault kv put "${MOUNT}/database" password="${NEW_DB_PASS}"
echo "Rotated ${MOUNT}/database password (update compose/DB to apply)."

NEW_JWT="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))' 2>/dev/null || openssl rand -base64 48)"
vault kv put "${MOUNT}/jwt" secret="${NEW_JWT}"
echo "Rotated ${MOUNT}/jwt secret."

echo "Run scripts/vault-init.sh to re-seed defaults if needed."
