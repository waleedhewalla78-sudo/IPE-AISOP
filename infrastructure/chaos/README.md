# IPE Chaos Mesh — Staging Experiments

Chaos experiments validate production resilience SLOs for R4 exit gate **SC-011**:

| Experiment | Target | Recovery SLO |
|------------|--------|--------------|
| `kafka-pod-kill.yaml` | Kafka broker | < 30s |
| `postgres-failover.yaml` | PostgreSQL primary | < 15s |
| `redis-pod-kill.yaml` | Redis | < 30s |
| `kafka-network-partition.yaml` | Kafka ↔ Zookeeper | < 60s |
| `cpu-pressure.yaml` | dpe-svc | graceful degradation |

## Prerequisites

1. Kubernetes staging cluster with namespace `ipe-platform` (override via `CHAOS_NAMESPACE`).
2. [Chaos Mesh](https://chaos-mesh.org/docs/production-installation/using-helm/) installed:

```bash
helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh --create-namespace
```

## Run experiments

**Linux/macOS:**

```bash
./infrastructure/chaos/run-chaos.sh
./infrastructure/chaos/collect-evidence.sh
```

**Windows:**

```powershell
.\infrastructure\chaos\run-chaos.ps1
.\infrastructure\chaos\collect-evidence.ps1
```

## Evidence

Store signed output under `specs/003-autonomous-planning-v5/evidence/r4/`:

- `chaos-run-report.txt` — experiment apply log
- `chaos-recovery-metrics.txt` — pod recovery timestamps from `collect-evidence`

Attach both files to the v1.0.0 release checklist before production promotion.
