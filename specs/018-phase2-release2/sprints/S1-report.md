# Sprint S1 Report — Release 2 Infrastructure

**Sprint**: S1 — R2 environment  
**Date**: 2026-07-10  
**Gate**: G-R2-01 (`release2-smoke.ps1` PASS)  
**Authority**: `specs/018-phase2-release2/tasks.md`, constitution v1.2.4

---

## Summary

Sprint S1 delivers the Release 2 Docker stack, Kong routes for intelligence APIs, frontend `release2` profile (Demand + Scenarios hubs; Copilot inherited from R1), deploy/smoke scripts, and nav regression tests. All S1 code deliverables are complete; gate G-R2-01 remains **FAIL** pending a successful docker deploy + smoke run in this environment.

---

## Deliverables

| ID | Task | Status | Artifact |
|----|------|--------|----------|
| S1-01 | R2 compose overlay | ✅ | `infrastructure/docker/docker-compose.release2.yml` |
| S1-02 | R2 Kong routes | ✅ | `infrastructure/docker/kong.release2.yml` |
| S1-03 | `release2` frontend profile | ✅ | `apps/web/src/lib/releaseProfile.ts`, `Sidebar.tsx` |
| S1-04 | Deploy scripts | ✅ | `scripts/deploy-release2.ps1`, `scripts/deploy-release2.sh` |
| S1-05 | Smoke test | ✅ | `scripts/release2-smoke.ps1`, `scripts/release2-smoke.sh` |
| S1-06 | E2E nav test | ✅ | `apps/web/e2e/release2-nav.spec.ts`, `tests/features/release2/release2-nav.test.tsx` |

---

## Files created / modified

### Created

- `infrastructure/docker/docker-compose.release2.yml` — standalone R2 stack (R1 + nlp/demand/scenario)
- `infrastructure/docker/kong.release2.yml` — R1 routes + `/copilot`, `/nlp`, `/demand`, `/scenario`
- `scripts/deploy-release2.ps1`
- `scripts/deploy-release2.sh`
- `scripts/release2-smoke.ps1`
- `scripts/release2-smoke.sh`
- `apps/web/e2e/release2-nav.spec.ts`
- `apps/web/tests/features/release2/release2-nav.test.tsx`
- `specs/018-phase2-release2/sprints/S1-report.md`

### Modified (non-release1)

- `apps/web/src/lib/releaseProfile.ts` — `IS_RELEASE2`, `RELEASE2_HUBS`, `isHubEnabled()`
- `apps/web/src/components/layout/Sidebar.tsx` — Copilot visible in R2 trimmed profile
- `apps/web/playwright.config.ts` — `release2` Playwright project
- `specs/018-phase2-release2/tasks.md` — S1 items marked done

### Not modified (per constraint)

- All `release1` files unchanged (`docker-compose.release1.yml`, `kong.release1.yml`, `deploy-release1.ps1`, etc.)

---

## Test results

| Test | Command | Result |
|------|---------|--------|
| Vitest R2 nav | `npm test -- tests/features/release2/release2-nav.test.tsx --run` | **PASS** (3/3) |
| Playwright R2 nav | `npx playwright test --project=release2` | **SKIP** — Chromium not installed (`npx playwright install` required) |
| Docker smoke G-R2-01 | `.\scripts\release2-smoke.ps1` | **FAIL** (0/9) — R2 stack not running |
| Docker deploy attempt | `docker compose -f docker-compose.release2.yml up -d --build` | **FAIL** — PyPI download timeouts during image build |

---

## Gate G-R2-01

| Criterion | Status |
|-----------|--------|
| `release2-smoke.ps1` PASS | **FAIL** — services not up on expected ports |
| `VITE_RELEASE_PROFILE=release2` shows Demand + Scenarios | **PASS** (vitest) |
| Copilot visible in R2 nav | **PASS** (vitest) |

**Gate G-R2-01: FAIL** (smoke blocked by environment — no running R2 stack)

---

## Blockers / notes

1. **R2 stack not deployed** — smoke hit connection refused on all service ports (8003–8050, 8020, 8016).
2. **Docker image build** — `uv sync` failed with PyPI timeout (`uvicorn`, `starlette`, `mako`, `prometheus-client`). Retry when network stable.
3. **Port conflicts** — partial `docker-*` compose already bound 8180/9000/8200; stop conflicting stacks before `deploy-release2.ps1`.
4. **Playwright browsers** — run `npx playwright install` in `apps/web` for e2e execution.
5. R2 compose reuses R1 port map (8000 Kong, 8082 web, 5433 db, 6380 redis). Stop R1 stack before deploying R2.
6. Kafka consumers in nlp/demand run with empty bootstrap; health may report `degraded` — smoke accepts `ok` or `degraded`.

### To pass G-R2-01 locally

```powershell
cd ipe\infrastructure\docker
# Stop conflicting stacks first
docker compose -f docker-compose.release2.yml up -d --build
cd ..\..
.\scripts\release2-smoke.ps1
```

---

*S1 report — Phase 2 Release 2 — gate pending deploy*
