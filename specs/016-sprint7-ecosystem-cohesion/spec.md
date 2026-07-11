---
status: CLOSED
closed_by: v9.4.0-p3
date: 2026-07-11
---

# Feature Specification: Sprint 7 Ecosystem Cohesion (016)

**Feature**: `016-sprint7-ecosystem-cohesion`  
**Version**: 2.0  
**Date**: 2026-07-07  
**Status**: Tier 1 complete — integration wiring + Tier 2 pending  
**Source**: `IPE-Sprint7-Enhancement-Roadmap (3).docx` · `docs/PRD-IPE-AUTHORITATIVE.md` §7  
**Depends on**: `006-module-hub-consolidation`, `015-enterprise-production-readiness` (Phase 3 gates)  
**Release target**: `v9.5.0-s7` (Sprint 7 cohesion milestone)

---

## 1. Vision

Evolve IPE from isolated tool modules into a **unified, AI-native ecosystem** where cross-tool data flows automatically, activity is visible in one timeline, and decision-makers see a single intelligent workspace.

Sprint 7 thesis: **platform cohesion** — not new standalone tools.

---

## 2. Problem statement

| Pain | Today (pre-S7) | After Tier 1 |
|------|----------------|--------------|
| Context switching | Planners open 4+ hubs for status | Single `/workspace` landing |
| No cross-tool audit trail | Events in Kafka only (or nowhere in R1) | `cdm_activity_event` timeline |
| Executive blind spots | KPIs scattered across APIs | `/dashboard/unified` aggregation |
| Integration fragility | Ad-hoc topic shapes | EIB normalizer → canonical `ActivityEvent` |

---

## 3. User personas & stories

### 3.1 Production planner (primary)

| ID | Story | Acceptance |
|----|-------|------------|
| US-S7-P01 | As a planner, I want one workspace showing at-risk MOs and recent activity so I start my shift without opening four tabs | `/workspace` loads KPIs + feed < 2s on compose |
| US-S7-P02 | As a planner, I want to see when Odoo sync completed so I know data is fresh | Activity event `connector: sync_completed` with timestamp |
| US-S7-P03 | As a planner, I want feasibility score changes in the feed so I notice regressions | `feasibility: scored` events with MO id + score |
| US-S7-P04 | As a planner, I want schedule runs logged so I can trace approvals | `capacity: schedule_created` events |

### 3.2 Operations manager

| ID | Story | Acceptance |
|----|-------|------------|
| US-S7-M01 | As a manager, I want role-aware KPIs on one dashboard | Unified API returns alerts count, at-risk MOs, last sync |
| US-S7-M02 | As a manager, I want to filter activity by tool | `GET /activity/feed?source_tool=connector` |

### 3.3 Executive / CEO

| ID | Story | Acceptance |
|----|-------|------------|
| US-S7-E01 | As an executive, I want OTD and risk summary without navigating planning hubs | Unified dashboard includes OTD baseline + risk count |
| US-S7-E02 | As an executive, I want Arabic labels on workspace (R1) | i18n keys for workspace page |

### 3.4 Platform engineer

| ID | Story | Acceptance |
|----|-------|------------|
| US-S7-X01 | As an engineer, I want an audit script proving event coverage | `audit-event-streams.ps1` exits 0 |
| US-S7-X02 | As an engineer, I want EIB normalization unit-tested | `test_activity_eib.py` PASS |
| US-S7-X03 | As an engineer, I want Kafka-off R1 to still populate activity | Direct POST or in-process `record_from_kafka_topic` |

---

## 4. Functional requirements

### Tier 1 — Table-stakes (committed)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-S7-01 | **Unified dashboard consolidation** — single API aggregates KPIs, alerts, activity, AI recommendations by role | P0 | ✅ API + UI |
| FR-S7-02 | **Cross-tool activity feed** — chronological, filterable timeline | P0 | ✅ API + UI |
| FR-S7-03 | **Ecosystem Integration Bus (EIB)** — normalize `ipe.*` topics to `ActivityEvent`; schema-registry-ready | P0 | ✅ normalizer + consumer |
| FR-S7-04 | **R1 tool emitters** — connector, fea, cap, res emit activity on key actions | P0 | 🔄 fea wired; others pending |
| FR-S7-05 | **RLS on activity table** — tenant isolation on `cdm_activity_event` | P0 | ✅ migration 038 |

### Tier 2 — AI differentiators (stretch)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-S7-10 | Pattern discovery engine — 3 pattern types on activity stream | P2 | ⬜ |
| FR-S7-11 | Proactive anomaly alerting — 3 anomaly types with role routing | P2 | ⬜ |
| FR-S7-12 | Role-based insight delivery — exec/ops/team templates | P2 | ⬜ |

### Tier 3 — UX unification (stretch)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-S7-20 | Contextual command palette — keyboard search across tools | P3 | ⬜ |
| FR-S7-21 | Intelligent notification triage — AI priority scoring | P3 | ⬜ |

### Deferred (Sprint 8+)

- Real-time email ↔ project management sync (Microsoft Graph / Google Workspace)
- Integration marketplace API

---

## 5. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-S7-01 | Activity feed API p95 latency | < 500ms @ 50 events |
| NFR-S7-02 | Idempotent ingest | Duplicate `idempotency_key` ignored |
| NFR-S7-03 | Tenant isolation | RLS + JWT tenant claim |
| NFR-S7-04 | Kafka-off compatibility | Works with `IPE_KAFKA_ENABLED=false` |
| NFR-S7-05 | Constitution compliance | Principles I, III, IV, V |

---

## 6. Architecture

```
Tool services → ipe.{tool}.{event} (Kafka) → EIB normalizer → cdm_activity_event
                                              ↘ ipe.activity.unified (republish)
Unified dashboard API ← activity store + existing dashboard endpoints
         ↓
   /workspace (React)
```

**Release 1 profile**: When Kafka is disabled (`IPE_KAFKA_BOOTSTRAP_SERVERS=""`), services MAY:
1. POST to `/api/v1/activity/events`, or
2. Call `record_from_kafka_topic()` in-process when sharing DB session.

---

## 7. API contract (Tier 1)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/activity/feed` | JWT | Paginated timeline; `source_tool` filter |
| POST | `/api/v1/activity/events` | planner+ | Direct ingest |
| POST | `/api/v1/activity/ingest/kafka` | admin | EIB envelope ingest |
| GET | `/api/v1/dashboard/unified` | JWT | Role-aware KPI aggregation |

---

## 8. Data model

**Table**: `cdm_activity_event` (migration 038)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| tenant_id | UUID | RLS |
| source_tool | varchar(64) | e.g. `connector`, `feasibility` |
| event_type | varchar(128) | e.g. `sync_completed`, `scored` |
| summary | text | Human-readable line |
| severity | varchar(16) | info / warning / critical |
| occurred_at | timestamptz | Event time |
| idempotency_key | varchar(256) | Optional dedup |

---

## 9. Success metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Integration coverage | 100% R1 tools emit activity | audit script + manual checklist |
| Dashboard engagement | 60% DAU use `/workspace` | Post-launch analytics |
| AI recommendation acceptance | 40% by sprint end | Tier 2 only |
| Gate 11 (program) | 14/14 PASS | `verify-gate11.ps1` — blocks `v9.4.0-p3` |

---

## 10. Out of scope

- New microservice for activity (use dpe-svc + shared CDM)
- NEXUS Social product features
- Production SAP/D365 connectors
- Phase 4 GTM (Stripe, self-service) — tracked in spec 015

---

## 11. References

- `clarify.md` — OQ resolutions
- `analyze.md` — cross-artifact matrix
- `plan.md` — implementation phases
- `tasks.md` — actionable backlog
- `converge.md` — gap assessment

---

*Spec v2.0 — `/speckit.specify` 2026-07-07*
