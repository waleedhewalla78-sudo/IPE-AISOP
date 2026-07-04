#!/usr/bin/env bash
set -euo pipefail
echo "=== IPE K8s Verification ==="
NS="${NS:-ipe}"

echo "1. Pod Status"
kubectl get pods -n "$NS" -o wide || true

echo ""
echo "2. Service Status"
kubectl get svc -n "$NS" || true

echo ""
echo "3. HPA Status"
kubectl get hpa -n "$NS" || true

echo ""
echo "4. PDB Status"
kubectl get pdb -n "$NS" || true

echo ""
echo "5. Network Policies"
kubectl get networkpolicy -n "$NS" || true

echo ""
echo "6. Health Check (enabled services)"
for svc in dpe-svc fea-svc cap-svc mat-svc connector res-svc; do
  POD=$(kubectl get pod -n "$NS" -l "app.kubernetes.io/name=$svc" \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
  if [ -n "${POD:-}" ]; then
    PORT=$(kubectl get deploy -n "$NS" "$svc" -o jsonpath='{.spec.template.spec.containers[0].ports[0].containerPort}' 2>/dev/null || echo "8001")
    STATUS=$(kubectl exec -n "$NS" "$POD" -- \
      python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:${PORT}/api/v1/health', timeout=5).status)" \
      2>/dev/null || echo "UNREACHABLE")
    echo "  $svc ($POD): $STATUS"
  else
    echo "  $svc: no pod"
  fi
done

echo ""
echo "=== Verification Complete ==="
