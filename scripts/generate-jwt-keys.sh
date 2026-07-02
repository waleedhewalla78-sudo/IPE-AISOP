#!/bin/bash
# Generates RS256 key pair for JWT signing (requires openssl or python fallback)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEY_DIR="${ROOT}/config/keys"
mkdir -p "${KEY_DIR}/trusted"

if command -v openssl >/dev/null 2>&1; then
  openssl genrsa -out "${KEY_DIR}/jwt-private.pem" 4096
  openssl rsa -in "${KEY_DIR}/jwt-private.pem" -pubout -out "${KEY_DIR}/jwt-public.pem"
  chmod 600 "${KEY_DIR}/jwt-private.pem"
  chmod 644 "${KEY_DIR}/jwt-public.pem"
else
  python3 "${ROOT}/scripts/generate-jwt-keys.py"
fi

cp "${KEY_DIR}/jwt-public.pem" "${KEY_DIR}/jwt-public.pem.example"
echo "Keys ready under ${KEY_DIR}"
