# Implementation Plan: Sprint 7 Ecosystem Cohesion (016)

**Version**: 2.0 | **Date**: 2026-07-07  
**Tech stack**: Python 3.12 · FastAPI · SQLAlchemy async · PostgreSQL 16 RLS · React 18 · Kafka (optional) · Kong gateway

---

## Phase A — Infrastructure ✅

| Task | Deliverable | Status |
|------|-------------|--------|
| T701 | Migration `038_sprint7_activity_events` | ✅ |
| T702 | `ipe_shared/events/eib.py` — ActivityEvent normalizer | ✅ |
| T703 | EIB topic constants + `ipe.activity.unified` | ✅ |
| T704 | `scripts/sprint7/audit-event-streams.ps1` | ✅ |

## Phase B — Tier 1 APIs & UI ✅

| Task | Deliverable | Status |
|------|-------------|--------|
| T710 | `GET /api/v1/activity/feed` | ✅ |
| T711 | `POST /api/v1/activity/events` | ✅ |
| T712 | EIB Kafka consumer in dpe-svc | ✅ |
| T713 | `GET /api/v1/dashboard/unified` | ✅ |
| T714 | Unified Workspace page (`/workspace`) | ✅ |

## Phase C — R1 integration wiring 🔄

| Task | Deliverable | Status |
|------|-------------|--------|
| T715 | `ipe_shared/activity/emit.py` — `record_from_kafka_topic` | ✅ |
| T716 | fea-svc: activity on feasibility scored | ✅ |
| T717 | connector: activity on sync completed | ⬜ |
| T718 | cap-svc: activity on schedule created | ⬜ |
| T719 | res-svc: activity on resolution approved | ⬜ |
| T730 | Apply migration 038 on compose + K8s DB | ⬜ |

## Phase D — Program close-out (015 dependency)

| Task | Deliverable | Status |
|------|-------------|--------|
| T166-R1 | Gate 11 remediation — cap-svc OR-Tools timeout | 🔄 12/14 |
| T157 | Tag `v9.4.0-p3` after Gate 11 14/14 | ⬜ blocked |
| T732 | Reconcile mat-svc in `docker-compose.release1.yml` (OQ-8) | ⬜ |

## Phase E — Tier 2 stretch (post-tag)

| Task | Deliverable | Status |
|------|-------------|--------|
| T720 | Pattern discovery pipeline (3 types) | ⬜ |
| T721 | Anomaly alert framework | ⬜ |
| T722 | Role-based insight templates | ⬜ |

## Phase F — Tier 3 UX (optional)

| Task | Deliverable | Status |
|------|-------------|--------|
| T723 | Command palette (⌘K) | ⬜ |
| T724 | Notification triage scoring | ⬜ |

---

## Technical decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Activity store | dpe-svc + `cdm_activity_event` | Reuses dashboard router; no new service |
| Kafka-off path | `record_from_kafka_topic` in-process | Shared DB in R1 compose |
| EIB topic mapping | `ipe.{tool}.{event}` regex | Matches existing Kafka naming |
| Unified dashboard | SQL aggregates + activity COUNT | No OLAP dependency |
| Gate 11 blocker | cap-svc CPU on kind | OR-Tools exceeds ingress timeout |
| Email-PM sync | Sprint 8 | External API rate limits |

---

## Verification commands

```powershell
cd E:\AISOP\ipe

# Unit tests
uv run pytest services/shared/tests/test_activity_eib.py -q

# Event audit
.\scripts\sprint7\audit-event-streams.ps1

# Migration
uv run alembic -c migrations/alembic.ini upgrade head

# Gate 11 (when kind healthy)
.\scripts\k8s\verify-gate11.ps1 -BaseUrl "http://localhost"
```

---

## Phase 4 prep (after `v9.4.0-p3`)

Per spec 015: Stripe sandbox, tenant self-service API, developer portal (GitHub issues #25, #26). Sprint 7 Tier 2 MAY run in parallel only after OQ-9 resolved.

---

*Plan v2.0 — `/speckit.plan` 2026-07-07*
