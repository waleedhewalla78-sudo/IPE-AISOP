#!/usr/bin/env bash
# Chaos Mesh experiment runner for IPE platform staging environment.
# Prerequisites: Chaos Mesh installed in cluster (helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${CHAOS_NAMESPACE:-ipe-platform}"

echo "=== IPE Chaos Mesh Experiments ==="
echo "Namespace: $NAMESPACE"
echo ""

apply_experiment() {
    local name="$1"
    local file="$2"
    echo "Applying: $name..."
    if kubectl apply -f "$file" -n "$NAMESPACE" 2>/dev/null; then
        echo "  ✓ Applied"
    else
        echo "  ⚠ Skipped (namespace or CRD not found)"
    fi
}

echo "Phase 1: Kafka pod kill..."
apply_experiment "kafka-pod-kill" "$SCRIPT_DIR/kafka-pod-kill.yaml"
sleep 5

echo "Phase 2: Postgres failover..."
apply_experiment "postgres-failover" "$SCRIPT_DIR/postgres-failover.yaml"
sleep 5

echo "Phase 3: Redis pod kill..."
apply_experiment "redis-pod-kill" "$SCRIPT_DIR/redis-pod-kill.yaml"
sleep 5

echo "Phase 4: Network partition (Kafka↔Zookeeper)..."
apply_experiment "kafka-network-partition" "$SCRIPT_DIR/kafka-network-partition.yaml"
sleep 5

echo "Phase 5: CPU pressure on dpe-svc..."
apply_experiment "cpu-pressure" "$SCRIPT_DIR/cpu-pressure.yaml"

echo ""
echo "=== All chaos experiments applied ==="
echo "Monitor with: kubectl get pods -n $NAMESPACE"
echo "Check events with: kubectl get events -n $NAMESPACE --field-selector reason=ChaosKill"
