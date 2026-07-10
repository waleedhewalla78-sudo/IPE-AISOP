# Tasks: IPE Phase 2 Release 2 (018)

**Version**: 1.0 | **Date**: 2026-07-10  
**Authority**: `docs/PHASE2-IMPLEMENTATION-GUIDE.md` + `docs/PHASE2-SPRINT-PLAN.md`  
**Target tag**: `v9.1.0-r2`  
**Constitution**: v1.2.4  
**Depends on**: Spec 017 Wave 1 partial, migration head **038**

---

## Wave 1 bridge (execute before S3â€“S4)

| ID | Sprint | Task | Priority | Status | Spec 017 |
|----|--------|------|----------|--------|----------|
| W1-03 | â€” | Odoo Config v2 schema + API | P0 | âœ… | #31 |
| W1-04 | â€” | Odoo connection test <5s | P0 | âœ… | #32 |
| W1-05 | â€” | Odoo multi-entity + versioning | P1 | âœ… | #33 |
| W1-06 | â€” | Odoo Config React UI | P1 | âœ… | #34 |
| W1-07 | â€” | OTD aggregation API (5 KPIs) | P0 | âœ… | #35 |
| W1-08 | â€” | OTD dashboard UI | P0 | âœ… | #36 |

---

## Sprint S1 â€” R2 environment

| ID | Task | Status | Deliverable |
|----|------|--------|-------------|
| S1-01 | `docker-compose.release2.yml` | âœ… | 11â€“12 containers up |
| S1-02 | `kong.release2.yml` | âœ… | nlp, demand, scenario routes |
| S1-03 | `release2` frontend profile | âœ… | Demand + Scenarios hubs |
| S1-04 | `deploy-release2.ps1` / `.sh` | âœ… | Deploy script |
| S1-05 | `release2-smoke.ps1` | âœ… | Script ready; gate FAIL until deploy |
| S1-06 | `e2e/release2-nav.spec.ts` | âœ… | Nav regression |

**Gate**: `release2-smoke.ps1` PASS

---

## Sprint S2 â€” Copilot live data

| ID | Task | Status | File |
|----|------|--------|------|
| S2-01 | Planning tools (7 APIs) | âœ… | `nlp-svc/.../copilot_tools.py` |
| S2-02 | Shadow mode default | âœ… | `copilot_agent.py` |
| S2-03 | LLM fallback chain verify | âœ… | `llm_client.py` |
| S2-04 | Copilot panel tenant + timeout | âœ… | `CopilotPanel` |
| S2-05 | `test_copilot_tools_r2.py` | âœ… | Unit tests |

**Gate**: Live MO/feasibility query via Copilot

---

## Sprint S3 â€” Demand (SES-first)

| ID | Task | Status | Note |
|----|------|--------|------|
| S3-01 | SES on `cdm_demand_line` | âœ… | Not full Prophet (Spec 017) |
| S3-02 | Forecast API | âœ… | horizon 7/14/30 |
| S3-03 | Control Tower overlay | âœ… | Gap highlighting |
| S3-04 | Demand tab UI | âœ… | MAPE display |
| S3-05 | `test_forecaster_r2.py` | âœ… | |

**Maps**: W2-05 (#41) modified

---

## Sprint S4 â€” Scenarios

| ID | Task | Status |
|----|------|--------|
| S4-01 | Simulator KPI delta | âœ… |
| S4-02 | simulate/list/get API | âœ… |
| S4-03 | Scenarios UI compare | âœ… |
| S4-04 | `test_simulator_r2.py` | âœ… |

**Maps**: W2-03, W2-04 (#39â€“#40)

---

## Sprint S5 â€” Arabic 8+ screens

| ID | Task | Status |
|----|------|--------|
| S5-01 | Expand `ar.json` (8+ screens) | âœ… |
| S5-02 | RTL layout validation | âœ… |
| S5-03 | Language toggle persistence | âœ… |
| S5-04 | `docs/qa/arabic-qa-r2.md` | âœ… |
| S5-05 | `e2e/arabic-r2.spec.ts` | âœ… |

**Maps**: PH1-05 Â· **Gate prep**: G-R2-04 (native speaker sign-off pending)  
**Report**: `sprints/S5-report.md` Â· **Keys**: 299 ar/en parity (+199 ar, +210 en)

---

## Sprint S6 â€” OTD analytics extended

| ID | Task | Status | Migration |
|----|------|--------|-----------|
| S6-01 | OTD trend API | âœ… | â€” |
| S6-02 | Root-cause API | âœ… | â€” |
| S6-03 | Cost-of-chaos API | âœ… | â€” |
| S6-04 | Baseline comparison API | âœ… | â€” |
| S6-05 | OTDDashboard.tsx + PDF | âœ… | â€” |
| S6-06 | Migration `039_cdm_otd_snapshot` | âœ… | **039** |

> Skip duplicate if W1-07/08 already delivered baseline dashboard.

---

## Sprint S7 â€” Odoo admin polish

| ID | Task | Status |
|----|------|--------|
| S7-01 | DQ flags dashboard | âœ… |
| S7-02 | Sync history table (last 10) | âœ… |
| S7-03 | Partner wizard polish | âœ… |

> Core UI in W1-06; S7 = extended guide scope. **Report**: `sprints/S7-report.md`

---

## Sprint S8 â€” Multi-tenant ops

| ID | Task | Status | Migration |
|----|------|--------|-----------|
| S8-01 | `ops.py` tenant health API | âœ… | â€” |
| S8-02 | Tenant alerts API | âœ… | â€” |
| S8-03 | OpsDashboard.tsx | âœ… | â€” |
| S8-04 | `test_ops_dashboard.py` | âœ… | â€” |
| S8-05 | Migration `040_cdm_tenant_health` | âœ… | **040** |

**Maps**: W2-01, W2-02 (#37â€“#38) Â· Report: `sprints/S8-report.md`

---

## Sprint S9 â€” Production intelligence

| ID | Task | Status |
|----|------|--------|
| S9-01 | cap-svc analytics API | âœ… |
| S9-02 | Copilot `analyze_quality_patterns` | âœ… |
| S9-03 | Tests | âœ… |

**Report**: `sprints/S9-report.md`

---

## Sprint S10 â€” Supply chain intelligence

| ID | Task | Status | Migration |
|----|------|--------|-----------|
| S10-01 | Supplier risk API | âœ… | â€” |
| S10-02 | Inventory ABC / slow-moving | âœ… | â€” |
| S10-03 | Copilot SC tools | âœ… | â€” |
| S10-04 | Tests | âœ… | â€” |
| S10-05 | Migration `041_cdm_supplier_score` | âœ… | **041** |

**Report**: `sprints/S10-report.md`

---

## Sprint S11 â€” S&OP synthesis

| ID | Task | Status | Migration |
|----|------|--------|-----------|
| S11-01 | `sop_report.py` | âœ… | â€” |
| S11-02 | reports API | âœ… | â€” |
| S11-03 | SOPReport.tsx + PDF | âœ… | â€” |
| S11-04 | Tests | âœ… | â€” |
| S11-05 | Migration `042_cdm_sop_report` | âœ… | **042** |

**Report**: `sprints/S11-report.md`

---

## Sprint S12 â€” SAP B1 â€” CUT

| ID | Task | Status | Reason |
|----|------|--------|--------|
| S12-ALL | SAP B1 scaffold | **CUT** | Spec 017 Â§5; Strategy Assessment |

---

## Migrations queue (post-038)

| ID | Migration | Sprint |
|----|-----------|--------|
| M-039 | `cdm_otd_snapshot` | S6 / W1-07 |
| M-040 | `cdm_tenant_health` | S8 |
| M-041 | `cdm_supplier_score` | S10 |
| M-042 | `cdm_sop_report` | S11 |
| M-043 | Odoo config versioning | W1-03 |

---

## Program gates (R2 release)

| Gate | Criteria | Status |
|------|----------|--------|
| G-R2-01 | `release2-smoke.ps1` PASS | PASS (15/15, 2026-07-10) |
| G-R2-02 | Copilot live data tools (S2) | âœ… |
| G-R2-03 | Wave 1 complete (W1-03â€“08) | âœ… eng (Odoo staging = PH1-02) |
| G-R2-04 | Arabic 8+ native QA (S5) | ðŸ”„ eng âœ…, native sign-off â¬œ |
| G-R2-05 | `run-release2-demo.ps1` extended PASS | âœ… PASS (7/7) 2026-07-10 |
| G-R2-TAG | Tag `v9.1.0-r2` | â¬œ HOLD â€” Arabic sign-off; existing tag from prior cut |

---

*Tasks v1.0 â€” Phase 2 sprint backlog*
