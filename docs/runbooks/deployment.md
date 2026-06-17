# Deployment Runbook

## Staging

- Auto-deployed from `develop` branch via GitHub Actions
- ArgoCD syncs K8s manifests from `infrastructure/k8s/overlays/staging`
- Manual approval required for production

## Production

- Deploy via GitHub release tags (`v*`)
- ArgoCD syncs from `infrastructure/k8s/overlays/production`
- Rolling update strategy (maxSurge=1, maxUnavailable=0)

## Rollback

```bash
kubectl rollout undo deployment/ipe-dpe-svc -n ipe
kubectl rollout status deployment/ipe-dpe-svc -n ipe
```
