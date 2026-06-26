# IPE v7.0.0 Release Checklist

**Date:** 2026-06-26  
**Target tag:** v7.0.0

---

## Quality Gates

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Speckit built | 162/162 | 162/162 | ✅ |
| Speckit readiness | 100/100 | 100/100 | ✅ |
| Audit score | 100/100 | 100/100 | ✅ (see audit-final-score-v7.md) |
| Coverage | ≥75% per service | ~63% avg | ⚠️ Partial — 60% gate met on core |
| Demo | 20/20 | 20/20 (v6.1.0) | ✅ Re-run P11 required |
| Chaos | 6/6 | 6/6 (v6.1.0) | ✅ Re-run P11 required |
| Documentation | P5-04 complete | 18/20 items | ✅ P9 complete |
| FR-P | 14/14 or ADR | 13/14 + ADR-001 | ✅ Deferred |
| Secret scan | Clean | Clean | ✅ |
| Stack healthy | docker compose up | Pending P11 | ⬜ |
| CHANGELOG | v1.0.0–v7.0.0 | ✅ | ✅ |
| Git remote | Configured + pushed | Not configured | ⬜ P12 |

---

## Commits (this completion track)

| Phase | Commit | Status |
|-------|--------|--------|
| P5 | `f4f711a` gap analysis | ✅ |
| P6 | T049–T053 speckit 162/162 | ✅ |
| P10 | Keycloak ADR | Pending commit |
| P9 | Documentation suite | Pending commit |
| P7 | Audit + security sweep | Pending commit |
| P8 | Coverage tests | Pending commit |
| P11 | Final regression + tag | ⬜ |

---

## Pre-Tag Actions

- [ ] Run `python scripts/run_demo.py --all --evidence docs/final-regression-demo.txt`
- [ ] Run chaos C1–C6 with evidence
- [ ] Run Speckit verification
- [ ] Configure git remote (P12)
- [ ] `git tag -a v7.0.0`

---

## Known Limitations (v7.0.0)

- Keycloak live IdP deferred to v8.0.0 (ADR-001)
- Coverage 75% target — in progress (~63% average)
- Legacy RLS migrations 002–012 — POST-C3 backlog
