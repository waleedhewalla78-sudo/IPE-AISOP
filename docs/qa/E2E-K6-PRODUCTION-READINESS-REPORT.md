# E2E + k6 Production Readiness Report

**Workspace**: `E:\AISOP\ipe`  
**Date**: 2026-07-10  
**Scope**: Whole-project QA for R2 compose stack (Kong `:8000`, web `:8082`, Kind `ipe`)  
**Author**: QA automation session  

---

## 1. Environment & data

| Item | Value |
|------|--------|
| Compose | `infrastructure/docker/docker-compose.release2.yml` |
| Kong | `http://localhost:8000` (healthy) |
| Web UI | Docker `web-ui` `:8082` (stale **full** profile image) + Vite `VITE_RELEASE_PROFILE=release2` for R2 nav gate |
| DB | Postgres `ipe_test` via `63c7c80cc535_docker-db-1`; Alembic **042** |
| Redis | `:6380` healthy |
| Kafka | Disabled in R2 (`IPE_KAFKA_ENABLED=false`) |
| Kind | Namespace `ipe` — app pods + postgres/redis Ready (demo G-R2-05.6/7) |
| Seed | `scripts/seed-data.ps1` — representative demo data present (idempotent re-seed hit duplicate `cdm_operator` key; data already loaded) |
| Auth used for gates | **Local** `POST /api/v1/auth/login` (`Ahmed@nour` / `admin`) with `AUTH_MODE=local` on demand/scenario/dpe |
| Keycloak | Realm discovery + password grant **work** (`:8180`); container may show Docker **unhealthy** (healthcheck flake). SSO JWT **not** accepted by demand/dpe while `AUTH_MODE=local` until dual-mode image rebuild |

Evidence dirs: `docs/qa/*-2026-07-10.txt`, `docs/qa/k6-*`, `docs/demo-data/release2-demo-g-r2-05.txt`

---

## 2. Workflows tested

| Workflow | Result | Notes |
|----------|--------|-------|
| Auth / local login (API + UI) | **PASS** | Kong login + Playwright login |
| Control tower / planning hubs | **PASS** | Desktop + release2 nav |
| Demand forecast / accuracy | **PASS** | Smoke Kong demand + UI demand tab |
| Scenarios list | **PASS** | `/api/v1/scenario` (not `/scenarios`) |
| OTD baseline / ROI | **PASS** | Demo G-R2-05.1/2 |
| Odoo config/sync | **BLOCKED (CUT residual)** | Sync E2E via **mock-odoo** XML-RPC only; live staging = **PH1-02** |
| Ops / resolution | **PASS** | Demo + Playwright resolution chrome (empty MO queue tolerated) |
| SOP / Copilot / planner-assist | **PASS** | Demo + Copilot Playwright (real login) |
| Arabic RTL UI (8 screens) | **PASS (UI only)** | Playwright green; **API responses mocked** in `arabic-r2.spec.ts` — not a live-data E2E |
| Arabic native human sign-off | **BLOCKED** | Human only — do not fake |
| Release1 profile Copilot | **PASS** | With real login + serial workers |
| Release2 profile nav | **PASS** | Against Vite `release2`; **FAIL** against stale docker web-ui `full` image (Supply Chain visible) |
| Kind path | **PASS** | Demo checkpoints 6–7 |

---

## 3. Playwright matrix

Command (stable):  
`cd apps/web; npx playwright test --project=desktop --project=release2 --workers=1`

| Spec / project | Result | Evidence |
|----------------|--------|----------|
| `e2e/arabic-r2.spec.ts` ×4 (desktop) | **PASS** | `docs/qa/playwright-serial-2026-07-10.txt` — **API mocked** |
| `e2e/copilot.spec.ts` ×4 | **PASS** | Real login (fixed fake-JWT flakiness) |
| `e2e/critical-path.spec.ts` ×7 | **PASS** | Locale + empty-queue hardened |
| `e2e/demand-tab.spec.ts` | **PASS** | |
| `e2e/login.spec.ts` | **PASS** | Dropped `networkidle` wait |
| `e2e/supply-tab.spec.ts` | **PASS** | |
| `e2e/release2-nav.spec.ts` ×4 (`--project=release2`) | **PASS** | `docs/qa/playwright-release2-vite-2026-07-10.txt` (Vite release2) |
| `tests/**/*.perf.test.ts` (CPM mock) | **EXCLUDED** | Mock cascade only — not a production gate; removed from default `testMatch` |

**Scores**

- Desktop serial (API-backed + Arabic UI): **18/18 PASS**
- Release2 Vite: **4/4 PASS**
- Combined gate when web profile is release2: **22/22 PASS**
- Against stale docker web-ui `full`: release2 hub-hide **FAIL** (Supply Chain visible) — treat as **infra defect**, not product nav bug

**Flakiness note**: Parallel workers (`--workers=4`) + service restarts caused login timeouts / 502s. Prefer `--workers=1` for R2 compose on this host.

---

## 4. k6 results

| Suite | Script | Thresholds | Result | Evidence |
|-------|--------|------------|--------|----------|
| R2 critical APIs | `scripts/perf/k6-r2-critical.js` | errors &lt;10%, checks &gt;85%, p95 &lt;2s | **PASS** (517 req, p95 ~73ms, errors 0%) after pacing | `docs/qa/k6-r2-critical-rerun-2026-07-10.txt` |
| R2 critical (first run) | same | — | **FAIL** 22% errors | Kong **rate limit (~500 req/min)** under 3 VU × 6 GETs/iter; not app 5xx |
| SLO baseline | `scripts/perf/k6-slo.js` via `run-k6-slo.ps1 -AuthMode local` | p95 &lt;500ms, errors &lt;5% | **PASS** (624 req, p95 ~145ms, errors 0%) | `docs/qa/k6-slo-final-2026-07-10.txt`, `docs/qa/k6-slo-baseline.json` |
| Stress / 200 VU | existing scripts | — | **Not re-run this session** | Prior baselines under `docs/qa/`; optional for staging |

Critical endpoints covered: health, feasibility queue/KPIs, OTD baseline, demand accuracy, scenario list — all via Kong with local JWT.

---

## 5. Errors found → root cause → fix → re-verify

| Error | Root cause | Fix | Re-verify |
|-------|------------|-----|-----------|
| Playwright port 8082 conflict | `reuseExistingServer: false` | Set `reuseExistingServer: true`; API base → Kong `:8000` | Desktop suite runs |
| Login / Copilot redirect to `/login` with fake JWT | Fake HS256 token + Keycloak/auth race | Real Kong login in copilot/release2/critical-path | Copilot 4/4, release2 4/4 |
| English assertions vs Arabic UI | Browser/default locale Arabic | `forceEnglishLocale` / bilingual matchers | critical-path green |
| Resolution heading / empty MO | Strict heading + required rows | Heading i18n + empty-queue branch | PASS |
| release2 “hide Supply Chain” FAIL on docker UI | web-ui image built as **full**, not release2 | Run Vite `VITE_RELEASE_PROFILE=release2`; **rebuild web-ui** still required | Vite 4/4 PASS |
| Smoke 502 on demand/scenario | Containers restarting / not ready | Wait for healthy; re-smoke | **15/15 PASS** |
| k6 critical 22% errors | Exceeded Kong 500 req/min → 429 counted as errors | Increase sleep pacing in `k6-r2-critical.js` | **PASS** 0% errors |
| Keycloak JWT → demand/dpe 401 | `AUTH_MODE=local` path always `decode_token` | Code fix in `ipe_shared.auth.dependencies` (dual-mode); **images not rebuilt this session** | Local JWT PASS; KC SSO still **BLOCKED** until rebuild |
| Seed duplicate key | Idempotent re-seed | Accept; data already present | N/A |

---

## 6. Mocks inventory

| Mock / fallback | Replaced? | Verdict |
|-----------------|-----------|---------|
| `mock-odoo-api` XML-RPC | **No** — no customer Odoo staging | **BLOCKED / CUT residual** — owner: Ops **PH1-02**; do not claim live ERP PASS |
| `AUTH_MODE=local` | Partial — Keycloak realm works; services still local | **RESIDUAL** — rebuild demand/scenario/dpe with dual-mode JWT to accept SSO |
| Arabic E2E `mockProtectedApis` | **No** | **UI-only PASS**; live Arabic data path **BLOCKED** until mocks removed + native sign-off |
| Fake JWT in older specs | **Yes** → real login | Fixed in copilot/release2/critical-path |
| CPM cascade Playwright mock | Excluded from default run | Not a prod gate |
| LLM / Copilot model keys | Untouched | Tools callable; live LLM may degrade without keys — document if demos need Anthropic/OpenRouter |
| Kafka disabled | Accepted for R2 smoke | Event E2E **out of scope** unless enabled |

---

## 7. Data consistency

- Seed + demo sync: resolution scenarios and OTD/ROI APIs return coherent payloads after mock-odoo sync (`rescored`).
- Demand accuracy returns structured SES payload (`forecast_rows`, `tenant_mape_pct`).
- Scenario list empty array is valid for tenant without what-if rows.
- UI actions that depend on live APIs (login, resolution, demand page) persist tokens and call Kong; Arabic suite does **not** prove API persistence.
- After compose recreate, wait for demand/scenario/nlp healthy before asserting consistency (transient 502 observed).

---

## 8. Production-readiness verdict

**Not production-ready for customer staging/prod cutover.**  

**Ready for**: continued R2 engineering gates, local/demo sign-off of compose+Kind paths, k6 SLO baseline under local auth.

**Honest blockers before staging/prod**

1. **PH1-02** live Odoo (retire mock-odoo as “done”)  
2. **G-R2-04** native Arabic human sign-off + remove/replace Arabic API mocks  
3. Rebuild **web-ui** with `VITE_RELEASE_PROFILE=release2` and rebuild services with dual-mode JWT for Keycloak SSO  
4. Open product gaps: scenario promotion (#40), stock.quant (C-15), mat-svc in compose (C-14), tenant provision/quotas (#37/#38)  
5. Tag policy: do not push stale `v9.1.0-r2`; cut new tag only after Arabic policy + intentional gate close  

**Eng gates this session**: smoke **15/15**, demo **7/7**, Playwright **22/22** (correct profile), k6 SLO **PASS**, k6 critical **PASS** (paced).

---

## 9. Remaining actions (owners / commands)

| Priority | Action | Owner | Command / note |
|----------|--------|-------|----------------|
| P0 | Provision Odoo staging; wire connector | Ops / PH1-02 | Replace `ODOO_URL=http://mock-odoo-api:8010` |
| P0 | Native Arabic QA sign-off | Native reviewer | `docs/qa/arabic-qa-r2.md` — human only |
| P0 | Rebuild web-ui release2 image | Dev | `docker compose -f docker-compose.release2.yml build --no-cache web-ui && up -d web-ui` |
| P0 | Rebuild demand/scenario/dpe with dual-mode JWT | Dev | Apply `ipe_shared.auth.dependencies` fix into images; verify KC token → `/api/v1/demand/accuracy` 200 |
| P1 | Remove Arabic Playwright API mocks; hit Kong | QA | Edit `e2e/arabic-r2.spec.ts` |
| P1 | mat-svc in R2 compose | Dev | C-14 |
| P1 | stock.quant or ARB CUT | Dev / ARB | C-15 / FR-R1-05 |
| P1 | Scenario promote API+UI or CUT | Dev | #40 |
| P2 | Fix Keycloak Docker healthcheck | Dev | `start_period` / probe already adjusted in compose |
| P2 | Optional k6 stress / 200 VU on staging | QA | `scripts/run-k6-stress.ps1`, `run-k6-200vu.ps1` |
| P2 | Push / tag only after policy | Dev lead | No force; prefer `v9.1.1-r2` after G-R2-04 |

---

## 10. Gate snapshot (018)

| Gate | Status |
|------|--------|
| G-R2-01 smoke | **PASS** 15/15 |
| G-R2-02 Copilot | **PASS** |
| G-R2-03 Wave1/Odoo eng | **PASS eng**; live Odoo **BLOCKED PH1-02** |
| G-R2-04 Arabic | Eng UI **PASS**; native sign-off **OPEN**; API mock **not live E2E** |
| G-R2-05 demo | **PASS** 7/7 |
| G-R2-TAG | **HOLD** |

---

*End of report.*
