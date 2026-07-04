#!/usr/bin/env bash
# Gate 6 — Helm lint and template render (no cluster required)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHART="${ROOT}/helm/ipe"

if ! command -v helm >/dev/null 2>&1; then
  echo "SKIP: helm not installed — install Helm 3.14+ and re-run"
  exit 0
fi

echo "=== Gate 6: Helm lint + template ==="
helm lint "${CHART}" -f "${CHART}/values-release1.yaml"
helm lint "${CHART}" -f "${CHART}/values-prod.yaml"
helm template ipe "${CHART}" -f "${CHART}/values-release1.yaml" >/dev/null
helm template ipe "${CHART}" -f "${CHART}/values-prod.yaml" >/dev/null
echo "GATE 6: PASS"
