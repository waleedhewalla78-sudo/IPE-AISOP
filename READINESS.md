# IPE Platform — Deployment Readiness

**Version**: v6.1.0 tagged → **v7.0.0 completion in progress**  
**Published**: 2026-06-26  
**Supersedes**: v6.0.1, v6.0.0, v1.0.0

---

## Overall Score: 100/100 (Speckit) · 100/100 (Audit doc) · ~64% avg coverage

| Metric | Value |
|--------|-------|
| **Live demo** | **20/20** (`docs/demo-run-report-wave3-live.txt`) |
| **Chaos** | **6/6** C1–C6 (`docs/chaos/chaos-summary.md`) |
| **Git** | tags **v1.0.0** … **v6.1.0**; HEAD `4aac77d` (v7 track) |
| **Coverage** | cap/mat ~68%, dpe ~67%, alert ~69%, nlp ~57%, fea ~55% |
| **Phase** | **v7.0.0** — P8 coverage + P11 regression pending |
| **FR-P** | 13/14 — FR-P-13 Keycloak deferred (ADR-001) |

| Dimension | Score | Notes |
|-----------|-------|-------|
| Product completeness | 98 | V5 loop + V6 tariff/CPM/maintenance/chaos/war-room |
| Testing | 92 | 870+ backend tests; demo 20/20; chaos 6/6 |
| Security | 82 | RBAC + RLS; JWT rotation runbook; SEC-05 closed |
| Operations | 92 | Loki/Grafana MVP; TLS + JWT runbooks |
| Documentation | 90 | Gap analyses complete; CHANGELOG pending (P9) |

See `docs/speckit-gap-analysis-v6.1.md`, `docs/audit-gap-analysis-v6.1.md`.

---

## Git Lineage (oldest → newest)

| Commit | Description | Tag |
|--------|-------------|-----|
| `4efb8de` | Release v1.0.0 | v1.0.0 |
| `a203e68` | Release v6.0.0: 20/20 live demo gate | v6.0.0 |
| `0e2055e` | v6.0.1 audit fixes live-verified | v6.0.1 |
| `097dea3` | Wave 3 W3-01–03 TLS/JWT/SEC-05 | — |
| `51f41ec` | Wave 3 W3-04 regression 20/20 + chaos 6/6 | **v6.1.0** |
| `f4f711a` | P5 gap analysis (speckit, audit, coverage, docs) | — |

---

## Phase Completion

| Phase | Scope | Status |
|-------|-------|--------|
| 0 — Git + P0 fixes | GIT-01, C-01–C-02, BUG-02–03 | ✅ Complete |
| 1 — Demo 20/20 + tag | T016–T022, T055 / v6.0.0 | ✅ Complete |
| 2 — Audit criticals | fea0705 + v6.0.1 | ✅ Complete |
| 3 — REL-PROD Wave 2 | k6, Chaos, coverage, ops | ✅ Complete |
| 4 — Wave 3 hardening | C-03 TLS, C-04 JWT, SEC-05, v6.1.0 | ✅ Complete |
| 5 — v7.0.0 completion | P5–P12 | 🔄 P8 coverage + P11 regression |
| 6+ | Keycloak (C-007), Stripe, BRD | ⬜ Future / deferred |

---

## V6.0 Deliverables (004) — Live Proven

| Phase | Exit Gate | Demo Checkpoint | Live |
|-------|-----------|-----------------|------|
| V6-R1 Activity-Based Planning | ≥8% activity-cost delta | 17 | ✅ |
| V6-R2 Tariff & Landed Cost | Shock + substitute draft | 18 | ✅ |
| V6-R3 Visual CPM | p95 cascade <2s | 19 | ✅ |
| V6-R4 Predictive Maintenance | RUL → block published | 20 | ✅ |
| V6-R5 Cost of Chaos + War Room | ≥3 chaos categories; recovery top-3 | 20 | ✅ |

---

## Risk Register (Summary)

### P0 — All closed

| ID | Issue | Status |
|----|-------|--------|
| C-01 | check-availability → rule_based_atp | ✅ |
| C-02 | Double /api/v1 CTP prefix | ✅ |
| BUG-02 | MDR fail-open | ✅ |
| BUG-03 | Approve version race | ✅ |
| C-03 | TLS internal services | ✅ W3-01 |
| C-04 | JWT rotation | ✅ W3-02 |
| SEC-05 | password_hash column | ✅ W3-03 |

### P1 — Open for v7.0.0

| ID | Issue | Status |
|----|-------|--------|
| C-007 | Keycloak live IdP (FR-P-13) | 🔴 BLOCKED |
| R-021 | Coverage 75%+ target | 🔄 P8 |
| R-001 | Legacy RLS (002–012) | POST-C3 backlog |

---

## Speckit Rollup

| Feature | Built | Total | % |
|---------|-------|-------|---|
| 002 Release gates | 62 | 62 | 100% |
| 003 Autonomous V5 | 45 | 45 | 100% |
| 004 AI-first V6 | 55 | 55 | 100% |
| **Program** | **162** | **162** | **100%** |

---

## Next Steps (v7.0.0)

1. P6 — Close Speckit T049–T051 → 162/162
2. P7 — Audit hardening → 100/100
3. P8 — Coverage 75%+
4. P9 — Documentation suite
5. P10 — Keycloak ADR or mock
6. P11 — Final regression + tag v7.0.0
