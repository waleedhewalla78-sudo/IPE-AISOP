# IPE Kubernetes Deployment Guide

**Phase:** 3 (v9.4.0-p3 target)  
**Chart:** `helm/ipe`  
**Last updated:** 2026-07-04

## Prerequisites

- `kubectl` ≥ 1.28
- `helm` ≥ 3.14
- Container registry access (e.g. `ghcr.io`)
- Cluster: kind (local), AKS, EKS, GKE, or on-prem

## Quick Start

### Local development (kind)

```bash
bash scripts/k8s/deploy-kind.sh
bash scripts/k8s/verify-k8s.sh
```

### Release 1 (customer — minimal)

```bash
helm upgrade --install ipe ./helm/ipe -n ipe --create-namespace \
  -f helm/ipe/values-release1.yaml
```

### Full enterprise

```bash
helm upgrade --install ipe ./helm/ipe -n ipe --create-namespace \
  -f helm/ipe/values-prod.yaml
```

## Configuration profiles

| File | Use |
|------|-----|
| `values.yaml` | Base defaults |
| `values-dev.yaml` | kind / local |
| `values-release1.yaml` | Star Trans 8-service profile |
| `values-prod.yaml` | Full stack + enterprise flags |

## Secrets

Create before install (do not commit real values):

```bash
kubectl -n ipe create secret generic ipe-db-secret \
  --from-literal=url='postgresql+asyncpg://ipe:pass@postgresql:5432/ipe'
kubectl -n ipe create secret generic ipe-redis-secret \
  --from-literal=url='redis://:pass@redis:6379/0'
```

Chart `templates/secrets.yaml` ships placeholders for bootstrap only.

## Scaling

```bash
kubectl scale deployment dpe-svc --replicas=5 -n ipe
kubectl get hpa -n ipe
```

## Rollback

```bash
helm history ipe -n ipe
helm rollback ipe 1 -n ipe
```

## Compose ↔ K8s parity

With both stacks up:

```bash
export IPE_TOKEN=<jwt>
python scripts/k8s/test-compose-k8s-parity.py
```

## Resource guidance

| Profile | Min nodes | RAM / node | Notes |
|---------|-----------|------------|-------|
| Release 1 | 1 | 4–8 GB | Matches 8GB VM target |
| Full | 3 | 8 GB | All services |
| Enterprise HA | 5 | 16 GB | Keycloak + Vault + monitoring |

## Lint / dry-run (Gate 6)

```bash
helm lint ./helm/ipe -f helm/ipe/values-prod.yaml
helm lint ./helm/ipe -f helm/ipe/values-release1.yaml
helm template ipe ./helm/ipe -f helm/ipe/values-release1.yaml > /dev/null
```

## Troubleshooting

```bash
kubectl logs -n ipe deploy/dpe-svc
kubectl describe pod -n ipe -l app.kubernetes.io/name=dpe-svc
kubectl get networkpolicy -n ipe
```
