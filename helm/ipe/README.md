# IPE Helm Chart

Phase 3 Kubernetes packaging for the Intelligent Planning Engine.

## Install

```bash
# Lint
helm lint ./helm/ipe -f helm/ipe/values-release1.yaml

# Dry-run render
helm template ipe ./helm/ipe -f helm/ipe/values-release1.yaml

# Install (Release 1 profile)
helm upgrade --install ipe ./helm/ipe -n ipe --create-namespace \
  -f helm/ipe/values-release1.yaml
```

## Profiles

| Values file | Description |
|-------------|-------------|
| `values.yaml` | Base defaults (full enterprise-oriented) |
| `values-dev.yaml` | kind / local |
| `values-release1.yaml` | Star Trans 8-service minimal |
| `values-prod.yaml` | Full stack |

## Optional generator

Per-service YAML files can be regenerated with:

```bash
python scripts/helm/generate-templates.py
```

The chart uses **ranged** templates (`deployments.yaml`, `services.yaml`, `hpa.yaml`, `pdb.yaml`) by default — no generator required for install.

## Docs

- Operations: `docs/operations/K8S-DEPLOYMENT-GUIDE.md`
- Verify: `scripts/k8s/verify-k8s.sh`
