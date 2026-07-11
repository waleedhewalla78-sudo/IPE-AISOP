---
status: CLOSED
closed_by: foundation
date: 2026-07-11
---
# Feature Specification: Release 1 — Odoo Live + MENA Customer Go-Live

**Feature**: `013-release1-odoo-mena`  
**Version**: 2.1 (post-implement)  
**Date**: 2026-06-24  
**Status**: **88/100 — engineering complete, UAT blocked on customer inputs**  
**Customer**: Star Trans — Electrical Transformer Technology (Egypt)  
**ERP**: Odoo 17.0 / 19.0 compatible  
**Release target**: `v9.0.0-r1`  
**Constitution**: `.specify/memory/constitution.md` v1.1.0 — Principle VII

---

## 1. Vision (what we want to build)

> **Planners know which orders are at risk a day before it becomes a crisis, they have structured options to resolve it, and that information comes from their actual Odoo data — not a spreadsheet someone maintained manually.**

**Positioning (from strategic assessment):**

- **Sell against:** Excel + Odoo MRP — not Kinaxis/SAP IBP
- **Moat:** MENA implementation partner + feasibility-before-the-shift workflow — not Copilot or Kafka
- **Buyer:** CEO / Operations Director — not IT steering committee
- **Pricing:** $18K–30K/yr license + $12K–25K implementation

---

## 2. What we have built (inventory)

### 2.1 Platform v8.2.0 (demo / sales — complete)

| Asset | Status | Use |
|-------|--------|-----|
| 32/32 demo checkpoints | ✅ | Investor/sales demos |
| 22-service full stack | ✅ | Development only |
| Star Trans SQL overlay (012) | ✅ | Live demo on laptop |
| 870+ backend tests | ✅ | Engineering quality signal |

### 2.2 Release 1 engineering (013 — implemented)

| Component | Status | Evidence |
|-----------|--------|----------|
| Migration 036 (sync_run, data_quality_flag, MO ERP columns) | ✅ | `036_r1_odoo_sync_tables.py` |
| Odoo 17 mappers (product, MO, BOM, WC) | ✅ | `app/core/mapper.py` |
| Sync engine (upsert MO/BOM/WC/products/lines/routing/inventory) | ✅ | `app/odoo/sync_engine.py` |
| Post-sync feasibility rescore | ✅ | `_rescore_synced_mos()` |
| BOM line + routing sync | ✅ | `sync_bom_details()` |
| stock.quant inventory sync | ✅ | `sync_inventory()` → product.safety_stock |
| Sync failure alert hook | ✅ | `app/core/sync_alerts.py` |
| Admin Odoo config UI + API | ✅ | `AdminPage` Odoo tab, `/admin/erp/odoo` |
| web-ui in release1 compose | ✅ | `Dockerfile.release1`, nginx proxy |
| Arabic Resolution + Login i18n | ✅ | `ResolutionCenterPage`, `LoginForm` |
| SYNC_CONFLICT badge (Control Tower) | ✅ | queue API + UI badge |
| Sync audit + data quality flags | ✅ | `cdm_sync_run`, validation |
| Sync status APIs | ✅ | `GET /sync/status`, `/data-quality` |
| 15-min scheduler | ✅ | `jobs/sync_scheduler.py` |
| fea-svc unscorable MOs + queue flags | ✅ | `scorer.py`, `feasibility.py` |
| cap-svc direct Odoo activate | ✅ | `ERP_SYNC_MODE=direct` |
| release1 compose (8 services) | ✅ | `docker-compose.release1.yml` |
| Kong release1 routes | ✅ | `kong.release1.yml` |
| Deploy + smoke + ROI scripts | ✅ | `scripts/deploy-release1.ps1`, etc. |
| Arabic MVP (Control Tower, nav) | ✅ | `locales/ar.json`, i18n |
| Sync status bar + DQ badges | ✅ | `SyncStatusBar.tsx` |
| release1 nav profile | ✅ | `releaseProfile.ts` |
| Implementation + support playbooks | ✅ | `docs/implementation/`, `docs/runbooks/` |
| Odoo install + field mapping docs | ✅ | `docs/integration/` |

**Readiness score:** 90/100 (engineering complete; customer UAT pending)

---

## 3. What is missing (gap analysis)

### 3.1 P0 — blocks Star Trans go-live

| Gap | Impact | Owner |
|-----|--------|-------|
| **Odoo staging credentials** (T003) | Cannot validate MO sync on real data | Customer IT |
| **Signed SOW** (T002) | No contractual scope | Business |
| **Live Odoo UAT** (T025–T026, T071) | Unknown mapper breakage on custom fields | Eng + Customer |
| **`ipe_connector` installed on Star Trans Odoo** | Write-back / events incomplete | Customer IT |
| **BOM line + routing sync from Odoo** | ✅ Done (T080) | Engineering |
| **Post-sync feasibility rescore job** | ✅ Done (T082) | Engineering |
| **Resolution Center Arabic strings** | ✅ Done (T084) | Engineering |
| **Login page Arabic** | ✅ Done (T084) | Engineering |

### 3.2 P1 — needed before production hardening

| Gap | Impact | Phase |
|-----|--------|-------|
| Admin UI: Odoo connection test + save creds (T049) | ✅ Done | R1 |
| `stock.quant` / material availability sync (FR-R1-05) | ✅ Done (safety_stock proxy) | R1 |
| Sync failure alert (email/WhatsApp hook) | ✅ Webhook hook (`ODOO_SYNC_ALERT_WEBHOOK`) | R1.1 WhatsApp template |
| CI job for release1 compose (T036) | ✅ `.github/workflows/ci.yml` | R1 |
| Windows 8GB VM deploy validation (T037) | On-prem promise unproven | R1.1 |
| Integration tests with live/mock Odoo container | T025–T026 automated | R1.1 |

### 3.3 P2 — explicitly deferred (do not build now)

| Item | Phase | Rationale |
|------|-------|-----------|
| Copilot / nlp-svc | R2 | Commodity; hidden in release1 |
| Demand sensing, scenarios, supply network | R2 | Not in Star Trans SOW |
| SAP B1 / D365 connectors | R2 | Customer #2+ |
| Keycloak SSO, Stripe | R2 | Manual auth/invoice for R1 |
| Kafka in release1 | Never for R1 | Batch sync sufficient |
| 22-service K8s production | R3 | After 3 customers |
| Full 15-screen Arabic | R2 | MVP covers planner path |
| New v8.3 platform features | Never pre-UAT | Assessment: stop feature sprint |

---

## 4. Recommendations (from last assessment)

### 4.1 Strategic (business — do now)

| # | Recommendation | Action |
|---|----------------|--------|
| R-B1 | **Customer sprint over feature sprint** | Freeze platform scope until Star Trans UAT passes |
| R-B2 | **One ERP, one customer, end-to-end** | Odoo 17 only; ignore SAP until customer #2 |
| R-B3 | **Formalize PoC → production SOW** | Use `R1-IMPLEMENTATION-PLAYBOOK.md` §sign-off |
| R-B4 | **Start second prospect in parallel** | OQ-5 within 60 days — don't wait for UAT |
| R-B5 | **Lead with feasibility-first** | Demo/pitch: Control Tower + Resolution, not Copilot |
| R-B6 | **WhatsApp support in contract** | Documented in support runbook — competitive advantage |

### 4.2 Technical (engineering — do before/at UAT)

| # | Recommendation | Priority |
|---|----------------|----------|
| R-T1 | Complete **routing + BOM line sync** from Odoo | P0 |
| R-T2 | Add **post-sync rescore** (call fea-svc for new/updated MOs) | P0 |
| R-T3 | Finish **Arabic on Resolution + Login** | P0 |
| R-T4 | Build **Admin Odoo config UI** | P1 |
| R-T5 | Run **release1-smoke.ps1** on every PR touching R1 paths | P1 |
| R-T6 | Record **Odoo field mapping worksheet** with Star Trans IT | P0 (business) |

### 4.3 Anti-patterns (do not do)

- Do not run `seed-startrans-overlay.sql` for production — Odoo is source of truth
- Do not deploy 22-service stack to customer factory
- Do not pitch Kinaxis feature matrix to Star Trans CEO
- Do not add Copilot to release1 nav

---

## 5. User stories — status matrix

| ID | Story | Priority | Build status | UAT status |
|----|-------|----------|--------------|------------|
| US-01 | MOs from Odoo in Control Tower | P0 | ✅ Code | ⬜ Needs live Odoo |
| US-02 | BOM + routing synced | P0 | ✅ Code | ⬜ Needs live Odoo |
| US-03 | Work centers synced | P0 | ✅ Code | ⬜ Needs live Odoo |
| US-04 | Scheduled sync + visible status | P0 | ✅ Code + alert hook | ⬜ Needs live Odoo |
| US-05 | Graceful bad data handling | P0 | ✅ Code | ⬜ Needs live Odoo |
| US-06 | At-risk MOs sorted | P0 | ✅ Existing fea-svc | ✅ With seed data |
| US-07 | Resolution scenarios | P0 | ✅ Existing dpe-svc | ✅ With seed data |
| US-08 | Unscorable MOs labeled | P0 | ✅ Code | ⬜ Needs live Odoo |
| US-09 | Schedule write-back to Odoo | P0 | ✅ direct activate | ⬜ Needs live Odoo |
| US-10 | SYNC_CONFLICT badge | P0 | ✅ Code | ⬜ Needs live Odoo |
| US-11 | Executive OTD trend | P1 | ✅ Existing UI | 🟡 Baseline manual |
| US-12 | MOs saved metric | P1 | ✅ API | ⬜ Customer tracking |
| US-13 | Arabic Control Tower | P0 | ✅ | 🟡 QA with native speaker |
| US-14 | Arabic Resolution | P0 | ✅ | 🟡 Native speaker QA |
| US-15 | Arabic nav/login/alerts | P0 | ✅ | 🟡 Native speaker QA |
| US-16 | release1 on 8GB VM | P0 | ✅ Compose | ⬜ T037 manual |
| US-17 | Support runbook | P0 | ✅ Doc | ✅ |
| US-18 | Implementation playbook | P0 | ✅ Doc | ✅ |

**Legend:** ✅ Done · 🟡 Partial · ⬜ Not done / not validated

---

## 6. Functional requirements — compliance

| ID | Requirement | Status |
|----|-------------|--------|
| FR-R1-01 | MO sync upsert | ✅ |
| FR-R1-02 | BOM + **BOM lines** sync | ✅ |
| FR-R1-03 | Work center sync | ✅ |
| FR-R1-04 | Product update path | ✅ |
| FR-R1-05 | Stock/material availability | ✅ |
| FR-R1-06 | Scheduled sync 15 min | ✅ |
| FR-R1-07 | Sync run log | ✅ |
| FR-R1-08 | Data quality flags | ✅ |
| FR-R1-09 | Conflict detection | ✅ |
| FR-R1-10 | Activate write-back | ✅ |
| FR-R1-11 | Odoo install guide | ✅ |
| FR-R1-12 | Feasibility skip flagged MOs | ✅ |
| FR-R1-13 | Queue with data_quality_flags | ✅ |
| FR-R1-14 | Resolution scenarios | ✅ (seed); ⬜ auto-gen post-sync |
| FR-R1-15 | Schedule approve → Odoo | ✅ |
| FR-R1-16 | OTD baseline capture | ✅ |
| FR-R1-17 | Sync status widget | ✅ |
| FR-R1-18 | Data quality on Control Tower | ✅ |
| FR-R1-19 | Conflict badge | ✅ |
| FR-R1-20 | i18n ar/en | ✅ Framework |
| FR-R1-21 | Language switcher | ✅ |
| FR-R1-22 | Hide POST-R1 hubs | ✅ |
| FR-R1-23–26 | Ops docs + compose | ✅ |

---

## 7. Release 1 vs future roadmap

```text
NOW (013 — Star Trans UAT)          R1.1 (post-UAT hardening)        R2 (customer #2+)
────────────────────────────          ─────────────────────────        ─────────────────
• Odoo MO/BOM/WC sync                 • Routing + BOM lines sync       • SAP B1 connector
• Control Tower + Resolution        • Post-sync rescore              • Copilot (optional)
• Schedule write-back                 • Admin Odoo UI                  • Demand/scenarios
• Arabic MVP                          • Vault creds                    • Keycloak SSO
• release1 compose                    • Sync failure alerts            • Odoo partner channel
• Playbooks + runbooks                • OTD baseline API               • 3rd customer
• 90-day ROI clock                    • CI release1 gate               • Full Arabic
```

---

## 8. Success criteria (90-day — unchanged)

| # | Metric | Target | Instrumented? |
|---|--------|--------|---------------|
| SC-R1-01 | Planner opens IPE before Excel | ≥4 days/week by week 4 | ⬜ Manual observation |
| SC-R1-02 | At-risk MOs resolved pre-late | ≥2/month | ⬜ |
| SC-R1-03 | OTD trend improving | vs week-1 baseline | 🟡 export-roi-metrics.ps1 |
| SC-R1-04 | Sync reliability | ≥95% | ✅ cdm_sync_run |
| SC-R1-05 | MOs scorable | ≥80% in 30 days | ✅ data_quality flags |
| SC-R1-06 | Referenceable CEO | 1 call | ⬜ Business |

---

## 9. Dependencies (updated)

| Dependency | Status |
|------------|--------|
| OQ-1 Star Trans | ✅ Locked |
| OQ-3 Odoo 17 | ✅ Locked |
| OQ-2 Cloud vs on-prem | ⬜ Default: Diligent cloud |
| OQ-4 SOW | ⬜ |
| Odoo staging access | ⬜ **Critical blocker** |
| v8.2.0 platform | ✅ |
| 013 code | ✅ 78/100 |

---

## 10. References

- `docs/implementation/R1-IMPLEMENTATION-PLAYBOOK.md`
- `docs/runbooks/R1-SUPPORT-RUNBOOK.md`
- `docs/integration/ODOO-CONNECTOR-INSTALL.md`
- `specs/013-release1-odoo-mena/clarify.md`
- `specs/013-release1-odoo-mena/analyze.md`
- Strategic assessment (2026-06-29) — demo vs customer readiness
