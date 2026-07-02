# Analyze — 014 Release 2 + Whole Project Status

**Date**: 2026-07-01  
**Feature**: `014-release2-growth`  
**Analyst**: Speckit cross-artifact analysis  
**Platform**: IPE v8.2.0 · Release 1 @ 96/100 · Tag v8.2.0

---

## 1. Executive summary

| Dimension | Score | Grade | Trend |
|-----------|-------|-------|-------|
| Engineering completeness (platform) | 92/100 | A | Stable |
| Release 1 customer readiness | 96/100 | A | ↑ (13/13 demo) |
| Commercial / SaaS readiness | 45/100 | D | Flat (POST-B) |
| Documentation coherence | 72/100 | C | Improving |
| Test coverage (services) | 88/100 | B+ | Stable (~206 test files) |
| **Overall product** | **80/100** | **B** | Demo-strong, not SaaS-ready |

**Recommendation:** Execute 014 streams A+B immediately (highest ROI, builds on shipped R1). Stream C parallel. Stream D after Star Trans UAT feedback. Defer Stream E to 015.

---

## 2. Cross-artifact consistency matrix

| Artifact | Version claim | Demo score | Active feature | Conflict? |
|----------|---------------|------------|----------------|-----------|
| `README.md` | v8.2.0 / v9.0.0-r1 | 32/32 | 013 link | — |
| `ipe/.specify/feature.json` | v8.2.0 / v9.0.0-r1 | — | 013 | ✅ Canonical |
| Root `.specify/feature.json` | v6.0.0 | 20/20 | 005/004 | ⚠️ **Stale** |
| `READINESS.md` | v8.2.0 100/100 | 32/32 | — | — |
| `SPECKIT-CHECKLIST.md` | v6.0.0 | 20/20 | 005 | ⚠️ **Stale** |
| `013/converge.md` | 96/100 | 13/13 R1 | 013 | ✅ Updated 2026-06-30 |
| `PRODUCT-STATUS.md` | v8.2.0 | 32/32 | — | — |
| `FULL-PRODUCT-STATUS-AUDIT.md` | 80/100 | 10/13→13/13 | 013 | Audit predates R1 fixes |

**Actions:**
1. Update root `.specify/feature.json` → point to 013/014
2. Refresh `SPECKIT-CHECKLIST.md` header to v8.2.0 / 32/32
3. Archive v6 demo score references in 005 analyze as historical

---

## 3. Spec coverage vs codebase (014 streams)

| FR | Spec stream | Code today | Gap |
|----|-------------|------------|-----|
| FR-R2-01 | A Auto-propose | res-svc API ✅; consumer bug ⚠️; no connector HTTP | **Implement T110** |
| FR-R2-02 | A Threshold config | Not in tenant config | **Implement T111** |
| FR-R2-03 | B Outcomes UI | APIs ✅; no page | **Implement T120** |
| FR-R2-04 | B Baseline capture | API ✅; no UI button | **Implement T121** |
| FR-R2-06 | C Copilot Lite | nlp-svc full only | **Implement T140** |
| FR-R2-08 | D Odoo chatter | Not implemented | **Implement T150** |
| FR-R2-10 | Demo script | Not exists | **Implement T160** |

---

## 4. Service maturity map (22 app services)

| Service | LOC | Tests | Kong R1 | Kong Full | R2 role |
|---------|-----|-------|---------|-----------|---------|
| dpe-svc | ~15k | 40+ | ✅ | ✅ | Outcomes API, Copilot Lite host |
| fea-svc | ~4k | 15+ | ✅ | ✅ | Rescore trigger |
| res-svc | ~2k | 5+ | ✅ | ✅ | **Stream A core** |
| cap-svc | ~12k | 36+ | ✅ | ✅ | Schedule (unchanged) |
| connector | ~4k | 9+ | ✅ | ✅ | **Stream A trigger**, Stream D |
| nlp-svc | ~8k | 20+ | ❌ | ✅ | Stream C hybrid optional |
| demand-svc | ~3k | 10+ | ❌ | ✅ | R3+ |
| mat-svc | ~5k | 15+ | ❌ | ✅ | R3 inventory Copilot |

---

## 5. Release profile coverage

| Capability | Full 32/32 | R1 13/13 | R2 target |
|------------|------------|----------|-----------|
| Control Tower | PASS | PASS | PASS |
| Resolution | PASS | PASS | PASS + auto-propose |
| Schedule | PASS | PASS | PASS |
| Outcomes | Partial (exec API) | API only | **PASS UI** |
| Copilot | SKIP | SKIP | **PASS Lite** |
| Shop floor | SKIP | SKIP | R3 |

---

## 6. Test & quality posture

| Metric | Value | Source |
|--------|-------|--------|
| Python test files (services) | ~206 | audit-metrics.json |
| Documented passing tests | 1110 | PRODUCT-STATUS |
| Release 1 integration demo | 13/13 | 2026-06-30 |
| Full demo on R1 stack | 13/32 PASS, 19 SKIP | Expected |
| TODO/FIXME in services/web | ~0 tracked | audit |
| P1 open (post-R1 fixes) | 0 bugs | RELEASE1-DEMO-STATUS |

**014 test requirements:** Unit tests for auto-propose dedupe, Outcomes API aggregation, Copilot Lite intent router, Odoo chatter mock.

---

## 7. Competitive gap analysis (updated)

| vs Competitor | R1 today | After 014 |
|---------------|----------|-----------|
| Excel + Odoo | Strong | **Stronger** (outcomes proof) |
| SAP Joule NL | Weak (hidden) | **Parity Lite** (structured) |
| Kinaxis scenarios | Partial | **Improved** (auto-propose) |
| SAP IBP S&OP | Weak | Unchanged (R3+) |

---

## 8. Findings requiring action

| ID | Severity | Finding | Action |
|----|----------|---------|--------|
| F-01 | P1 | Root feature.json stale | Update in implement T001 |
| F-02 | P0 | res-svc Kafka handler wrong mo_id field | Fix T112 |
| F-03 | P0 | No HTTP auto-propose after sync | Implement T110 |
| F-04 | P1 | No Outcomes UI for executives | Implement T120 |
| F-05 | P2 | ml-svc not in Kong | Defer — cap-svc degrades gracefully |
| F-06 | P1 | 013 commercial blockers T002/T003/T071 | Track in 013; not 014 eng |

---

## 9. Readiness projection

| Milestone | Score | Date target |
|-----------|-------|-------------|
| 014 specify–tasks complete | — | 2026-07-01 |
| 014 implement A+B | 88/100 | 2026-07-15 |
| 014 full streams A–D | 92/100 | 2026-08-01 |
| v9.1.0-r2 tag | 94/100 | After Star Trans R2 UAT |

---

## 10. Whole project status (detailed)

### Shipped ✅
- v8.2.0 platform (22 services, 274 endpoints)
- V6-R1–R5 features (margin, tariff, CPM, maintenance, chaos)
- v8 Phases 1–3 (demand, scenario, supply, order, equipment, design, procurement)
- Release 1 Odoo sync + Control Tower + Schedule + Resolution (13/13)
- Star Trans seed + MDR boost + hybrid gap analysis docs

### In progress 🟡
- Star Trans UAT (T071)
- Commercial SOW (T002)
- Release 2 specification (014 — this artifact)

### Blocked ⬜
- v9.0.0-r1 tag (needs UAT)
- Keycloak SSO (011 POST-B)
- Stripe live billing
- SAP live connector

### Technical debt
- Dual feature.json pointers (root vs ipe/)
- SPECKIT-CHECKLIST v6 references
- Kafka optional in R1 but res-svc consumer expects it
- Git dubious ownership on dev machines

---

*Generated by `/speckit.analyze` — 2026-07-01*
