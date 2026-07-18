# R1 Release Readiness — Phase 8 Wave 1 Snapshot

**Date**: 2026-07-18 · **Constitution**: 1.4.2 · **Spec**: 030-phase8-r1-production

## Engineering readiness

| Gate | Status |
|------|--------|
| Control Tower / Resolution / OTD (R1 core) | BUILT (prior specs) |
| Odoo connector (mock + aliases) | BUILT; live sync PH1-02 OPEN |
| Arabic eng keys (core + Phase 8 banner) | BUILT; **G-R2-04 COM OPEN** |
| Ollama degrade + amber banner | BUILT (Spec 030) |
| Role thresholds | BUILT (Spec 030) |
| Write-back dry-run safety | BUILT; live flag false (Spec 030) |
| deploy/star-trans + validate script | Artifact ready |
| Specs 022–029 Wave 1 | ENG COMPLETE |
| Spec 030 Wave 1 (8A) | ENG COMPLETE (this report) |

## Commercial / human blockers (MUST remain OPEN)

| ID | Blocker | Blocks |
|----|---------|--------|
| OQ-7 | Pricing | SOW send |
| PH1-02 | Live Odoo staging | Live sync / write-back |
| G-R2-04 | Native Arabic QA | Tag `v9.1.1-r2` |
| OQ-1 | Odoo 17 vs 19 confirm | Pre-engagement clarity |

## Tag policy

- `v9.2.0-planning` applied @ b04434d
- `v9.1.1-r2` **HOLD** until G-R2-04
- **Never** push stale `v9.1.0-r2`

## Recommendation

**Verdict: ENG READY / COM CONDITIONAL.**

Engineering Wave 1 (through Phase 8 8A) is ready for demo and customer technical review. Commercial go-live remains gated on human COM items above — do not invent sign-off. Do **not** apply `v9.1.1-r2` or `v9.3.0-r1-eng` until humans confirm; this run documents eng readiness only.
