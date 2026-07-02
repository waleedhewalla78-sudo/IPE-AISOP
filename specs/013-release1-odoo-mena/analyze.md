# Cross-Artifact Analysis: 013-release1-odoo-mena

**Version**: 2.0  
**Date**: 2026-06-29  
**Analyst**: Speckit pipeline (post-implementation refresh)  
**Overall readiness**: **78/100** (↑ from 0% at spec start)

---

## 1. Executive summary

Release 1 **engineering is largely complete** for the Odoo → Control Tower → Resolution → write-back loop. The project is **blocked on customer-side inputs** (Odoo staging access, SOW, field mapping workshop) and **three P0 engineering gaps** (routing/BOM lines sync, post-sync rescore, Arabic on Resolution/Login).

The **strategic assessment** remains valid: v8.2.0 is demo-ready; 013 closes the customer gap but has **not been validated on live Odoo**. Principle VII (Customer-First Release Slicing) should prevent any v8.3 platform work until T071 UAT sign-off.

---

## 2. Readiness scorecard

| Dimension | Score | Weight | Weighted | Notes |
|-----------|-------|--------|----------|-------|
| Spec completeness | 95 | 10% | 9.5 | spec.md v2.0 covers gaps + roadmap |
| Code — connector/sync | 85 | 20% | 17.0 | Missing routing/BOM lines |
| Code — fea/cap integration | 80 | 15% | 12.0 | Post-sync rescore missing |
| Code — web/i18n | 70 | 10% | 7.0 | Resolution/Login partial |
| Tests (unit) | 85 | 10% | 8.5 | Mapper + sync mocks pass |
| Tests (integration/live) | 30 | 10% | 3.0 | T025–T026 not run |
| Deploy/ops | 85 | 10% | 8.5 | Compose + scripts ready |
| Business artifacts | 75 | 10% | 7.5 | Playbooks done; SOW pending |
| UAT / customer validation | 0 | 5% | 0.0 | **Blocker** |
| **Total** | | | **78.0** | |

---

## 3. Cross-artifact consistency matrix

| Topic | constitution.md | spec.md | clarify.md | plan.md | tasks.md | Code | Consistent? |
|-------|-----------------|---------|------------|---------|----------|------|-------------|
| Customer = Star Trans | VII | §1 | OQ-1 ✅ | ✅ | T000 | overlay | ✅ |
| Odoo 17 | VII | §1 | OQ-3 ✅ | ✅ | T012+ | mapper | ✅ |
| 8-service release1 | VII | §2.2 | OQ-7 ✅ | ✅ | T032 | compose | ✅ |
| BOM + routing sync | FR in spec | FR-R1-02 🟡 | OQ-12 | Phase 1 | T080 ⬜ | header only | ⚠️ **Gap** |
| Arabic MVP | — | US-13–15 | OQ-9 | Phase 3 | T040–048 | partial | ⚠️ **Gap** |
| Live Odoo UAT | VII | §3.1 | OQ-11 | Phase 4 | T025–026 | — | ⚠️ **Blocked** |
| Demo overlay ≠ prod | VII | §4.3 | OQ-6 ✅ | ✅ | — | seed SQL | ✅ |
| fea-svc in compose | — | §2.2 | — | ✅ | T032 | yml | ✅ |
| Direct write-back | spec FR-R1-15 | ✅ | OQ-10 ✅ | ✅ | T030 | erp_direct | ✅ |
| Readiness 78/100 | feature.json | §2.2 | — | — | header | — | ✅ |

**Inconsistencies resolved in this refresh:** Previous analyze.md stated MO ingest ❌ — now ✅ at code level, ⬜ at UAT level.

---

## 4. Requirements coverage

### 4.1 User stories (18 total)

| Status | Count | IDs |
|--------|-------|-----|
| ✅ Code complete | 11 | US-01,03,04,05,06,07,08,09,10,17,18 |
| 🟡 Partial | 5 | US-02,11,13,14,15 |
| ⬜ Not validated / not built | 2 | US-12,16 (16 = manual T037) |

**Coverage:** 89% code path · 44% UAT validated

### 4.2 Functional requirements (26 total)

| Status | Count |
|--------|-------|
| ✅ | 18 |
| 🟡 | 3 (FR-R1-02, 19, 20 partial UI) |
| ⬜ | 5 (FR-R1-05, 14 auto, 16, 12 metric, conflict UI polish) |

**FR compliance (code):** 69% full · 12% partial · 19% deferred

---

## 5. Whole project status

### 5.1 Repository layers

```text
┌─────────────────────────────────────────────────────────────────┐
│  SALES / DEMO (v8.2.0)                    Status: COMPLETE      │
│  22 services · Star Trans overlay · 32 checkpoints              │
├─────────────────────────────────────────────────────────────────┤
│  RELEASE 1 (013)                          Status: 78% CODE    │
│  8 services · Odoo sync · Arabic MVP · playbooks                │
│  BLOCKER: live Odoo UAT + SOW + routing sync                    │
├─────────────────────────────────────────────────────────────────┤
│  PLATFORM BACKLOG (v8.3+)                 Status: FROZEN         │
│  Copilot · scenarios · supply network · SSO                     │
│  Per constitution VII — no work until T071                      │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Service map (release1 compose)

| Service | Role | R1 status |
|---------|------|-----------|
| db | PostgreSQL + CDM | ✅ Migration 036 |
| redis | Cache/queue | ✅ |
| kong | API gateway | ✅ release1 routes |
| dpe-svc | Resolution, Control Tower API | ✅ |
| fea-svc | Feasibility scoring | ✅ queue + skip flags |
| cap-svc | Scheduling + Odoo write-back | ✅ direct mode |
| connector | Odoo sync engine | 🟡 routing gap |
| web-ui | React frontend | 🟡 host-only deploy |

### 5.3 Test inventory

| Suite | Count | R1 relevance |
|-------|-------|--------------|
| Platform total | 870+ | Baseline green |
| test_odoo_mapper.py | 10 | ✅ |
| test_odoo_sync_mo.py | 2 | ✅ mocked |
| test_r1_sync_models.py | — | ✅ |
| test_r1_sync_tables_rls.py | — | ✅ (with TEST_DB_USER=ipe) |
| Live Odoo integration | 0 | ⬜ T025–T026 |
| release1-smoke.ps1 | manual | ⬜ T036 CI |

### 5.4 Documentation coverage

| Doc | Status | Linked from |
|-----|--------|-------------|
| R1-IMPLEMENTATION-PLAYBOOK | ✅ | spec §10 |
| R1-SUPPORT-RUNBOOK | ✅ | US-17 |
| ODOO-CONNECTOR-INSTALL | ✅ | FR-R1-11 |
| ODOO-FIELD-MAPPING-WORKSHEET | ✅ Template | OQ-11 |
| PRD v8.2.0 | ✅ | Platform reference |
| PRD R1 addendum | ⬜ T067 | — |
| PRODUCT-STATUS | ⬜ T066 | — |

---

## 6. Risk register (updated)

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| RK-1 | Star Trans custom Odoo fields break mapper | High | High | Field mapping workshop (OQ-11) |
| RK-2 | All MOs unscorable (no routing) | High | High | T080 before UAT |
| RK-3 | Customer IT delays staging access | Medium | Critical | Escalate week 1; parallel T004 |
| RK-4 | Arabic QA fails with native users | Medium | Medium | Native speaker review pre-UAT |
| RK-5 | 8GB VM under memory pressure | Low | Medium | T037 + compose tuning |
| RK-6 | Plaintext Odoo creds in DB | Medium | High | T081 vault before prod |
| RK-7 | Scope creep (Copilot, v8.3) | Medium | High | Constitution VII enforcement |

---

## 7. Assessment alignment (external review)

| Assessment claim | Current state | Verdict |
|------------------|---------------|---------|
| Demo-ready, not customer-ready | 78% code, 0% UAT | **Still true until T071** |
| Odoo connector IS the product | Sync engine built | **Agree — routing completes it** |
| 22 microservices too heavy | release1 = 8 services | **Addressed for R1** |
| Arabic required | MVP on Control Tower | **Partial — finish US-14/15** |
| Excel+Odoo is competition | Positioning in spec | **Locked** |
| Feasibility-first sell | fea-svc + queue | **Ready for demo with seed** |

---

## 8. Recommended next actions (priority order)

1. **T003** — Obtain Odoo staging credentials (customer IT)
2. **T002** — Sign SOW (commercial)
3. **T080** — Routing + BOM line sync (engineering P0)
4. **T082** — Post-sync rescore hook (engineering P0)
5. **T084** — Resolution + Login i18n (engineering P0)
6. **Field mapping workshop** — Complete worksheet (customer + eng)
7. **T025–T026** — Live Odoo integration tests
8. **T071** — UAT sign-off → **T073** tag `v9.0.0-r1`

---

## 9. Artifact freshness

| File | Version | Last updated | Sync status |
|------|---------|--------------|-------------|
| spec.md | 2.0 | 2026-06-29 | ✅ This refresh |
| clarify.md | 2.0 | 2026-06-29 | ✅ |
| analyze.md | 2.0 | 2026-06-29 | ✅ |
| plan.md | 2.0 | 2026-06-29 | Pending |
| tasks.md | 2.0 | 2026-06-29 | Pending |
| feature.json | — | Update readiness 78 | Pending |
| constitution.md | 1.1.0 | Stable | ✅ |

---

## 10. Conclusion

The **013 feature set is internally consistent** across spec, code, and deploy artifacts for the **happy path** (standard Odoo 17 MOs with existing seed routings). **External consistency with customer reality is unproven** until live sync runs. The critical path is **business unblock (T002, T003) + engineering P0 gaps (T080, T082, T084) + UAT (T071)**. No new platform features should enter scope before sign-off.
