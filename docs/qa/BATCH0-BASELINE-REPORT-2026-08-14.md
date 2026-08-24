# BATCH0 Baseline Health Check — 2026-08-15

**Branch:** `033-phase9-wave9a`  
**Spec:** `040-startrans-demo-aug18`  
**Constitution:** v1.4.7  

---

## 1. Repository state

| Item | Result |
|------|--------|
| Branch | `033-phase9-wave9a` ✓ |
| STREAM-1…7 + STREAM-040 commits | Present in last 30 ✓ |
| Working tree | **DIRTY** — many pre-existing modified/untracked files outside Spec 040 (not discarded) |

## 2. Spec Kit alignment

| Item | Result |
|------|--------|
| `feature.json` | `specs/040-startrans-demo-aug18` ✓ |
| tasks T001–T062 | checked ✓ |
| T063–T066 / T090–T097 | unchecked ✓ |
| Constitution | **1.4.7** ✓ |

## 3. Frontend build health

| Check | Result |
|-------|--------|
| `npm install` | OK |
| `tsc --noEmit` | **0 errors** after fixes (EmptyState API, schedule imports, api default import, frappe CSS) |
| `npm run build` | **PASS** (~43s); DetailedSchedulePage chunk ~55.7 kB |

## 4. Backend surface check

| Path | Status |
|------|--------|
| `startrans_workbook.py` | Present |
| `startrans_ingest.py` | Present |
| `api/v1/data_upload.py` | Present (not `routes/data_upload.py`) |
| `DetailedSchedulePage.tsx` | Present |
| `ExecutiveHome.tsx` / `PlannerHome.tsx` | Present under `hubs/workspace/components/` (not `features/home/`) |
| `FeasibilityDrawer.tsx` | Present under `components/planning/` |
| `demoRole.ts` | Present |

**Gaps vs Prompt 0 path list:** naming/location differs; FR coverage intact. No missing FR implementations.

## 5. Test results

| Suite | Result |
|-------|--------|
| Vitest | **151 passed / 9 failed / 30 files** (5 files failed) — pre-existing ResolutionCenter / planningLabels util color + others |
| `test_startrans_workbook.py` | **2 passed** |
| `verify-startrans-template.ps1` | **PASS** — 24 sheets, insert 69, fail 0, priority OK |

## 6. Docker Compose validation

| Check | Result |
|-------|--------|
| `docker-compose.release2.yml config` | exit 0 |
| `deploy/star-trans` compose config | exit 0 |
| Kong `/api/v1/upload` + `/api/v1/data` | Present in `infrastructure/docker/kong.release2.yml` |

## 7. Migration head

| Check | Result |
|-------|--------|
| Files `080`/`081`/`082` | Present under `migrations/versions/` |
| Expected head | **082** `cdm_platform_advanced` |

## 8. VERDICT

**YELLOW** — proceed to T090 with caveats:

1. Working tree dirty (pre-existing); do not mass-commit unrelated files.
2. Vitest 9 failures remain (non-blocking for demo path if e2e+k6 green later).
3. Prompt-0 path aliases differ from repo layout (documented above).

## 9. Recommended actions

1. Proceed T090–T094 on warm R2.
2. After stack up: fix remaining vitest failures that block CI if required.
3. Run full e2e + k6 as follow-on finalize (user request).

**Fixed during baseline (required for GREEN build):** EmptyState compat props, DetailedSchedule imports, StarTrans upload `api` import, vendored frappe-gantt CSS.
