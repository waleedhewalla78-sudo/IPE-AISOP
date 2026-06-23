# Quickstart: Release Stabilization Validation

**Feature**: 002-release-stabilization-gates  
**Goal**: Prove the product is finalize-ready in one session (~4 hours first run)

---

## Prerequisites

- Docker Desktop running
- Python 3.12+ with `uv` installed
- Node 20+ with `pnpm` installed
- k6 installed (Gate 2 only)
- Ports available: **5433** (Postgres host map), 6380, 8020, 8002–8016, 9092

---

## Step 1: Environment Setup (30 min)

```powershell
cd D:\AISOP\ipe

# Copy and edit secrets
copy .env.template .env
# Set at minimum (names must use IPE_ prefix — see .env.template):
#   IPE_JWT_SECRET_KEY=dev-jwt-secret-change-in-production-min-32-chars
#   IPE_DATABASE_URL=postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev

uv sync
cd apps\web && pnpm install && cd ..\..
```

**Expected**: No errors from `uv sync` or `pnpm install`.

---

## Step 0: One-Command Product Demo (optional)

```powershell
cd D:\AISOP\ipe
.\scripts\start-product.ps1
```

Opens **http://localhost:8082** — login `admin@demo.com` / `demo`. See `GETTING-STARTED.md`.

---

## Step 2: Gate 1 — Unit Tests (60–90 min)

```powershell
# Shared library (JWT must pass after .env configured)
cd services\shared
$env:IPE_JWT_SECRET_KEY = "dev-jwt-secret-change-in-production-min-32-chars"
uv run pytest tests -v --tb=short
cd ..\..

# dpe-svc (must collect without GL_ACCOUNT_MAP error)
cd services\dpe-svc
uv run pytest tests -q
cd ..\..

# cap-svc (must complete without OTel I/O error)
cd services\cap-svc
$env:OTEL_SDK_DISABLED = "true"
uv run pytest tests -q
cd ..\..

# Remaining services
foreach ($svc in @("mat-svc","fea-svc","res-svc","del-svc","nlp-svc","rec-svc","alert-svc","network-svc","scn-svc","quality-svc","sustain-svc","connector","ml-svc")) {
  Write-Host "Testing $svc..."
  cd "services\$svc"
  uv run pytest tests -q --tb=no
  cd ..\..
}

# Frontend
cd apps\web
pnpm test -- --run
pnpm typecheck
cd ..\..
```

**Expected**:
- Zero collection/import errors
- shared: ≥123 passed, JWT 3/3 pass
- dpe-svc: full suite passes
- cap-svc: full suite completes (exit 0)

**Evidence**: Save output to `specs/002-release-stabilization-gates/evidence/gate-1/`

---

## Step 3: Gate 2 — Docker Stack (45 min)

```powershell
cd D:\AISOP\ipe

docker compose -f infrastructure/docker/docker-compose.yml up -d

# Wait for migrate + health (≤90 seconds)
Start-Sleep -Seconds 90
docker compose -f infrastructure/docker/docker-compose.yml ps

# Health spot-check (tenant header required)
$tenant = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
curl -s -H "X-Tenant-ID: $tenant" http://localhost:8020/api/v1/health
curl -s -H "X-Tenant-ID: $tenant" http://localhost:8002/api/v1/health
curl -s -H "X-Tenant-ID: $tenant" http://localhost:8003/api/v1/health
curl -s -H "X-Tenant-ID: $tenant" http://localhost:8004/api/v1/health
```

**Expected**: All services `Up`; health returns `"status":"ok"` or equivalent JSON.

```powershell
# Seed data
bash scripts/seed-data.sh   # or WSL equivalent
```

---

## Step 4: Gate 2 — Integration E2E (30 min)

```powershell
cd D:\AISOP\ipe

# Sprint 2 integration (15 tests)
uv run pytest tests/integration/test_sprint2_e2e.py -v

# Phase 5-6 integration (16 tests)
uv run pytest tests/integration/test_phase5_6_e2e.py -v

# Critical path script
uv run python scripts/e2e/critical_path_test.py
```

**Expected**: ≥15/15 + ≥16/16 pass (31 total).

---

## Step 5: Gate 2 — Load Smoke (15 min)

```powershell
k6 run tests/performance/k6/load-test-phase56.js
```

**Expected**:
- `http_req_failed`: 0%
- `http_req_duration` p(95) < 2000ms

---

## Step 6: Gate 3 — Documentation Check (30 min)

1. Open [CROSS-ARTIFACT-ANALYSIS.md](../CROSS-ARTIFACT-ANALYSIS.md) — verify CRITICAL/HIGH items marked resolved
2. Open [READINESS.md](../../READINESS.md) (created in Gate 3) — single score **85/100**
3. Complete checklists:
   - [gate-1-engineering.md](./contracts/gate-1-engineering.md)
   - [gate-2-operations.md](./contracts/gate-2-operations.md)
   - [gate-3-release.md](./contracts/gate-3-release.md)

---

## Step 7: Release Tag (Gate 3)

After Gates 1–2 green and docs reconciled:

```powershell
git add -A
git commit -m "chore(release): stabilize for v1.0.0-rc1"
git tag v1.0.0-rc1
```

**Expected**: Fresh checkout at tag passes Steps 2–4.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Redis port conflict | Use host port 6380 per docker-compose |
| dpe-svc port conflict | Use external 8020 |
| JWT tests fail | Set `JWT_SECRET_KEY` in `.env` and test env |
| dpe-svc collection error | Update `test_cost_accounting.py` imports |
| cap-svc OTel crash | Set `OTEL_SDK_DISABLED=true` in tests |
| E2E 500 errors | Run `migrate` service first; check DB has tables |
| Keycloak tests | **BLOCKED** — skip; do not claim SSO ready |

---

## References

- [plan.md](./plan.md) — full 3-week implementation plan
- [research.md](./research.md) — readiness score and test count decisions
- [data-model.md](./data-model.md) — gate and evidence entities
- [Makefile](../../Makefile) — Linux equivalents (`make test`, `make docker-up`)
