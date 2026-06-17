#!/usr/bin/env bash
#
# provision-tenant.sh
#
# Provisions a new tenant in the IPE platform.
# Usage: ./provision-tenant.sh --tenant-name ACME --tier enterprise [--admin-email admin@acme.com]
#
# Requires:
#   - psql client connected to the IPE database
#   - IPE_DATABASE_URL environment variable (or --db-url argument)
#   - uuidgen command
#

set -euo pipefail

# --- Argument parsing ---
TENANT_NAME=""
TIER="standard"
ADMIN_EMAIL=""
DB_URL="${IPE_DATABASE_URL:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tenant-name)   TENANT_NAME="$2";   shift 2 ;;
    --tier)          TIER="$2";           shift 2 ;;
    --admin-email)   ADMIN_EMAIL="$2";    shift 2 ;;
    --db-url)        DB_URL="$2";         shift 2 ;;
    --help)
      echo "Usage: $0 --tenant-name NAME --tier TIER [--admin-email EMAIL] [--db-url URL]"
      echo ""
      echo "Provisions a new tenant in the IPE platform."
      echo ""
      echo "Arguments:"
      echo "  --tenant-name NAME   Tenant name (required)"
      echo "  --tier TIER          Tier: standard | enterprise (default: standard)"
      echo "  --admin-email EMAIL  Admin user email (auto-generated if omitted)"
      echo "  --db-url URL         Postgres DSN (default: \$IPE_DATABASE_URL)"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$TENANT_NAME" ]]; then
  echo "ERROR: --tenant-name is required"
  exit 1
fi

if [[ -z "$DB_URL" ]]; then
  echo "ERROR: --db-url or IPE_DATABASE_URL is required"
  exit 1
fi

# --- Generate IDs ---
TENANT_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
ADMIN_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
CONNECTOR_API_KEY=$(uuidgen | tr -d '-' | head -c 32)
ADMIN_PASSWORD=$(uuidgen | tr -d '-' | head -c 16)

if [[ -z "$ADMIN_EMAIL" ]]; then
  ADMIN_EMAIL="admin@${TENANT_NAME,,}.com"
fi

echo "=== Provisioning Tenant: $TENANT_NAME ==="
echo "  Tenant UUID:  $TENANT_UUID"
echo "  Tier:         $TIER"
echo "  Admin Email:  $ADMIN_EMAIL"
echo ""

# --- Create tenant record ---
psql "$DB_URL" -v ON_ERROR_STOP=1 <<SQL
INSERT INTO cdm_tenant (id, name, tier, config, created_at, updated_at)
VALUES (
  '$TENANT_UUID',
  '$TENANT_NAME',
  '$TIER',
  jsonb_build_object(
    'priority_weights', jsonb_build_object('demand_urgency', 0.4, 'customer_priority', 0.3, 'strategic_value', 0.2, 'promised_date', 0.1),
    'auto_resolve_threshold', 90,
    'shadow_mode', true,
    'max_concurrent_mos', CASE WHEN '$TIER' = 'enterprise' THEN 500 ELSE 100 END,
    'alert_channels', jsonb_build_array('email'),
    'data_retention_days', 365
  ),
  NOW(),
  NOW()
);
SQL

echo "  [OK] Tenant record created in cdm_tenant"

# --- Create admin user ---
psql "$DB_URL" -v ON_ERROR_STOP=1 <<SQL
INSERT INTO cdm_user (id, tenant_id, email, role, password_hash, is_active, created_at)
VALUES (
  '$ADMIN_UUID',
  '$TENANT_UUID',
  '$ADMIN_EMAIL',
  'admin',
  crypt('$ADMIN_PASSWORD', gen_salt('bf')),
  true,
  NOW()
);
SQL

echo "  [OK] Admin user created"
echo "  [!!] Admin password: $ADMIN_PASSWORD (save this immediately)"

# --- Generate and store connector API key ---
psql "$DB_URL" -v ON_ERROR_STOP=1 <<SQL
INSERT INTO ipe_connector_config (tenant_id, api_key, hmac_enabled, created_at)
VALUES (
  '$TENANT_UUID',
  crypt('$CONNECTOR_API_KEY', gen_salt('bf')),
  true,
  NOW()
);
SQL

echo "  [OK] Connector API key generated"
echo "  [!!] Connector API Key: $CONNECTOR_API_KEY (save this immediately)"
echo ""

# --- Print summary ---
echo "=== PROVISIONING COMPLETE ==="
echo ""
echo "Tenant Summary:"
echo "  Name:           $TENANT_NAME"
echo "  UUID:           $TENANT_UUID"
echo "  Tier:           $TIER"
echo "  Admin Email:    $ADMIN_EMAIL"
echo "  Admin Password: $ADMIN_PASSWORD"
echo "  Connector Key:  $CONNECTOR_API_KEY"
echo ""
echo "Next steps:"
echo "  1. Share admin credentials with tenant admin securely"
echo "  2. Configure Odoo connector with the API key"
echo "  3. Begin Week 1 data integration (see docs/runbooks/tenant-onboarding.md)"
