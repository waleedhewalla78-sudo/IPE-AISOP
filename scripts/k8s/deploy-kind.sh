#!/usr/bin/env bash
# Local kind cluster bootstrap for IPE Helm chart (Phase 3).
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-ipe-dev}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== IPE K8s Local Development Setup (kind) ==="

if ! command -v kind >/dev/null 2>&1; then
  echo "ERROR: kind not installed (https://kind.sigs.k8s.io/)"
  exit 1
fi
if ! command -v helm >/dev/null 2>&1; then
  echo "ERROR: helm not installed"
  exit 1
fi

if ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  cat <<EOF | kind create cluster --name "$CLUSTER_NAME" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
      - containerPort: 443
        hostPort: 443
  - role: worker
EOF
fi

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s || true

kubectl create namespace ipe --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install ipe "$ROOT/helm/ipe" \
  -n ipe \
  -f "$ROOT/helm/ipe/values-dev.yaml" \
  --wait --timeout 600s || {
    echo "Helm install failed — check images/secrets. Templates may still be valid (helm lint)."
    exit 1
  }

kubectl get pods -n ipe
echo "Web UI (when images present): http://localhost:8082"
