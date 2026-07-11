---
status: CLOSED
closed_by: foundation
date: 2026-07-11
---
# Feature Specification: Release 2 — Commercial Growth & Agentic Planning

**Feature**: `014-release2-growth`  
**Version**: 1.0  
**Date**: 2026-07-01  
**Status**: Specify complete — pending UAT on 013 tag  
**Depends on**: `013-release1-odoo-mena` (13/13 integration PASS, 96/100 converge)  
**Customer anchor**: Star Trans (customer #1) + second Odoo prospect  
**Release target**: `v9.1.0-r2`  
**Constitution**: `.specify/memory/constitution.md` v1.1.0 — Principles I–III, VII

---

## 1. Vision (what we want to build)

> **After Release 1 proves Odoo sync works, Release 2 turns IPE from a planning dashboard into a revenue-generating outcomes platform: planners get suggested mitigations the moment ERP data changes, executives see OTD/ROI proof, and optional conversational access accelerates triage — without replacing Odoo or bloating the 8 GB VM profile.**

**Strategic positioning (from product assessment 2026-06-30):**

| Dimension | Release 1 (shipped) | Release 2 (this spec) |
|-----------|---------------------|------------------------|
| Buyer story | "See at-risk MOs from Odoo" | "Save MOs + prove ROI to renew" |
| AI posture | Hidden | Copilot Lite (structured, no GPU required) |
| Resolution | Static seeded scenarios | Auto-proposed after  rescore/sync |
| ERP write-back | Schedule dates only | Resolution drafts → Odoo chatter/PO |
| Executive value | APIs exist | Outcomes dashboard + QBR export |

**Pricing evolution:** $24K/yr → $30K/yr with Outcomes + Copilot Lite tier.

---

## 2. What we have built (baseline)

| Asset | Status | Evidence |
|-------|--------|----------|
| Release 1 integration 13/13 | ✅ | `release1-integration-demo-final.txt` |
| res-svc scenario engine + API | ✅ | `POST /resolution/scenarios` |
| fea-svc rescore after sync | ✅ | `connector/_rescore_synced_mos` |
| Kafka feasibility_scored consumer (res-svc) | ⚠️ Partial | Handler uses wrong field `demand_line_id`; no DB persist in consumer |
| ROI + OTD baseline APIs | ✅ | `dpe-svc/analytics` |
| nlp-svc Copilot (full stack) | ✅ | Hidden in release1 profile |
| Odoo schedule write-back | ✅ | cap-svc direct activate |

---

## 3. Scope — Release 2 streams

### Stream A — Agentic Resolution Loop (P0)

**User story:** As a **planner**, when Odoo sync rescored an MO below 75% feasibility, I want **fresh resolution scenarios** in Resolution Center without manual refresh, so I can act before the shift starts.

**Acceptance criteria:**
- After sync rescore, MOs with score &lt; 75% receive ≥3 proposed scenarios in `cdm_resolution_scenario`
- Idempotent: re-sync does not duplicate identical strategy rows for same MO
- Release 1 stack (no Kafka required): HTTP trigger from connector → res-svc
- Demo: MO-ST-001 shows new scenarios after `POST /sync/run`

### Stream B — Customer Outcomes Dashboard (P0)

**User story:** As an **CEO/Ops director**, I want a **single Outcomes view** showing OTD trend, baseline delta, MOs saved, and sync health, so I can justify renewal in QBR.

**Acceptance criteria:**
- New Command Center tab **Outcomes** visible in release1 profile
- Displays: current 30d OTD, baseline (capture button if missing), weekly ROI metrics, last sync status
- Arabic labels for Star Trans (i18n keys)
- Export: copy summary text or print-friendly view

### Stream C — Planner Copilot Lite (P1)

**User story:** As a **planner**, I want to **ask plain-language questions** about at-risk MOs and stock, without learning the UI, so triage time drops ≥30%.

**Acceptance criteria:**
- 5 supported intents: `at_risk_mos`, `mo_detail`, `scenario_list`, `sync_status`, `schedule_summary`
- Works on release1 stack: structured fallback (no Ollama required); optional Ollama when hybrid profile
- Responses cite MO IDs and scores from live APIs
- Latency &lt; 3s for structured path

### Stream D — Odoo Resolution Write-Back (P1)

**User story:** As a **planner**, when I **approve a resolution scenario**, I want a **draft PO or chatter note** in Odoo, so shop floor sees the decision in ERP.

**Acceptance criteria:**
- Approved scenarios create Odoo `mail.message` on linked MO or draft `purchase.order` for expedite_po strategy
- Human approve required; no silent ERP mutation
- Audit log entry in IPE

### Stream E — Managed SaaS Foundations (P2, POST-R2)

Deferred to `015-saas-foundation`: Keycloak, Stripe, tenant provisioning API.

---

## 4. Functional requirements

| ID | Requirement | Priority | Stream |
|----|-------------|----------|--------|
| FR-R2-01 | Auto-propose resolution scenarios when feasibility &lt; threshold after sync/rescore | P0 | A |
| FR-R2-02 | Configurable feasibility threshold per tenant (default 75%) | P1 | A |
| FR-R2-03 | Outcomes dashboard UI in Command Center (release1 visible) | P0 | B |
| FR-R2-04 | OTD baseline capture from Outcomes UI | P0 | B |
| FR-R2-05 | Combined outcomes summary API (optional aggregator) | P2 | B |
| FR-R2-06 | Copilot Lite endpoint with 5 planner intents | P1 | C |
| FR-R2-07 | Copilot Lite panel in Control Tower (collapsible) | P1 | C |
| FR-R2-08 | Odoo chatter note on scenario approve | P1 | D |
| FR-R2-09 | Odoo draft PO on expedite_po approve | P2 | D |
| FR-R2-10 | Integration demo script 014 (5 streams smoke) | P0 | All |
| FR-R2-11 | Release 2 compose profile (optional nlp-svc) | P1 | C |

---

## 5. Success criteria (measurable)

| ID | Criterion | Target |
|----|-----------|--------|
| SC-R2-01 | Integration demo pass rate | 5/5 R2 checkpoints PASS |
| SC-R2-02 | Auto-propose latency after sync | &lt; 10s for 10 MOs |
| SC-R2-03 | Planner triage time (qualitative UAT) | ≥30% reduction vs R1 baseline |
| SC-R2-04 | Executive can capture OTD baseline in &lt; 2 clicks | UAT sign-off |
| SC-R2-05 | Copilot Lite structured path | &lt; 3s p95 |
| SC-R2-06 | No regression on R1 13/13 integration demo | 13/13 PASS after R2 merge |

---

## 6. Out of scope (Release 2)

- Live SAP / D365 connectors (customer #2+)
- Full 22-service hybrid requirement for R2 go-live
- Autonomous schedule without human approve
- Kafka migration for release1 profile
- Stripe / Keycloak production (→ 015)

---

## 7. Assumptions

- Star Trans UAT on 013 completes before R2 customer-facing rollout
- Odoo 19 XML-RPC remains integration transport
- Release 1 VM stays ≤8 GB RAM; Copilot Lite uses structured fallback by default
- Second customer also on Odoo

---

## 8. User stories summary

| ID | Role | Story |
|----|------|-------|
| US-R2-01 | Planner | See auto-generated scenarios after Odoo sync |
| US-R2-02 | Planner | Ask "which MOs are at risk?" in Copilot Lite |
| US-R2-03 | Executive | View OTD vs baseline on Outcomes page |
| US-R2-04 | Executive | Export QBR summary |
| US-R2-05 | Plant manager | Approve scenario → Odoo note visible to team |
| US-R2-06 | Admin | Set auto-propose feasibility threshold |
