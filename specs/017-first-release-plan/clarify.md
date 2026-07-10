# Clarification Record — Spec 017 First Release Plan

**Date**: 2026-07-10  
**Constitution**: v1.2.4

---

## Resolved (DECIDED)

| ID | Question | Resolution |
|----|----------|------------|
| CL-017-01 | Active program spec? | **Spec 017** is canonical program rollup |
| CL-017-02 | Copilot in R1 vs Principle VII? | **Dedicated sidebar** in release1; full AI hub hidden |
| CL-017-03 | Sprint 7 emitters? | T717–T719 **done**; T730 migration **applied** |
| CL-017-04 | Gate 11 acceptable score? | **12/14 + OQ-9 waiver** — tag applied |
| CL-017-05 | Wave sequencing? | Wave 1 foundation before Wave 2 ML |
| CL-017-06 | #27 OR-Tools timeout? | **CLOSED WON'T FIX** — infra, Compose 14/14 proves logic |
| CL-017-07 | W1-02 Copilot smoke? | **12/12 PASS** — Vitest 7 + nlp 401 + Playwright 4 |
| CL-017-08 | SAP B1 connector? | **CUT** per Strategy Assessment — not in task list |
| CL-017-09 | Demand sensing algorithm? | **Modify** — basic statistical forecast in Wave 2, not full Prophet/SES initially |
| CL-017-11 | NEXUS Social PRD scope? | **Out of IPE Spec 017** — separate `nexus-social/` track; PRD at `nexus-social/docs/PRD-NEXUS-AUTHORITATIVE.md` | Product |

## Open (stakeholder / commercial)

| ID | Question | Recommendation | Owner |
|----|----------|----------------|-------|
| OQ-9-NAMES | PO/Platform/QA names on waiver §6 | Fill before external audit | Stakeholder |
| OQ-1 | Odoo 17 vs 19 canonical for SOW? | Odoo 17 SOW; 19 dev OK | Commercial |
| OQ-8 | mat-svc in release1 compose? | Include — T732 carry-over | Engineering |
| PH1-SOW | Signed SOW | Escalate exec-to-exec by Sprint 4 | CEO |
| PH1-STAGING | Star Trans Odoo staging access | Remote VM + VPN fallback | Customer IT |
| PH1-AR | Arabic native speaker QA | Before Phase 1 UAT execution | QA |

## Underspecified — now clarified

| Area | Was vague | Clarification |
|------|-----------|---------------|
| Gate 11 step IDs | UAT doc vs demo script mismatch | **Authoritative**: `gate11-k8s-demo.txt` |
| Copilot schedule | Phase 2 UAT vs Wave 1 | W1-01/02 **delivered early**; Phase 2 UAT validates same components |
| Phase 0 vs Phase 1 | Overlap on Odoo config | Wave 1 W1-03–06 = engineering; Phase 1 UAT = customer validation |
| Tag vs HEAD | 6 commits post-tag | Push `ad494e0`; consider `v9.4.0-p3-p1` or move tag |

---

*Clarify v2.0 — `/speckit.clarify` 2026-07-10*
