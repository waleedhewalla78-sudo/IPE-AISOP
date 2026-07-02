#!/usr/bin/env bash
# Wait for Keycloak and print OIDC configuration for IPE Release 1.
set -euo pipefail

KC_URL="${KEYCLOAK_URL:-http://localhost:8180}"
KC_ADMIN="${KEYCLOAK_ADMIN_USER:-admin}"
KC_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
REALM="${KEYCLOAK_REALM:-ipe}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-ipe-platform}"

echo "Waiting for Keycloak at ${KC_URL} ..."
for i in $(seq 1 60); do
  if curl -sf "${KC_URL}/health/ready" >/dev/null 2>&1; then
    echo "Keycloak is ready."
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "Keycloak did not become ready in time." >&2
    exit 1
  fi
  sleep 2
done

echo ""
echo "IPE Keycloak SSO configuration"
echo "  Realm:        ${REALM}"
echo "  Client ID:    ${CLIENT_ID}"
echo "  Admin console: ${KC_URL}/admin (user: ${KC_ADMIN})"
echo "  OIDC issuer:  ${KC_URL}/realms/${REALM}"
echo "  JWKS:         ${KC_URL}/realms/${REALM}/protocol/openid-connect/certs"
echo ""
echo "Demo users (realm ${REALM}):"
echo "  admin / admin       (role: admin)"
echo "  planner / planner   (role: planner)"
echo "  ahmed / admin       (role: planner, Star Trans tenant)"
echo ""
echo "To enable Keycloak auth in Release 1:"
echo "  1. Set AUTH_MODE=keycloak and AUTH_PROVIDER=keycloak in infrastructure/docker/ipe-common.env"
echo "  2. docker compose -f infrastructure/docker/docker-compose.release1.yml up -d --build"
echo "  3. Open http://localhost:8082 and sign in with SSO"
