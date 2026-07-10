# Tasks: IPE First Release Plan (017)

**Version**: 1.1 | **Date**: 2026-07-10

---

## Phase 1 — Star Trans UAT (commercial track)

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| PH1-01 | Signed SOW | P0 | ⬜ | Commercial blocker |
| PH1-02 | Odoo staging access | P0 | ⬜ | Commercial blocker |
| PH1-03 | FR-R1-05 stock.quant sync | P0 | ⬜ | R1.1 ~2–3 days |
| PH1-04 | FR-R1-16 OTD baseline API | P0 | ⬜ | Overlaps W1-07 |
| PH1-05 | Arabic native speaker QA | P0 | ⬜ | RTL sign-off |
| PH1-06 | Phase 1 UAT execution | P0 | ⬜ | Sprint 5 gate |
| PH1-07 | Production go-live `v9.0.0-r1` | P0 | ⬜ | Sprint 6 gate |

---

## Phase 0 — Close v9.4.0-p3

| ID | Task | Priority | Status | GitHub |
|----|------|----------|--------|--------|
| P0-01 | Cluster stabilize (HPA off, scale=1) | P0 | ✅ | — |
| P0-02 | Gate 11 remediation (steps 10–11 OR-Tools) | P0 | ✅ 12/14 (closed #27 infra) | [#27](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/27) |
| P0-03 | OQ-9 waiver or 14/14 decision | P0 | ✅ | [#28](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/28) — `docs/demo-data/gate11-oq9-waiver.md` §6 |
| P0-04 | T717 connector activity emitter | P0 | ✅ | — |
| P0-05 | T718 cap-svc activity emitter | P0 | ✅ | — |
| P0-06 | T719 res-svc activity emitter | P0 | ✅ | — |
| P0-07 | T730 migration 038 (compose + K8s) | P0 | ✅ | [#29](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/29) — alembic head 038 |
| P0-08 | Tag `v9.4.0-p3` + update GATE-RESULTS | P0 | ✅ | [#18](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/18) — tag `v9.4.0-p3` |

## Wave 1 — Foundation (Weeks 2–5)

| ID | Task | Priority | Status | GitHub |
|----|------|----------|--------|--------|
| W1-01 | Copilot R1 sidebar nav + i18n | P0 | ✅ | — |
| W1-02 | Copilot smoke test (auth + route) | P1 | ✅ | [#30](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/30) — `docs/qa/copilot-r1-smoke.txt` 12/12 |
| W1-03 | Odoo Config v2 — schema + validation API | P0 | ✅ | [#31](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/31) — migration 043, connector API |
| W1-04 | Odoo Config v2 — connection test endpoint | P0 | ✅ | [#32](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/32) — 5s timeout |
| W1-05 | Odoo Config v2 — multi-entity + versioning | P1 | ✅ | [#33](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/33) — rollback + v1 bootstrap |
| W1-06 | Odoo Config v2 — React UI | P1 | ✅ | [#34](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/34) — Platform hub, en+ar |
| W1-07 | OTD dashboard — aggregation service | P0 | ✅ | [#35](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/35) |
| W1-08 | OTD dashboard — React 5 KPI cards | P0 | ✅ | [#36](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/36) |

## Wave 2 — Intelligence (Weeks 6–11)

| ID | Task | Priority | Status | GitHub |
|----|------|----------|--------|--------|
| W2-01 | Multi-tenant ops — tenant provision API | P0 | ⬜ | [#37](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/37) |
| W2-02 | Multi-tenant ops — quotas + metering | P1 | ⬜ | [#38](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/38) |
| W2-03 | Scenario workbench — CRUD + compare API | P0 | ⬜ | [#39](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/39) |
| W2-04 | Scenario workbench — promotion workflow UI | P1 | ⬜ | [#40](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/40) |
| W2-05 | Demand sensing — Prophet + SES service | P1 | ⬜ | [#41](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/41) |
| W2-06 | Predictive delay — XGBoost + SHAP gRPC | P1 | ⬜ | [#42](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/42) |

## Wave 3 — Automation (Weeks 12–15)

| ID | Task | Priority | Status | GitHub |
|----|------|----------|--------|--------|
| W3-01 | NL schedule change — intent classifier | P1 | ⬜ | [#43](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/43) |
| W3-02 | NL schedule change — preview + execute | P1 | ⬜ | [#44](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/44) |
| W3-03 | Supplier comms — rule engine + templates | P1 | ⬜ | [#45](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/45) |
| W3-04 | Supplier comms — email delivery + audit | P1 | ⬜ | [#46](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/46) |

## Carry-over (016/015)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T731 | Activity API integration tests | P1 | ⬜ |
| T732 | mat-svc in release1 compose (OQ-8) | P1 | ⬜ |
| T720–T722 | Sprint 7 Tier 2 AI stretch | P2 | ⬜ deferred |

## Converge carry-over (2026-07-10)

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| C-08 | Push 6 commits to origin | P0 | ⬜ | `ad494e0` ahead of tag |
| C-09 | Restabilize kind cluster | P0 | ⬜ | HPA delete + scale=1 |
| C-10 | Update `wave1-readiness.md` | P2 | ✅ | 2026-07-10 |
| C-11 | Regenerate UAT docx from corrections | P2 | ⬜ | `UAT-PHASES-0-3-CORRECTIONS.md` |
| C-12 | OQ-9 stakeholder names on waiver §6 | P2 | ⬜ | #28 |
| C-13 | T731 activity API integration tests | P1 | ⬜ | — |
| C-14 | T732 mat-svc release1 compose | P1 | ⬜ | OQ-8 |
| C-15 | FR-R1-05 stock.quant (Phase 1) | P0 | ⬜ | overlaps PH1-03 |
| C-16 | FR-R1-16 OTD baseline API (Phase 1) | P0 | ⬜ | overlaps W1-07 |

---

*Tasks v1.2 — `/speckit.tasks` 2026-07-10*
