# IPE Platform — Open Topics Register

**Compiled:** 2026-07-17 · **Updated:** 2026-07-18 (Phase 8 Wave 1 / Spec 030)
**Workspace:** `E:\AISOP\ipe` (canonical)
**GitHub repo:** `waleedhewalla78-sudo/IPE-AISOP` (open issues pulled live via `gh issue list --state open`)
**Maintainer split:** Commercial/Human items — Waleed / Star Trans; Engineering items — Engineering Lead

---

## Executive summary

This register consolidates every open issue, risk, action, integration gap, deferral, and commercial blocker across the IPE program, grounded in real repository files and live GitHub issues (no invented items). It captures **41 open topics** across six categories:

| Category | Count | P0 | P1 | P2 |
|----------|------:|---:|---:|---:|
| 1. Commercial / Human blockers | 8 | 4 | 3 | 1 |
| 2. Integrations | 8 | 2 | 4 | 2 |
| 3. Engineering residuals / deferrals | 12 | 1 | 6 | 5 |
| 4. Quality / testing risks | 6 | 1 | 4 | 1 |
| 5. Release / tagging | 2 | 1 | 1 | 0 |
| 6. Ops / support | 5 | 0 | 3 | 2 |
| **Total** | **41** | **9** | **21** | **11** |

**Honesty boundary (critical):** The program's true blockers are **HUMAN / COMMERCIAL**, not engineering. All Wave 1 engineering for Ops Blueprint Phases 3–7 **plus Spec 029 productionization and Spec 030 Phase 8 Wave 1 (8A)** is **ENG COMPLETE** with green unit suites (Phase 8: 31 new PASS; Phase 4–8 dpe bundle 102 PASS). Customer enablement package remains artifact-ready. What remains gating: **OQ-7**, **PH1-02**, **G-R2-04**, **OQ-1**. Phase 8B–8D (live multi-site, full Excel everywhere, partner launch) and validate #70/#72/#110 remain eng residuals. Under-load k6 p95 is the genuine non-COM engineering risk.

Owner legend: **ENG** = Engineering · **COM** = Commercial (Waleed / sales) · **OPS** = Operations/SRE · **CUST** = Customer (Star Trans IT/Ops) · **HUMAN** = named human reviewer/signer (non-engineering).

---

## 1. Commercial / Human blockers

These MUST remain OPEN until the named human closes them. Engineering has zero ability to close and must not fake resolution.

| ID | Topic | Category | Current state | Needed action | Owner | Priority | Reference |
|----|-------|----------|---------------|---------------|-------|----------|-----------|
| C-01 | OQ-7 licence / implementation pricing | Commercial | OPEN — BLOCKING. SOW carries `[AMOUNT — to be confirmed by Waleed]` placeholders. Reference range: licence $18–30K, implementation $12–25K. | Waleed decides exact numbers; remove placeholders from SOW; unblocks SOW send. | COM (Waleed) | P0 | GH#106; `docs/project/OQ-RESOLUTION-STATUS.md`; `PRODUCT-STATUS.md` |
| C-02 | PH1-01 SOW send | Commercial | OPEN — depends on OQ-7. SOW artifact otherwise ready. | Send SOW to Star Trans once C-01 resolved. | COM | P0 | `docs/project/OPEN-ITEMS.md`; `docs/customer/star-trans/SOW-STATUS.md` |
| C-03 | PH1-02 live Odoo staging access | Commercial/Integration | OPEN. No staging URL or test MOs from customer. Blocks all live-integration + live-sync UAT. | Star Trans IT provisions Odoo staging URL + test MOs; Ops coordinates connection. | CUST / OPS | P0 | GH#108; `docs/project/OPEN-ITEMS.md` |
| C-04 | G-R2-04 Arabic native QA sign-off | Commercial/Human | OPEN. Engineering i18n evidence green (Playwright 4/4, 361/361 keys) but NOT human acceptance. Sign-off table unsigned. | Assign native Arabic reviewer; complete terminology + RTL rows; sign off. Gates `v9.1.1-r2`. | HUMAN (native reviewer) | P0 | GH#109; `docs/qa/arabic-qa-r2.md`; `docs/project/OPEN-ITEMS.md` |
| C-05 | OQ-1 Odoo 17 vs 19 confirmation | Commercial | OPEN. Connector supports both via field aliases (`normalize_mo_mapped()`); recommend 19. Zero code change needed either way. | Star Trans IT confirms canonical version during pre-engagement call. | CUST | P1 | GH#107; `docs/project/OQ-RESOLUTION-STATUS.md` |
| C-06 | OQ-9 Gate 11 waiver signatures | Commercial/Human | OPEN. 12/14 checks passed; 2 failures are K8s infra contention, not product defects. Waiver drafted, unsigned. | Collect stakeholder signatures on `docs/demo-data/gate11-oq9-waiver.md` before go-live. | COM (Waleed) | P1 | `docs/project/OPEN-ITEMS.md`; `docs/project/OQ-RESOLUTION-STATUS.md` |
| C-07 | OQ-3 UI route-level RBAC decision | Commercial | OPEN (recommendation: defer to R2). Current JWT role system sufficient for single-tenant R1. Needs formal COM decision (affects support terms). | Waleed makes formal defer/include decision before SOW send. | COM | P1 | `docs/project/OQ-RESOLUTION-STATUS.md`; `docs/customer/star-trans/SOW-STATUS.md` |
| C-08 | OQ-8 Customer 2+ pipeline prospects | Commercial | OPEN. No target companies named. Zero eng impact — same `deploy/star-trans/` package reused. | Waleed names 5 target companies (Egyptian mfg, Odoo 17/19, 50–500 emp). | COM (Waleed) | P2 | `docs/project/OQ-RESOLUTION-STATUS.md` |

---

## 2. Integrations

Most live integrations are gated by PH1-02 (C-03). The Kong `/enterprise/*` route gap is the one purely-engineering-actionable integration item.

| ID | Topic | Category | Current state | Needed action | Owner | Priority | Reference |
|----|-------|----------|---------------|---------------|-------|----------|-----------|
| INT-01 | Kong `/api/v1/enterprise/*` route missing | Integration | **ENG CLOSED (Spec 029)** — route objects `r2-enterprise` / `st-enterprise` shipped. Live smoke still stack-dependent. | Re-run live Kong smoke when R2 healthy. | ENG | P2 | Spec 029; `PRODUCT-STATUS.md` |
| INT-02 | Live Odoo XML-RPC sync (connector) | Integration | Connector BUILT (mock validated locally, Odoo 17+19 aliases). Live sync unverified — mock-odoo only. | On PH1-02: run connector against real Odoo staging; execute live sync UAT. | CUST / ENG | P0 | `PRODUCT-STATUS.md`; GH#108 |
| INT-03 | Odoo Accounting integration | Integration | SCAFFOLD/MOCK (`OdooAccountingConnector`, `is_live=false`). | On PH1-02: wire live accounting; flip `is_live`. Do not fake. | ENG (blocked by CUST) | P1 | `PRODUCT-STATUS.md` (Phase 6 table); `CHANGELOG.md` |
| INT-04 | Market-data / FX feed (A14) | Integration | NOT WIRED. Analytics runs on supplied history only. | On PH1-02 / data-source availability: connect live market-data feed. | ENG (blocked by CUST) | P2 | `PRODUCT-STATUS.md` (Phase 6 table) |
| INT-05 | IoT / machine telemetry (A16 + Digital Gemba §5.2) | Integration | STUB (`iot_live=false`, last-known snapshot). No live MQTT/REST/MES. | On PH1-02: integrate live IoT/MES telemetry into Digital Gemba + Shop Floor Intelligence. | ENG (blocked by CUST) | P1 | `PRODUCT-STATUS.md`; `docs/qa/PHASE7-EXECUTION-AND-TEST-REPORT.md`; `docs/project/OPEN-ITEMS.md` |
| INT-06 | Odoo PO / invoice write-back (A15) | Integration | NOT executed against live Odoo. 3-way match logic + write-back route exist (405 on activate = route present). | On PH1-02: execute PO/RFQ write-back to live Odoo; validate 3-way match end-to-end. | ENG (blocked by CUST) | P1 | `PRODUCT-STATUS.md`; `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md` (#72 write-back route) |
| INT-07 | ERP connections routes / nav (Odoo Config v2) | Integration | Spec 023 residual — CRUD/test/activate/sync + Fernet-encrypted passwords BUILT (ENG). GitHub issues still open (not closed on GH). | ENG verify + close GH issues #74/#75/#76/#78/#82; confirm no password leak in API. | ENG | P2 | GH#74, #75, #76, #78, #82; `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md` |
| INT-08 | Keycloak SSO / enterprise IdP | Integration | Scaffold ready (`ipe_shared/auth/keycloak.py`); R1 uses local JWT. Kafka/Redis/Vault/Langfuse operational in stack. | Activate `AUTH_PROVIDER=keycloak` only if a tenant requires SSO (R2/enterprise); not needed for Star Trans R1. | ENG (on demand) | P2 | `READINESS.md` (C-007); Spec 011 |

---

## 3. Engineering residuals / deferrals

All are Wave 1 deferrals or open GitHub task-issues; none block Wave 1 ENG-COMPLETE status. Items marked "Wave 2" are intentional scope deferrals.

| ID | Topic | Category | Current state | Needed action | Owner | Priority | Reference |
|----|-------|----------|---------------|---------------|-------|----------|-----------|
| ENG-01 | #70 seed/sync demo MOs for validate queue | Issue | OPEN. Feasibility queue has 2 MOs via Kong (some unscorable/DQ). | Seed/sync demo MOs so `star-trans-validate` queue PASS; re-run when R2 stack healthy. | ENG | P1 | GH#70; `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md` |
| ENG-02 | #72 re-run star-trans-validate after seed | Issue | OPEN. Depends on #70. Write-back route reachable (405). | Re-run `scripts/star-trans-validate.ps1` after ENG-01; capture full PASS. | ENG | P1 | GH#72, GH#95 |
| ENG-03 | #110 re-run validate when Docker up (issues 70/72) | Issue | OPEN (Spec 024 tracking issue for the above). | Bring R2 stack up healthy; execute validate; close #70/#72/#110 together. | ENG | P1 | GH#110 |
| ENG-04 | Andon board DB persistence + notifications | Deferral | Spec 029 dual-write **BUILT**; real push notifications still Wave 2. | Wave 2: real notification channel + tablet UI. | ENG | P2 | Spec 029; Phase 8 report |
| ENG-05 | S&OP interactive stage-gate state machine | Deferral | Spec 029 stage-gate scaffold **BUILT** (`/sop/stage-gate*`). Full UI polish Wave 2. | Wave 2 UI polish. | ENG | P2 | Spec 029 |
| ENG-06 | Collaborative multi-user conflict/locking UI | Deferral | DEFERRED beyond Wave 1 (Spec 026 residual). | Wave 2: build collaborative planning conflict resolution + locking UI. | ENG | P1 | `PRODUCT-STATUS.md`; `docs/project/OPEN-ITEMS.md` |
| ENG-07 | MPS/MRP DB persistence migrations | Deferral | Spec 029 migration **069** + save helpers **BUILT**. | Optional richer plan history UI. | ENG | P2 | Spec 029 |
| ENG-12 | Phase 8B–8D (A18 live, Excel everywhere, launch) | Deferral | 8A stubs shipped (Spec 030). | Execute 8B–8D roadmap. | ENG | P1 | `docs/qa/PHASE8-EXECUTION-AND-TEST-REPORT.md` |
| ENG-08 | Monetary net-saving in R2 leveling engine | Deferral | DEFERRED. Leveling returns operational metrics only (peaks_smoothed/residual_spill/feasible). Was P5-LEV-02 SKIP. | Wave 2: add monetary net-saving quantification to leveling. | ENG | P2 | `docs/qa/PHASES3-5-E2E-TEST-REPORT.md` (P5-LEV-02) |
| ENG-09 | Operator tablet UI (Standard Work §5.5) | Deferral | MINIMAL Wave 1 (compute + tracking contract; no live tablet UX). | Wave 2: build operator tablet UI for Standard Work. | ENG | P2 | `docs/qa/PHASE7-EXECUTION-AND-TEST-REPORT.md`; `docs/project/OPEN-ITEMS.md` |
| ENG-10 | Alert inbox SLA UI (Spec 026) | Deferral | PARTIAL (ops live alerts only). | Wave 2: complete alert inbox SLA UI. | ENG | P2 | `docs/project/OPEN-ITEMS.md` |
| ENG-11 | Deeper OR-Tools multi-resource/campaign scheduling | Deferral | Wave 1 uses exact≤8 / greedy heuristics. | Wave 2: deeper OR-Tools integration for multi-resource + campaign scheduling. | ENG | P2 | `docs/qa/PHASE7-EXECUTION-AND-TEST-REPORT.md` |
| ENG-12 | Future waves W2/W3 backlog (multi-tenant ops, predictive ML, NL schedule, supplier comms) | Deferral | OPEN GitHub issues, not scheduled: tenant provision/quotas, XGBoost+SHAP predictive delay, NL schedule change, supplier comms rule engine/email. | Roadmap decision + scheduling into a future wave; not R1/Star Trans blockers. | ENG / COM | P2 | GH#37, #38, #42, #43, #44, #45, #46; enterprise-phase GH#15–#26 |

---

## 4. Quality / testing risks

| ID | Topic | Category | Current state | Needed action | Owner | Priority | Reference |
|----|-------|----------|---------------|---------------|-------|----------|-----------|
| QA-01 | k6 p95 SLO under concurrent load | Risk | Baseline p95 GREEN (293ms < 300ms target) but under contention/campaign load p95 FAILs (~6258ms vs 500ms; R2 critical ~60s). Functional checks 100%, errors 0%. | ENG profile + tune (connection pooling, solver timeouts, caching, horizontal scale) and re-run k6 under load before high-concurrency go-live. **Genuine eng risk, not commercially blocked.** | ENG | P1 | `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md`; `PRODUCT-STATUS.md` (baseline); `docs/qa/E2E-K6-PRODUCTION-READINESS-REPORT.md` |
| QA-02 | Playwright flakes (Arabic tablet, mobile a11y) | Risk | Full suite 56 pass / 2 fail: tablet Arabic labels timeout; mobile login `h1` a11y flake (desktop/tablet OK). Login 3/3 green. | ENG stabilize flaky specs (timeout/a11y selectors); add dedicated Phase 3+ page e2e. | ENG | P2 | `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md`; `PRODUCT-STATUS.md` (Playwright row) |
| QA-03 | UAT cases requiring live stack (15 SKIP / 1 BLOCKED) | Risk | Phases 3-5 E2E: 86 PASS / 0 FAIL / 15 SKIP / 1 BLOCKED. Skips need live Odoo (P4-PRO-03), time-travel (P3-PRS), browser/WebSocket (P5-CMD), or unbuilt gate (E2E-SOP-03). | On PH1-02 + live sessions: execute the SKIP/BLOCKED cases; do not fake. | ENG (blocked by CUST) | P1 | `docs/qa/PHASES3-5-E2E-TEST-REPORT.md` |
| QA-04 | RLS coverage gap (10 tables off) | Risk | RLS audit: 85 tables `rowsecurity=true`; ~10 CDM tables still off (TC-RLS-03 PARTIAL). | ENG audit remaining tables; add RLS policies where tenant-scoped (verify sub-tables scoped via parent JOIN). | ENG | P1 | `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md` (rls-tables.txt) |
| QA-05 | Copilot live chat (UAT-10) reliability | Risk | Unit tools 22/22 green; live chat UAT-10 previously timed out / 500 (timeout fix landed in Spec 021). Live LLM optional for R1. | ENG re-verify live Copilot path against configured LLM; keep unit coverage as gate. | ENG | P2 | `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md`; `PRODUCT-STATUS.md` (Planning UAT) |
| QA-06 | Live Kong smoke of Phase 6 `/enterprise/*` | Risk | NOT confirmed via Kong (404 route gap; handlers green direct + ASGI 6/6). Phase 7 `/planning-command/*` Kong smoke 13/13 confirmed. | Depends on INT-01: add Kong route then run live `/enterprise/*` smoke. | ENG | P0 | `PRODUCT-STATUS.md`; `docs/qa/PHASE7-EXECUTION-AND-TEST-REPORT.md` |

---

## 5. Release / tagging

| ID | Topic | Category | Current state | Needed action | Owner | Priority | Reference |
|----|-------|----------|---------------|---------------|-------|----------|-----------|
| REL-01 | `v9.1.1-r2` tag on HOLD | Release | HOLD until G-R2-04 Arabic native QA sign-off (C-04). Not applied. | After C-04 human sign-off, cut `v9.1.1-r2`. ENG cannot self-authorize. | ENG (gated by HUMAN) | P0 | `PRODUCT-STATUS.md`; `docs/project/OPEN-ITEMS.md`; `AGENTS.md` |
| REL-02 | `v9.1.0-r2` stale-tag policy | Release | LOCAL ONLY / STALE — superseded by `v9.1.1-r2`. | NEVER push stale `v9.1.0-r2`. Enforce as standing policy. | ENG | P1 | `PRODUCT-STATUS.md`; `docs/project/OPEN-ITEMS.md`; `AGENTS.md` |

---

## 6. Ops / support

| ID | Topic | Category | Current state | Needed action | Owner | Priority | Reference |
|----|-------|----------|---------------|---------------|-------|----------|-----------|
| OPS-01 | WhatsApp / Comms Hub | Deferral | DEFERRED (Spec 026 residual). Not built. | Wave 2: build WhatsApp / Comms Hub support channel. | ENG | P1 | `PRODUCT-STATUS.md`; `docs/project/OPEN-ITEMS.md` |
| OPS-02 | Customer VM + champion provisioning | Action | Pending. 8GB VM (Ubuntu 22.04 / Win Server) + planner champion not yet provisioned. | Star Trans IT provisions VM; Ops schedules Week 2 training champion. | CUST / OPS | P1 | `docs/customer/star-trans/SOW-STATUS.md` |
| OPS-03 | Live-stack validation re-run (R2 remap) | Action | R2 smoke prior 15/15; needs re-verify when stack healthy (Phase 3 services added). | Run `scripts/star-trans-validate.ps1 -DpePort 8020 -ConnectorPort 8016` on healthy R2 stack. | OPS / ENG | P1 | `PRODUCT-STATUS.md`; `AGENTS.md` |
| OPS-04 | Monitoring / observability activation | Action | Prometheus + Grafana + OTel + Jaeger + Langfuse scaffolded; `/metrics` on 14/16 services. Dashboards present (k6 perf). | Confirm dashboards/alerts wired in customer deploy; validate `/metrics` scrape post-deploy. | OPS | P2 | `PRODUCT-STATUS.md`; AGENTS.md progress log (P0 observability) |
| OPS-05 | Backup / restore + DR runbook validation | Action | Support guide + runbooks ready; TC-RES-01 DB restart NOT run (destructive), no live backup drill. | OPS execute backup/restore drill against deploy package before go-live sign-off. | OPS | P2 | `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md` (TC-RES-01 not run); `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` |

---

## Top 10 priorities / recommended next actions

Ordered by program impact. Items 1–4 are **HUMAN/COMMERCIAL** (engineering cannot close); items 5–10 are **ENGINEERING/OPS-actionable now**.

1. **[COM] Decide OQ-7 pricing and remove SOW placeholders** — single biggest unblock; gates SOW send and the whole customer track. (C-01, GH#106)
2. **[CUST/OPS] Provision live Odoo staging (PH1-02)** — unblocks live sync, Accounting, market-data, IoT, PO write-back, and 15 SKIPped UAT cases in one move. (C-03, GH#108, INT-02/03/04/05/06, QA-03)
3. **[HUMAN] Assign native Arabic reviewer and complete G-R2-04 sign-off** — only gate on the `v9.1.1-r2` tag. (C-04, GH#109, REL-01)
4. **[CUST] Confirm Odoo 17 vs 19 (OQ-1)** — quick call; zero code change but needed for staging clarity. (C-05, GH#107)
5. **[ENG] Add Kong `/api/v1/enterprise/*` route object** — closes the only pure-engineering integration gap and enables live Phase 6 gateway smoke. (INT-01, QA-06)
6. **[ENG] Investigate and tune k6 p95 under concurrent load** — the one genuine, non-blocked engineering quality risk before high-concurrency go-live. (QA-01)
7. **[ENG/OPS] Bring R2 stack healthy, seed demo MOs, re-run star-trans-validate** — closes GitHub #70/#72/#110 together. (ENG-01/02/03, OPS-03)
8. **[ENG] Close RLS coverage gap on remaining ~10 tables** — security hardening before customer data lands. (QA-04)
9. **[ENG] Stabilize Playwright flakes + add Phase 3+ page e2e** — restore full-suite green signal. (QA-02)
10. **[OPS] Run backup/restore + DR drill and confirm monitoring/alerts in customer deploy** — go-live operational readiness. (OPS-05, OPS-04)

---

*Grounding: every row cites a real repository file or live GitHub issue number. Commercial/Human items (Section 1, Top-10 #1–4) are explicitly NOT engineering-closable and are never marked resolved by engineering. Live Odoo sync and Arabic native sign-off are never faked. Sources: `docs/project/OPEN-ITEMS.md`, `docs/project/OQ-RESOLUTION-STATUS.md`, `PRODUCT-STATUS.md`, `READINESS.md`, `CHANGELOG.md`, `docs/customer/star-trans/SOW-STATUS.md`, `docs/qa/PHASE{3,4,5,6,7}-EXECUTION-AND-TEST-REPORT.md`, `docs/qa/PHASES3-5-E2E-TEST-REPORT.md`, `docs/qa/FULL-TEST-CAMPAIGN-REPORT.md`, `docs/qa/arabic-qa-r2.md`, and `gh issue list --state open` (repo `waleedhewalla78-sudo/IPE-AISOP`).*
