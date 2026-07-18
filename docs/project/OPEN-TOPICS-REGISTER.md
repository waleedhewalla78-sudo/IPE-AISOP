# IPE Platform — Open Topics Register

**Compiled:** 2026-07-17 · **Updated:** 2026-07-18 (program finalize — all phases/waves)
**Workspace:** `E:\AISOP\ipe` (canonical)
**Authoritative finalize:** `docs/project/FINAL-PROGRAM-STATUS.md`
**GitHub repo:** `waleedhewalla78-sudo/IPE-AISOP`
**Maintainer split:** Commercial/Human — Waleed / Star Trans; Engineering — Engineering Lead

---

## Executive summary

Wave 1 engineering for Ops Blueprint Phases 3–7, Spec 029 productionization, and Spec 030 Phase 8 **8A** is **ENG COMPLETE**. R1 verdict: **ENG READY / COM CONDITIONAL**.

| Category | Remaining OPEN | Notes |
|----------|---------------:|-------|
| 1. Commercial / Human | **8** | Never fake |
| 2. Integrations (live) | **5** | Gated by PH1-02 (+ Keycloak on-demand) |
| 3. Engineering / stack / QA | **6** | Validate, k6, flakes, RLS audit, Copilot, Kong smoke |
| 4. Ops / support | **4** | VM, validate ops, monitoring, DR |
| 5. Release / tagging | **2** | HOLD + stale-tag policy |
| **Actionable total** | **≈25** | Excludes Wave 2 / 8B–8D roadmap |
| Deferred roadmap | Wave 2 / 8B–8D / W2–W3 GH | Not R1 eng blockers |

**Closed eng (do not re-open):** INT-01 Kong `/api/v1/enterprise` (+ `/phase8`) route objects shipped; Specs 022–030 Wave 1 product scope; Spec 029 Andon/RLS/MPS/stage-gate; Spec 030 8A scaffold.

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
| ENG-01 | #70 seed demo MOs | Seed when R2 healthy | ENG | P1 | GH#70 |
| ENG-02 | #72 star-trans-validate | Re-run after ENG-01 | ENG | P1 | GH#72 |
| ENG-03 | #110/#120/#136 validate absorb | Close with #70/#72 when stack up | ENG | P1 | GH#110,#120,#136 |
| QA-01 | k6 p95 under load | Profile + tune + re-run | ENG | P1 | Spec 029 notes |
| QA-02 | Playwright flakes | Stabilize selectors/timeouts | ENG | P2 | Spec 029 notes |
| QA-04 | RLS residual tables | Audit remaining after 068 | ENG | P1 | Campaign report |
| QA-05 | Copilot live chat | Re-verify when LLM up | ENG | P2 | — |
| QA-06 | Live Kong enterprise/phase8 smoke | Smoke when gateway healthy (routes exist) | ENG | P1 | — |

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
| OPS-03 | Live-stack validate re-run | `star-trans-validate.ps1 -DpePort 8020 -ConnectorPort 8016` | OPS / ENG | P1 |
| OPS-04 | Monitoring activation | Confirm dashboards/alerts in customer deploy | OPS | P2 |
| OPS-05 | Backup / DR drill | Execute restore drill before go-live | OPS | P2 |

---

## Top 10 priorities / recommended next actions

1. **[COM]** Decide OQ-7 pricing and remove SOW placeholders (C-01, GH#106)
2. **[CUST/OPS]** Provision live Odoo staging PH1-02 (C-03, GH#108)
3. **[HUMAN]** G-R2-04 Arabic native sign-off → `v9.1.1-r2` (C-04, GH#109, REL-01)
4. **[CUST]** Confirm Odoo 17 vs 19 OQ-1 (C-05, GH#107)
5. **[ENG/OPS]** Bring R2 stack healthy → seed MOs → star-trans-validate → close #70/#72/#110/#120/#136 (ENG-01/02/03, OPS-03)
6. **[ENG]** Tune k6 p95 under concurrent load (QA-01)
7. **[ENG]** Live Kong smoke `/enterprise/*` + `/phase8/*` when gateway up (QA-06) — **routes already shipped; do not “add route”**
8. **[ENG]** Close residual RLS gaps post-068 (QA-04)
9. **[ENG]** Stabilize Playwright flakes (QA-02)
10. **[OPS]** Backup/restore + DR drill + monitoring confirm (OPS-05, OPS-04)

---

*Honesty: COM/Human items are never marked resolved by engineering. Live Odoo and Arabic native sign-off are never faked. Docker was down on 2026-07-18 finalize — validate left OPEN. Sources: FINAL-PROGRAM-STATUS.md, PRODUCT-STATUS.md, OPEN-ITEMS.md, PHASE{3–8} reports, Spec 029/030, `gh issue list`.*
