# IPE Platform — Open Topics Register

**Compiled:** 2026-07-17 · **Updated:** 2026-08-15 (Star Trans Batch0 ENG closed; T097 hard-stop locked; Vitest residuals closed; **COM still OPEN** — see `docs/qa/COM-BLOCKERS-REMAIN-OPEN-2026-08-15.md`)
**Workspace:** `E:\AISOP\ipe` (canonical)
**Authoritative full status (DETAILED closure playbooks):** `docs/project/FULL-PROJECT-STATUS-AND-ROADMAP-2026-07-31.md`  
→ Use that file for step-by-step closure of every OPEN ID (C-*, INT-*, QA-*, 9A-OPS-*, REL-*, OPS-*). This register stays the short index.
**Authoritative finalize (baseline):** `docs/project/FINAL-PROGRAM-STATUS.md`
**GitHub repo:** `waleedhewalla78-sudo/IPE-AISOP`
**Maintainer split:** Commercial/Human — Waleed / Star Trans; Engineering — Engineering Lead

---

## Executive summary

Wave 1 engineering for Specs **022–032** and Phase **9A–9F** (Spec **033** / **033a–033f**) is **ENG COMPLETE** at **scaffold** depth (unit tests green; soft `live:false` badges; lab alembic **082**; 9B–9F soft DB persist; Kong/EventBus/RLS residuals closed 2026-08-01). R1/R2 verdict remains: **ENG READY / COM CONDITIONAL**. Production ML/SAP/OCR and COM gates are **not** claimed closed.

| Category | Remaining OPEN | Notes |
|----------|---------------:|-------|
| 1. Commercial / Human | **8** | Never fake |
| 2. Integrations (live) | **5** | INT-9A eng CLOSED (#154); PH1-02 live Odoo still OPEN |
| 3. Engineering / stack / QA | **~2** | Playwright flakes; Copilot live; deferred ML/SAP |
| 4. Ops / support | **3** | VM, monitoring, DR (validate DONE 2026-07-25) |
| 5. Release / tagging | **2** | HOLD + stale-tag policy |
| **Actionable total** | **≈20** | Go-live still COM-blocked |
| Deferred deeper | 9B–9F production depth · 8B–8D · Wave 2 UX | Scaffold ≠ production ML/SAP |

**Closed eng (do not re-open):** INT-01 Kong `/api/v1/enterprise` (+ `/phase8`); Specs 022–030 W1; Spec 029 Andon/RLS/MPS; Spec 030 8A; **9A-OPS-1→082**; **T160 9B–9F persist**; **QA-06 Kong smoke 2026-08-01**; **QA-04 RLS lab 082**; **9A-OPS-2/3**; **T165 wave i18n keys**.

Owner legend: **ENG** · **COM** · **OPS** · **CUST** · **HUMAN**.

---

## 1. Commercial / Human blockers (OPEN)

| ID | Topic | Needed action | Owner | Priority | Ref |
|----|-------|---------------|-------|----------|-----|
| C-01 | OQ-7 pricing | Set licence + impl prices; remove SOW placeholders | COM (Waleed) | P0 | GH#106 |
| C-02 | PH1-01 SOW send | Send SOW after C-01 | COM | P0 | OPEN-ITEMS |
| C-03 | PH1-02 live Odoo staging | Provision URL + test MOs | CUST / OPS | P0 | GH#108 |
| C-04 | G-R2-04 Arabic native QA | Sign off terminology + RTL | HUMAN | P0 | GH#109 |
| C-05 | OQ-1 Odoo 17 vs 19 | Confirm canonical version | CUST | P1 | GH#107 |
| C-06 | OQ-9 Gate 11 waiver | Collect signatures | COM | P1 | OQ-RESOLUTION |
| C-07 | OQ-3 UI RBAC decision | Formal defer/include | COM | P1 | OQ-RESOLUTION |
| C-08 | OQ-8 Customer 2+ pipeline | Name 5 prospects | COM | P2 | OQ-RESOLUTION |

---

## 2. Integrations

| ID | Topic | Current state | Needed action | Owner | Priority |
|----|-------|---------------|---------------|-------|----------|
| ~~INT-01~~ | ~~Kong `/api/v1/enterprise/*` missing~~ | **CLOSED** — `r2-enterprise` / `st-enterprise` (+ phase8) shipped Spec 029/030 | Live smoke only when stack healthy (→ QA-06) | — | — |
| INT-02 | Live Odoo XML-RPC sync | Connector BUILT; live unverified | On PH1-02: live sync UAT | CUST / ENG | P0 |
| INT-03 | Odoo Accounting | SCAFFOLD/MOCK `is_live=false` | Wire live on PH1-02 | ENG (blocked) | P1 |
| INT-04 | Market-data / FX (A14) | NOT WIRED | Connect when data source available | ENG (blocked) | P2 |
| INT-05 | IoT / machine telemetry | STUB `iot_live=false` | Live IoT/MES on PH1-02 | ENG (blocked) | P1 |
| INT-06 | Odoo PO / invoice write-back | Logic present; not live | Execute on PH1-02 | ENG (blocked) | P1 |
| ~~INT-07~~ | ~~ERP connections routes (Spec 023)~~ | **ENG CLOSED** — CRUD/Fernet/UI shipped; GH hygiene close | — | — | — |
| INT-08 | Keycloak SSO | Scaffold ready; R1 uses JWT | Activate only if tenant requires SSO | ENG (on demand) | P2 |

---

## 3. Engineering residuals

### 3.1 Still OPEN (stack / quality)

| ID | Topic | Needed action | Owner | Priority | Ref |
|----|-------|---------------|-------|----------|-----|
| ENG-03 | #70/#72/#110/#120/#136 validate absorb | Evidence commented; **leave OPEN** for human close | ENG | P1 | GH#110,#120,#136 |
| QA-02 | Playwright flakes | Stabilize selectors/timeouts | ENG | P2 | Spec 029 notes |
| QA-05 | Copilot live chat | Re-verify when LLM up | ENG | P2 | — |

### 3.1b Resolved on R2 (2026-07-25 / 2026-08-01) — do not auto-close GH without human review

| ID | Topic | Resolution |
|----|-------|------------|
| ENG-01 / ENG-02 | #70/#72 star-trans-validate | **PASS** 17/0/1 SKIP (Odoo — PH1-02). Evidence: `docs/qa/STAR-TRANS-VALIDATE-2026-07-25.txt` |
| QA-01 | k6 SLO p95 | **PASS** 2026-07-25 p95 **165ms**; re-run 2026-08-01 — see `docs/qa/K6-FINAL-RUN-REPORT.md` |
| ~~QA-04~~ | RLS residual | **ENG CLOSED** lab 082 — 135 tenant tables / 0 gaps (`docs/qa/QA-04-RLS-AUDIT-2026-08-01.md`) |
| ~~QA-06~~ | Kong enterprise/phase8 smoke | **PASS** 2026-08-01 (`docs/qa/KONG-SMOKE-2026-08-01.md`) |
| 9A-OPS-2 | ATP/approvals DB persist | **ENG CLOSED** — `try_persist` + `test_phase9_persist.py` (5 passed) |
| 9A-OPS-3 | Redis EventBus wire | **ENG CLOSED** — dpe/connector/upload + publish smoke (`docs/qa/EVENTBUS-SMOKE-2026-08-01.md`) |
| T165 | Phase9 EN/AR wave labels | **ENG CLOSED** keys in `locales/en.json` + `ar.json` (#160 progress; ≠ G-R2-04) |

### 3.2 ~~CLOSED Wave 1 eng~~ (strikethrough — do not reopen)

| ID | Topic | Resolution |
|----|-------|------------|
| ~~ENG-04~~ | ~~Andon dual-write~~ | Spec 029 **BUILT** (push notifications still Wave 2) |
| ~~ENG-05~~ | ~~S&OP stage-gate scaffold~~ | Spec 029 **BUILT** (UI polish Wave 2) |
| ~~ENG-07~~ | ~~MPS/MRP persistence 069~~ | Spec 029 **BUILT** |

### 3.3 Deferred Wave 2 / 8B–8D (roadmap — not R1 blockers)

| ID | Topic | Horizon |
|----|-------|---------|
| ENG-06 | Collaborative multi-user locking UI | Wave 2 |
| ENG-08 | Monetary net-saving in leveling | Wave 2 |
| ENG-09 | Operator tablet UI | Wave 2 |
| ENG-10 | Alert inbox SLA UI | Wave 2 |
| ENG-11 | Deeper OR-Tools multi-resource/campaign | Wave 2 |
| ENG-12 | Phase 8B–8D (A18 live, Excel everywhere, launch) | 8B–8D |
| ENG-13 | Future W2/W3 GH (#37/#38/#42–#46) + enterprise #15–#26 | Roadmap |
| OPS-01 | WhatsApp / Comms Hub | Wave 2 |

---

## 4. Release / tagging

| ID | Topic | Needed action | Owner | Priority |
|----|-------|---------------|-------|----------|
| REL-01 | `v9.1.1-r2` HOLD | After G-R2-04 sign-off, cut tag | ENG (gated by HUMAN) | P0 |
| REL-02 | `v9.1.0-r2` stale | **NEVER push** | ENG | P1 |

---

## 5. Ops / support (OPEN)

| ID | Topic | Needed action | Owner | Priority |
|----|-------|---------------|-------|----------|
| OPS-02 | Customer VM + champion | Provision 8GB VM + training champion | CUST / OPS | P1 |
| OPS-03 | Live-stack validate re-run | **DONE 2026-07-25** PASS 17/0/1 SKIP — see `docs/qa/STAR-TRANS-VALIDATE-2026-07-25.txt` | OPS / ENG | P1 |
| OPS-04 | Monitoring activation | Confirm dashboards/alerts in customer deploy | OPS | P2 |
| OPS-05 | Backup / DR drill | Execute restore drill before go-live | OPS | P2 |

---

## Top 10 priorities / recommended next actions

1. **[COM]** Decide OQ-7 pricing and remove SOW placeholders (C-01, GH#106)
2. **[CUST/OPS]** Provision live Odoo staging PH1-02 (C-03, GH#108)
3. **[HUMAN]** G-R2-04 Arabic native sign-off → `v9.1.1-r2` (C-04, GH#109, REL-01)
4. **[CUST]** Confirm Odoo 17 vs 19 OQ-1 (C-05, GH#107)
5. **[ENG]** Human-close GH #70/#72/#110/#120/#136 after reviewing validate PASS comments (ENG-03 — eng will not auto-close)
6. **[ENG]** Keep k6 warm-up ≥90s for release gates (QA-01)
7. **[ENG]** Stabilize Playwright flakes (QA-02)
8. **[ENG]** Copilot live re-verify when LLM up (QA-05)
9. **[OPS]** Backup/restore + DR drill + monitoring confirm (OPS-05, OPS-04)
10. **[CUST/OPS]** PH1-02 live Odoo staging (C-03) — blocks live integrations

---

*Honesty: COM/Human items are never marked resolved by engineering. Live Odoo and Arabic native sign-off are never faked. Sources: FINAL-PROGRAM-STATUS.md, PRODUCT-STATUS.md, OPEN-ITEMS.md, PHASE{3–8} reports, Spec 029/030/032, `gh issue list`.*
