#!/usr/bin/env bash
# Run IPE chaos scenarios C1–C6 (demo Docker stack) and summarize results.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/docs/chaos/chaos-post-v8-output.txt"
mkdir -p "$(dirname "$OUT")"

{
  echo "=== IPE Chaos Post-v8 Run ==="
  echo "Started: $(date -Iseconds 2>/dev/null || date)"
  echo ""

  if command -v powershell >/dev/null 2>&1; then
    powershell -ExecutionPolicy Bypass -File "${ROOT}/scripts/run-chaos-scenarios.ps1"
  elif command -v pwsh >/dev/null 2>&1; then
    pwsh -ExecutionPolicy Bypass -File "${ROOT}/scripts/run-chaos-scenarios.ps1"
  else
    echo "ERROR: PowerShell required for C1-C6 on Windows demo stack"
    exit 1
  fi

  echo ""
  echo "=== Summary ==="
  for f in C1-nlp-kill C2-alert-kill C3-kafka-pause-approve C4-kafka-drain C5-pg-connections C6-post-chaos-regression; do
    if grep -q "Result: PASS" "${ROOT}/docs/chaos/${f}.md" 2>/dev/null; then
      echo "${f}: PASS"
    else
      echo "${f}: FAIL or missing"
    fi
  done
  echo "Completed: $(date -Iseconds 2>/dev/null || date)"
} 2>&1 | tee "$OUT"
