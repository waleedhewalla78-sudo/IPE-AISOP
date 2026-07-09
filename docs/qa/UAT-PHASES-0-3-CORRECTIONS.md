# UAT Phases 0–3 — Program Review Corrections

**Source document**: `IPE-UAT-Phases-0-3.docx` v1.0 (July 2026)  
**Applied**: 2026-07-10  
**Commits**: `43d55b1` (W1-02) through closure pass on `master`

This companion file records corrections to the UAT doc where the compiled `.docx`
does not yet reflect actual program state. Apply these edits when regenerating the UAT document.

---

## Correction 1 — Phase 0 UAT sign-off §8.1 (working tree)

**Was**: Repo clean criterion stated working tree clean at tag time.

**Now**:

> Repo clean: ~~Clean~~ **Clean after W1-02 commit (`43d55b1`).** Working tree was
> dirty with W1-02 Copilot smoke artifacts during the 2026-07-09 closure session;
> resolved in the 2026-07-10 final closure pass.

**Current state**: `git status` → working tree clean after UAT corrections commit.

---

## Correction 2 — Phase 2 UAT §5 (W1-01 / W1-02 ahead of schedule)

Add callout before or after §5.2.1 (Copilot R1 Navigation):

> **Schedule note**: W1-01 (Copilot R1 sidebar nav + i18n) and W1-02 (Copilot smoke
> tests) were completed in the Phase 0 → Wave 1 transition, ahead of the Phase 2
> UAT schedule in this document. This is intentional — Copilot nav unhide was pulled
> forward per Spec 017 Wave 1 task ordering. Phase 2 UAT execution for Copilot
> features will validate against these already-delivered components.
>
> Evidence: `apps/web/src/components/layout/Sidebar.tsx`, `docs/qa/copilot-r1-smoke.txt` (12/12).

---

## Correction 3 — Phase 0 UAT §3.2 (Gate 11 step numbering)

Add note after the Gate 11 results table:

> **Authoritative evidence**: Gate 11 step numbering and results are sourced from
> `ipe/docs/demo-data/gate11-k8s-demo.txt` (integration demo script output from
> `scripts/k8s/verify-gate11.ps1`). The step table in this UAT document uses a
> condensed numbering for readability; refer to the evidence file for canonical
> step IDs and timestamps (2026-07-09 11:49:58, 12/14 PASS).

**Canonical steps (evidence file)**:

| Step | Result |
|------|--------|
| 1–9.5 | PASS (login through MDR gate) |
| 10–11 | FAIL (OR-Tools timeout — closed #27 infra) |
| 12–13 | PASS (OTD, ROI) |

---

## Phase 0 UAT verdict (updated)

| Criterion | Status |
|-----------|--------|
| Cluster 8/8 stable at Gate 11 run | ✅ |
| Gate 11 ≥12/14 with evidence | ✅ |
| OQ-9 waiver + §6 sign-off | ✅ |
| Migration 038 both envs | ✅ |
| Sprint 7 emitters 20/20 | ✅ |
| Tag `v9.4.0-p3` pushed | ✅ |
| W1-02 smoke 12/12 | ✅ |
| Repo clean | ✅ |

**Verdict**: **PASS** (was CONDITIONAL PASS pending W1-02 and §6).

---

*Companion to IPE-UAT-Phases-0-3.docx — maintain in repo until docx is regenerated.*
