#!/bin/bash
# Rotate JWT RS256 keys — backs up current pair and generates new signing keys.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEY_DIR="${ROOT}/config/keys"
TRUSTED="${KEY_DIR}/trusted"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"
NEW_KID="ipe-rs256-v2"

mkdir -p "${TRUSTED}"

if [[ -f "${KEY_DIR}/jwt-public.pem" ]]; then
  cp "${KEY_DIR}/jwt-private.pem" "${KEY_DIR}/jwt-private.pem.bak.${TIMESTAMP}"
  cp "${KEY_DIR}/jwt-public.pem" "${KEY_DIR}/jwt-public.pem.bak.${TIMESTAMP}"
  cp "${KEY_DIR}/jwt-public.pem" "${TRUSTED}/jwt-public.pem.v1"
fi

python3 "${ROOT}/scripts/generate-jwt-keys.py"

echo "Keys rotated. Set JWT_KEY_ID=${NEW_KID} after distributing trusted public keys."
echo "Old public key archived to ${TRUSTED}/jwt-public.pem.v1"
