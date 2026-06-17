#!/usr/bin/env bash
set -euo pipefail

echo "Generating TypeScript types from OpenAPI specs..."

# Requires openapi-typescript: pnpm add -D openapi-typescript

SERVICES=(dpe-svc mat-svc cap-svc fea-svc res-svc del-svc nlp-svc)

for svc in "${SERVICES[@]}"; do
  echo "  Generating types for $svc..."
  npx openapi-typescript "http://localhost:${svc#*-svc}" \
    --output "apps/web/src/types/generated/$svc.ts" 2>/dev/null || \
    echo "  [WARN] Could not generate types for $svc (service not running?)"
done

echo "Type generation complete."
