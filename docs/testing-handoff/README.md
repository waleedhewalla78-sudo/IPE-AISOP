# IPE v7.0.0 — Human Testing Handoff

**Repository:** https://github.com/waleedhewalla78-sudo/IPE-AISOP  
**Tag:** `v7.0.0`  
**Date:** 2026-06-26

## Start here

| Document | Purpose |
|----------|---------|
| [QUICK-START.md](QUICK-START.md) | Clone, start stack, UI, automated smoke |
| [HUMAN-TEST-PLAN.md](HUMAN-TEST-PLAN.md) | 20 manual acceptance scenarios |
| [EVIDENCE-INDEX.md](EVIDENCE-INDEX.md) | Automated gate evidence (demo, chaos, coverage) |
| [RELEASE-NOTES-v7.0.0.md](RELEASE-NOTES-v7.0.0.md) | GitHub release notes |

## Automated gates (pre-verified)

| Gate | Result | Evidence |
|------|--------|----------|
| Demo | 20/20 | `../final-regression-demo.txt` |
| Chaos | 6/6 | `../final-regression-chaos.txt` |
| Coverage | 75%+ / service | `../coverage-report-v7.md` |
| Speckit | 162/162 | `../speckit-final-p6.txt` |
| Audit | 100/100 | `../audit-final-score-v7.md` |

## Defect reporting

Open issues at: https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues

Template: **Steps to reproduce | Expected | Actual | Severity (P1–P3)**
