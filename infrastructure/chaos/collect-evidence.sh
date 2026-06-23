#!/usr/bin/env bash
# Collect Chaos Mesh recovery evidence for R4 release gate.
set -euo pipefail

NAMESPACE="${CHAOS_NAMESPACE:-ipe-platform}"
OUT_DIR="${CHAOS_EVIDENCE_DIR:-specs/003-autonomous-planning-v5/evidence/r4}"
mkdir -p "$OUT_DIR"

REPORT="$OUT_DIR/chaos-recovery-metrics.txt"
{
  echo "IPE Chaos Recovery Evidence"
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "Namespace: $NAMESPACE"
  echo ""
  echo "=== Pod status ==="
  kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null || echo "(kubectl unavailable)"
  echo ""
  echo "=== Recent chaos events ==="
  kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' 2>/dev/null | tail -n 40 || true
  echo ""
  echo "=== Chaos resources ==="
  kubectl get networkchaos,podchaos,stresschaos -n "$NAMESPACE" 2>/dev/null || echo "(no chaos CRDs)"
} > "$REPORT"

echo "Evidence written: $REPORT"
