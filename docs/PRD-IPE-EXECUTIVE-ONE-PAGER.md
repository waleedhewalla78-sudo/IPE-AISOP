# IPE — Executive One-Pager

**Intelligent Planning Engine · As-Is · June 2026**

| | |
|---|---|
| **Product version** | v8.2.0 (full platform) · Release 1 targeting v9.0.0-r1 |
| **Status** | Staging/demo ready (32/32 checkpoints) · Star Trans Odoo UAT in progress |
| **Full PRD** | [PRD-IPE-COMPREHENSIVE-AS-IS.md](./PRD-IPE-COMPREHENSIVE-AS-IS.md) |

---

## What IPE Is

IPE is an **AI-assisted manufacturing planning platform** that tells planners **which orders are at risk before the shift starts**, offers **structured resolution options**, and publishes **finite-capacity schedules** — connected to ERP master data instead of parallel spreadsheets.

**Default posture:** AI runs in **shadow mode**; humans approve every schedule change.

---

## Who It Serves

| Buyer / user | Job to be done |
|--------------|----------------|
| **CEO / Ops Director** (Release 1) | Replace Excel + Odoo firefighting with feasibility-first visibility |
| **Production Planner** | Triage MOs, resolve constraints, approve schedules |
| **Plant Manager** | Authorize overtime, expedites, schedule releases |
| **Executive** | OTD, delay cost, disruption exposure in one session |

**Reference customer:** Star Trans — electrical transformers (Egypt / MENA).

---

## Two Deployment Profiles

| | **Full platform (v8.2.0)** | **Release 1 (customer)** |
|---|---|---|
| **Purpose** | Sales demos, enterprise evaluation | Star Trans go-live |
| **Services** | 22 microservices | **8** (fits 8 GB VM) |
| **UI** | 6 hubs — Planning, Command, Supply, AI, Shop Floor, Platform | Planning (3 tabs) + Command + Admin |
| **ERP** | Demo seed + Odoo sync path | **Live Odoo sync** (15-min + manual) |
| **AI Copilot** | ✅ | Hidden (R2) |
| **Validation** | **32/32** demo checkpoints | UAT pending customer sign-off |

---

## Core Workflow (Release 1)

```
Odoo ERP  →  sync  →  Control Tower (risk queue + scores)
                              ↓
                    Resolution Center (scenarios)
                              ↓
                    Schedule (OR-Tools)  →  approve  →  write-back to Odoo
```

**Locally validated:** 2 Star Trans MOs synced from Odoo 19; feasibility scores 82.5; auto-rescore after sync.

---

## Business Outcomes & Metrics

| Goal | Target | Status |
|------|--------|--------|
| Faster MO triage vs spreadsheet | ≥30% reduction | Qualitative demo; formal baseline TBD |
| Feasibility before commitment | Score every syncable MO | ✅ Release 1 path working |
| Structured disruption response | ≥3 scenarios per at-risk MO | ✅ Demo tenant (8+ scenarios) |
| Closed-loop schedule persist | Survives refresh + ERP write-back | ✅ Implemented |
| Demo / engineering quality | 32/32 checkpoints, 870+ tests | ✅ Achieved |
| Customer UAT (Star Trans) | Signed acceptance | ⬜ Blocked on SOW + customer Odoo access |

---

## Competitive Position

| Compete with | Why IPE wins | Where IPE is honest |
|--------------|--------------|---------------------|
| **Excel + Odoo MRP** (R1) | Feasibility queue, scenarios, OR-Tools schedule in one UI | Not a full ERP replacement |
| **Kinaxis / SAP IBP** (enterprise demo) | Faster PoC, integrated hubs, MENA delivery story | No live SAP connector; no multi-site benchmarks yet |

**Release 1 pricing signal:** $18K–30K/yr + $12K–25K implementation *(commercial confirmation pending)*.

---

## Product Evolution (One Line)

**v1.0.0 (V5 convergence)** → **v6.0 AI-first** → **v7 hubs + LLM** → **v8.2 SAP-gap streams (32/32)** → **Release 1 Odoo live (in progress)**

*Note: “V5.0” product scope shipped as git tag v1.0.0.*

---

## Top Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Customer UAT delay | Local Odoo validation complete; parallel second prospect |
| Odoo field/customization breaks sync | Data quality flags + field mapping worksheet |
| Security (Odoo creds in DB) | R1.1 vault encryption on roadmap |
| Over-selling vs Kinaxis | R1 pitch: feasibility-first, not suite parity |

---

## Decisions Needed from Leadership

1. **Canonical Odoo version** for Release 1 docs — 17 (spec) vs 19 (local validation)?
2. **Commercial pricing** confirmation for Star Trans SOW
3. **UI role-based access** — implement before enterprise deals?
4. **Tag v8.2.0** in git and complete CHANGELOG

---

## Key Links

| Document | Purpose |
|----------|---------|
| [Comprehensive PRD](./PRD-IPE-COMPREHENSIVE-AS-IS.md) | Full as-is specification (20 sections) |
| [Product Status](./PRODUCT-STATUS.md) | Feature matrix & test counts |
| [Readiness](../READINESS.md) | Deployment readiness score |
| [Release 1 spec](../specs/013-release1-odoo-mena/spec.md) | Star Trans scope & gaps |
| [Odoo setup](./integration/ODOO-LOCAL-SETUP.md) | Integration runbook |

---

*IPE — Intelligent Planning Engine · AISOP · 2026*
