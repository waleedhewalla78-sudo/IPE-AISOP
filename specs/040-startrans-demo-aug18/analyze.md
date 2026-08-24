# Cross-Artifact Analysis — Spec 040 + Whole Project Status

**Date:** 2026-08-14  
**Active Speckit feature:** `specs/040-startrans-demo-aug18`  
**Constitution:** `ipe/.specify/memory/constitution.md` **v1.4.7**  

---

## 1. Spec ↔ Plan ↔ Code coverage (040)

| FR | Spec | Plan WS | Code evidence (STREAM) | Status |
|----|------|---------|------------------------|--------|
| FR-040-01 Greeting | ✓ | Hygiene | STREAM-1.1 | DONE |
| FR-040-02 Widget purge | ✓ | Hygiene | STREAM-1.2 | DONE |
| FR-040-03 DateCell | ✓ | Hygiene | STREAM-1.3 | DONE |
| FR-040-04 Needs data | ✓ | Hygiene | STREAM-1.4 | DONE |
| FR-040-05 Copilot tile | ✓ | Hygiene | STREAM-1.5 | DONE |
| FR-040-06 Tokens | ✓ | IA | STREAM-3.1 | DONE |
| FR-040-07 Nav + components | ✓ | IA | STREAM-3.2–3.4 | DONE |
| FR-040-08 Role switcher | ✓ | Homes | STREAM-4.1 | DONE |
| FR-040-09 Exec/Planner Home | ✓ | Homes | STREAM-4.2–4.3 | DONE |
| FR-040-10 Gantt | ✓ | Schedule | STREAM-5.1–5.3 | DONE |
| FR-040-11 Drawer | ✓ | Drawer | STREAM-6.1–6.2 | DONE |
| FR-040-12 Terminology | ✓ | Drawer | STREAM-6.3 | DONE |
| FR-040-13 Empty states | ✓ | Drawer | STREAM-6.4 | DONE |
| FR-040-14–17 Excel path | ✓ | Excel | STREAM-2.* + template align | DONE eng |
| FR-040-18 Walkthrough/screenshots | ✓ | Ops | Docs + checklist | **PARTIAL** — boxes unchecked; PNGs missing |

**Coverage:** 17/18 FRs eng-complete; 1 FR ops-partial.

### Consistency findings

| ID | Severity | Finding | Action |
|----|----------|---------|--------|
| A1 | Med | `feature.json` previously pointed at 033a; now 040 | Updated |
| A2 | Med | Spec 012 CLOSED still documents old Excel schema | Link 040 as superseding for Aug 18 |
| A3 | Low | Early STREAM-2.2 invented sheet names; later align fixed | Prefer template file as SSOT |
| A4 | Med | `demo_*` tables skip RLS — conflicts with Principle I if mistaken for production | Document NFR-040-05; never enable for paying tenant without RLS migration |
| A5 | Low | Supervisor/Buyer share Planner Home | Clarify C6 default — OK for demo |
| A6 | High (ops) | Walkthrough not executed on warm stack | T-OPS-01 |
| A7 | High (ops) | Screenshots empty | T-OPS-02 |
| A8 | Med | Kong `/api/v1/data` needs reload | T-OPS-03 |

No FR orphaned without plan. No plan item inventing COM PASS.

---

## 2. Whole project status (detailed)

### 2.1 Program verdict

| Dimension | Status |
|-----------|--------|
| Engineering Wave 1 (022–032, 033a, 033b–f scaffolds) | **ENG READY** |
| Commercial / human | **COM CONDITIONAL** |
| Star Trans Aug 18 demo eng | **SHIPPED on branch** |
| Star Trans Aug 18 demo ops | **OPEN** (warm pass) |

### 2.2 Speckit inventory (high level)

| Spec range | Status |
|------------|--------|
| 000–011 | Historical / closed |
| **012** Star Trans foundation | **CLOSED** — seed/scripts base |
| 013–021 | R1/R2/planning closure ENG COMPLETE |
| 022–030 | Sprint/Ops/Prod ENG COMPLETE Wave 1 |
| 031–032 | Planner UX + Upload CDM ENG COMPLETE |
| **033 + 033a–f** Phase 9 | 9A scaffold COMPLETE; 9B–9F Wave 1 scaffolds; COM OPEN (T166–T168) |
| 034–036, 038–039 | Workspace/hub/persona redesign ENG (prior) |
| **040** Aug 18 demo cycle | **ACTIVE** — eng done / ops residual |

### 2.3 Phase naming (binding map excerpt)

- Platform Phase 3 (`v9.4.0-p3`) ≠ Ops Blueprint Phase 3 (Spec 024)
- Phase 9B–9F Wave 1 = soft stubs / honesty badges — not production ML/SAP/OCR

### 2.4 COM blockers (never eng-close)

| ID | Topic | Status |
|----|-------|--------|
| OQ-7 | Pricing / SOW amounts | OPEN |
| PH1-02 | Live Odoo staging | OPEN |
| G-R2-04 | Arabic native QA | OPEN |
| PH1-01 / C-01…C-08 | Commercial checklist | OPEN |
| `v9.1.1-r2` | Customer tag | HOLD |

### 2.5 Demo-critical services

| Service | Role in demo |
|---------|----------------|
| web-ui :8082 | Homes, CT, Gantt, upload UI |
| Kong :8000 | Auth + routing |
| dpe-svc | Workspace dashboard, auth |
| fea-svc | Feasibility queue |
| cap-svc | Active schedule for Gantt |
| upload-svc | Excel multipart `/data/upload` |
| mat/res | Supporting CT |

### 2.6 Constitution compliance (040)

| Principle | 040 stance |
|-----------|------------|
| I RLS | Demo tables explicitly non-prod; gap documented |
| II Auth | Upload behind Kong JWT (same as upload-svc) |
| III Tests | Parser unit tests present |
| VII Customer-first | Star Trans Excel + CT/Home first |
| X Honesty | No live Odoo/ML claims |

---

## 3. Recommendation

1. Treat **040** as the Speckit active feature through Mon 18.  
2. Execute ops tasks only until demo (no new features after Sun 17 18:00).  
3. After demo, either close 040 with evidence or spin residuals to 041.
