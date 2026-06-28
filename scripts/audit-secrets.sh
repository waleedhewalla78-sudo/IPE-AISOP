#!/usr/bin/env bash
# Audit codebase for potential hardcoded secrets (dev hygiene).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Scanning $ROOT for secret patterns..."
rg -n --glob '!**/node_modules/**' --glob '!**/.git/**' \
  -e 'password\s*=' -e 'secret\s*=' -e 'api_key\s*=' -e 'token\s*=' \
  "$ROOT" 2>/dev/null | head -80 || true
echo "Review config/secrets.env.example for required secrets."
