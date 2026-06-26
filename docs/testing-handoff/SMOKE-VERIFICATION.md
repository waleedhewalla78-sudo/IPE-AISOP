# Pre-Test Smoke Verification — v7.0.0

**Date:** 2026-06-26  
**Git:** `master` @ post-v7.0.0 handoff  
**Stack:** REL-STACK demo overlay (already running)

## Git parity

```
git pull origin master  → Already up to date
git checkout v7.0.0     → (optional for frozen test baseline)
```

Uncommitted local files: log artifacts and `.kms_keys/` only — **not** part of release.

## API health smoke (2026-06-26)

| Endpoint | Status |
|----------|--------|
| `http://localhost:8000/api/v1/health` (Kong) | **200** |
| `http://localhost:8020/api/v1/health` (dpe-svc) | **200** |
| `http://localhost:8002/api/v1/health` (mat-svc) | **200** |
| `http://localhost:8003/api/v1/health` (cap-svc) | **200** |
| `http://localhost:8004/api/v1/health` (fea-svc) | **200** |
| `http://localhost:8007/api/v1/health` (nlp-svc) | **200** |
| `http://localhost:8010/api/v1/health` (alert-svc) | **200** |
| `http://localhost:8082` (React UI) | **Not running** — start `apps/web` per QUICK-START |

> Use `/api/v1/health` on direct service ports. `/healthz` may not be exposed on all direct port mappings.

## Documentation verification

All required docs present (A-05 check): README, CHANGELOG, CONTRIBUTING, architecture, API reference, deployment, runbooks, `.env.example`, `docker-compose.yml`.

## Tester action

Before manual UAT, run:

```powershell
cd apps\web && npm install && npm run dev
```

Then proceed with [HUMAN-TEST-PLAN.md](HUMAN-TEST-PLAN.md).
