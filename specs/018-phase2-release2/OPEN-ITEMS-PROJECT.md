# IPE Open Items — Whole Project + Phase 2 R2

**Workspace**: `E:\AISOP\ipe`  
**Generated**: 2026-07-10 (live-verified: `gh`, `git`, `docker`, `kubectl`, specs)  
**Purpose**: Durable inventory of everything still not closed, with needed action per point.

---

## Section A — Whole project (all phases / specs)

### A1. Specs & program tracks

| Item | Status | Needed action |
|------|--------|---------------|
| Spec 000–003 (foundation / readiness / stabilization) | Historical / largely closed | Keep as archive; do not reopen unless regression |
| Spec 004 `ai-first-v6` / REL-STACK→REL-DEMO→`v6.0.0` | Superseded by later tags (`v9.x`) | Confirm `READINESS.md` / AGENTS.md pointers; no new REL-* work unless program reopens v6 gate |
| Spec 005 `ipe-program-status` | Rollup pointer | Refresh status from this doc after R2 finalize |
| Spec 006–012 (hubs, v8, Keycloak, StarTrans, R1 MENA) | Delivered / absorbed into R1–R2 | Track only residual defects via GitHub |
| Spec 013 Release 1 Odoo MENA | Engineering largely done; commercial UAT open | Executive: Phase 1 SOW + Odoo staging (PH1-01/02) |
| Spec 014 Release 2 growth | Overlaps 018; tag `v9.1.0-r2` **already exists** locally from earlier R1+R2 cut | Do **not** retag blindly; document delta vs current 018 finalize; push tag only if remote missing **and** gates allow |
| Spec 015 Enterprise production readiness | Partial; issues #15–#24 open | Triage EP3 tasks; close or re-scope stale T09x/T15x |
| Spec 016 Sprint 7 ecosystem cohesion | Emitters / migration 038 claimed done | Close related GH issues after push; verify Gate 11 waiver docs |
| Spec 017 First release plan | Wave 1 eng ✅; C-08–C-16 + PH1-* still open | See A2; push commits; commercial PH1; stock.quant / mat-svc compose |
| Spec 018 Phase 2 Release 2 | Engineering ~90%; gates in progress this session | See **Section B** |

### A2. Spec 017 converge carry-over (still open)

| Item | Status | Needed action |
|------|--------|---------------|
| C-08 Push 6 commits to origin | OPEN (branch ahead 6) | `git push origin master` (owner: Dev lead) |
| C-09 Restabilize kind cluster | DONE (8/8 Running) | None — evidence `docs/qa/kind-restabilize-2026-07-10.txt` |
| C-11 Regenerate UAT docx | OPEN | Regenerate from corrected UAT source (P2) |
| C-12 OQ-9 stakeholder names | OPEN (#28) | Fill Section 6 sign-off names in waiver doc |
| C-13 T731 activity API integration tests | OPEN | Add integration tests against live stack |
| C-14 T732 mat-svc in release1/R2 compose | OPEN | Add `mat-svc` service to `docker-compose.release2.yml` (URL already referenced) |
| C-15 FR-R1-05 `stock.quant` | OPEN | Implement Odoo stock.quant sync path (no mock) or ARB CUT in Spec 017 |
| C-16 FR-R1-16 OTD baseline API | ENG DONE | Close after push; verify `/api/v1/analytics/otd-baseline` via Kong |
| PH1-01 Phase 1 SOW / commercial | OPEN | Executive / commercial owner |
| PH1-02 Odoo staging environment | OPEN | Ops: provision staging Odoo; wire connector |
| PH1-03 stock.quant (if distinct from C-15) | OPEN | Same as C-15 |
| PH1-05 Arabic native QA | OPEN | Native reviewer sign-off (`docs/qa/arabic-qa-r2.md`) |
| Phase 1 UAT | BLOCKED commercial | After PH1-01/02 |

### A3. GitHub issues (live `gh issue list --state open`)

| Item | Status vs engineering | Needed action |
|------|----------------------|---------------|
| #15–#24 Enterprise Phase 3 tasks | Stale / unclear delivery | Triage: close if shipped in EP3, else implement or defer with comment |
| #25 T172 Tenant self-service provision API | Partial (ops health exists; full provision API unclear) | Implement real provision API **or** CUT/defer with ARB note; comment on issue |
| #26 T173 Terraform ipe-saas module | OPEN | Implement skeleton **or** defer to EP4 with comment |
| #27 Gate 11 OR-Tools 10–11 | ENG: WON'T FIX infra | **Close** after push with infra waiver comment |
| #28 OQ-9 stakeholder decision | Template done; names open | Comment; leave open until names signed **or** close if waiver accepted |
| #29 P0-07 T730 migration 038 | Applied (compose at 042) | **Close** after push |
| #30 W1-02 Copilot R1 smoke | 12/12 evidence | **Close** after push |
| #31–#36 W1-03–W1-08 Odoo v2 + OTD | Eng delivered in tree | **Close** after push if E2E verified; else leave #32/#34 if staging Odoo required |
| #37 W2-01 Tenant provision API | Ops dashboard health ≠ full provision | Implement real provision **or** defer with comment (do not fake close) |
| #38 W2-02 Quotas and metering | `tenant-quotas.json` mounted; metering incomplete | Implement metering E2E **or** defer with comment |
| #39 W2-03 Scenario CRUD/compare API | Delivered (`scenario-svc`) | **Close** after smoke green + push |
| #40 W2-04 Scenario promotion UI | **NOT FOUND** in code (no promote) | Implement promote API+UI **or** explicit CUT in GATES/spec |
| #41 W2-05 Demand sensing SES | Delivered | **Close** after smoke green + push |
| #42 W2-06 Predictive delay XGBoost+SHAP | Not verified as E2E | Implement for real **or** defer/CUT with comment |
| #43–#44 W3 NL schedule change | Wave 3 — not R2 gate | Leave open; schedule Wave 3 or CUT |
| #45–#46 W3 Supplier comms | Wave 3 — not R2 gate | Leave open; schedule Wave 3 or CUT |

### A4. Requirements / FR / gates (cross-program)

| Item | Status | Needed action |
|------|--------|---------------|
| G-R2-01 release2-smoke | **PASS 15/15** (this session) | Keep evidence `docs/qa/release2-smoke-2026-07-10.txt` |
| G-R2-02 Copilot live tools | PASS | None |
| G-R2-03 Wave 1 W1-03–08 | PASS eng; live Odoo staging open | PH1-02 for full integration proof |
| G-R2-04 Arabic native QA | Eng ✅; human sign-off ⬜ | Native reviewer; cannot fake |
| G-R2-05 run-release2-demo | Kind PASS; compose APIs failing (auth) | Fix dpe AUTH_MODE + re-run demo (Section B) |
| G-R2-TAG `v9.1.0-r2` | Tag **exists locally** from prior cut; remote TBD | Do not retag until G-R2-05 green + policy on G-R2-04; push existing tag only if intentional |
| FR-R1-05 stock.quant | OPEN | See C-15 |
| Keycloak SSO (Spec 011) | Container **unhealthy** | Fix Keycloak health; keep local RS256 login as R2 path |
| RLS on migrations 039–043 | Chain applied to **042** | Verify 043 applied or document head=042 |

### A5. Scripts

| Item | Status | Needed action |
|------|--------|---------------|
| `scripts/release2-smoke.ps1` | **PASS 15/15** | Re-run after any Kong/auth change |
| `scripts/deploy-release2.ps1` | Stack up | Use for cold start |
| `scripts/run-release2-demo.ps1` | FAIL 2/7 (JWT/auth) | Force `-AuthMode local`; recreate dpe with AUTH_MODE=local; re-run |
| `scripts/demo-http.ps1` | Patched: Keycloak→local fallback | Commit |
| `scripts/seed-data.ps1` | Available | Seed if demo APIs return empty business data |
| Alembic upgrade | Compose DB at **042** | `alembic upgrade head` if 043 required |
| Playwright `arabic-r2` / `release2-nav` | Port 8082 listening (web-ui) | `cd apps/web; npx playwright test e2e/arabic-r2.spec.ts --project=desktop` |
| `git push origin master` | Ahead **6** + large dirty tree | Commit R2 deliverables then push |

### A6. Integrations / infra

| Item | Status | Needed action |
|------|--------|---------------|
| Kong R2 (`kong.release2.yml`) | Routes OK; demand/scenario fixed via AUTH_MODE | Keep AUTH_MODE=local for R2 services using local login |
| Compose R2 stack | Up (dpe, fea, res, cap, connector, nlp, demand, scenario, kong, web-ui, keycloak, db, redis) | Recreate **dpe-svc** with AUTH_MODE=local |
| mat-svc in R2 compose | **Missing** (URL env only) | Add service definition (C-14 / OQ-8) |
| Kind `ipe` namespace | **8/8 Running** | None immediate |
| Keycloak | **unhealthy** | Repair container; until then use local auth |
| Odoo staging | Not available | PH1-02 |
| LLM keys (Anthropic/OpenRouter/Ollama) | Copilot may degrade | Set keys in `.env` for live LLM; tools still callable |
| Kafka in R2 compose | Disabled (`IPE_KAFKA_ENABLED=false`) | Accept for R2 smoke **or** enable if event E2E required |
| Dual-mode JWT (`dependencies.py`) | Code fixed on host; images may be stale | Rebuild services **or** rely on AUTH_MODE=local env |

### A7. Migrations / git / tags

| Item | Status | Needed action |
|------|--------|---------------|
| Alembic head on compose DB | **042** | Confirm whether 043 must apply; upgrade if yes |
| Unpushed commits | **6** ahead of origin/master | `git push origin master` |
| Uncommitted R2 tree | Large modified + untracked (018, compose, services, web, docs) | Stage safe paths; commit; exclude `.env`, `.venv`, secrets, kms test keys |
| Tag `v9.1.0-r2` | Exists locally (prior annotated tag) | Verify `git ls-remote --tags origin v9.1.0-r2`; do not move tag; new finalize may need `v9.1.1-r2` if content diverged |
| Tag `v9.4.0-p3` | Interim platform tag | Keep; not a substitute for R2 gate close |

### A8. Frontend / backend TODOs mapped to deliverables

| Item | Status | Needed action |
|------|--------|---------------|
| Scenario promotion UI (#40) | Missing | Implement or CUT |
| Tenant provision API (#37/#25) | Incomplete vs issue title | Implement or defer |
| Quotas metering (#38) | Config mount only | Implement metering or defer |
| Arabic E2E 8-screen | Eng present; native sign-off open | Run Playwright; human sign-off |
| Predictive delay ML (#42) | Unverified | Prove E2E or CUT |
| Wave 3 NL + supplier (#43–#46) | Out of R2 gate scope | Schedule or CUT |

---

## Section B — Last phase: Spec 018 Phase 2 Release 2

**Refreshed 2026-07-10 after smoke PASS + demo PASS**

### B1. Gate matrix (this session)

| Gate | Status | Evidence / needed action |
|------|--------|--------------------------|
| G-R2-01 | **PASS** (15/15) | `docs/qa/release2-smoke-2026-07-10.txt` |
| G-R2-02 | **PASS** | Copilot tools |
| G-R2-03 | **PASS (eng)** | Live Odoo = PH1-02; local mock-odoo XML-RPC E2E for sync |
| G-R2-04 | **PARTIAL** | Eng ✅; **native Arabic sign-off OPEN** |
| G-R2-05 | **PASS** (7/7, 0 SKIP) | `docs/demo-data/release2-demo-g-r2-05.txt` |
| G-R2-TAG | **HOLD** | Eng gates green except human G-R2-04; do not move existing `v9.1.0-r2`; prefer `v9.1.1-r2` after Arabic sign-off |

### B2. What was fixed this session

| Item | Status | Needed action |
|------|--------|---------------|
| Kong demand/scenario 401 | **FIXED** | AUTH_MODE=local on demand/scenario/dpe |
| Dual-mode JWT resolve | **CODE FIXED** | `ipe_shared.auth.dependencies` |
| Demo Keycloak timeout | **FIXED** | `demo-http.ps1` + `-AuthMode local` |
| dpe analytics 401 | **FIXED** | dpe AUTH_MODE=local recreate |
| mock-odoo XML-RPC + BOM/MO sync | **FIXED** | R2 compose service; sync returns `rescored` |
| Resolution demo mo_id | **FIXED** | Propose from queue `mo_id` |

### B3. Sprint / converge (018)

| Item | Status | Needed action |
|------|--------|---------------|
| S1–S4, S6–S11 | ✅ eng | Close matching GH issues after push |
| S5 Arabic | Eng ✅; QA sign-off ⬜ | Native reviewer |
| S12 SAP B1 | **CUT** | No action unless ARB revives |
| C-019 Arabic sign-off | OPEN | Human |
| C-020 Playwright arabic-r2 | Pending run | `npx playwright test e2e/arabic-r2.spec.ts --project=desktop` |
| C-021 smoke | **DONE PASS** | — |
| C-022 demo | **DONE PASS** | — |
| C-023 / C-024 | P2 open | Optional or CUT |
| C-026 push | OPEN | `git push origin master` |
| C-027 tag | HOLD | After G-R2-04 policy |

### B4. Honest E2E vs CUT

| Topic | Verdict |
|-------|---------|
| Demand accuracy via Kong | **E2E complete** |
| Scenario list via Kong | **E2E complete** |
| Demo Outcomes/sync/Copilot/Kind | **E2E complete** (mock-odoo = local ERP double; staging Odoo = PH1-02) |
| Scenario promotion (#40) | **Not delivered** — implement or CUT |
| Tenant provision/quotas (#37/#38) | **Partial** — defer or implement |
| stock.quant | **Not delivered** |
| mat-svc in R2 compose | **Missing** (URL only) |
| Arabic native sign-off | **Human open** |
| S12 SAP B1 | **CUT** |

---

*End of inventory.*
