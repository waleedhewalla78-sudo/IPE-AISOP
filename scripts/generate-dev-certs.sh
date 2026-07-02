#!/bin/bash
# Generate self-signed TLS certs for Kong HTTPS (:8443)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="${ROOT}/infrastructure/certs"
mkdir -p "${CERT_DIR}"

if command -v openssl >/dev/null 2>&1; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "${CERT_DIR}/ipe-dev.key" \
    -out "${CERT_DIR}/ipe-dev.crt" \
    -subj "/CN=localhost/O=IPE/C=US"
  chmod 600 "${CERT_DIR}/ipe-dev.key"
  chmod 644 "${CERT_DIR}/ipe-dev.crt"
else
  python3 "${ROOT}/scripts/generate-dev-certs.py"
fi
echo "Dev TLS certs ready under ${CERT_DIR}"
