# Implementation Plan: IPE First Release Plan (017)

**Version**: 3.0 | **Date**: 2026-07-10  
**Constitution**: v1.2.4  
**Stack**: Python 3.12 · FastAPI · SQLAlchemy · PostgreSQL 16 RLS · React 18 · Kong/nginx · Kafka (optional) · kind/Helm

---

## 1. Architecture (current)

```
[Odoo 19] ←XML-RPC→ [connector] → [PostgreSQL CDM + RLS]
                              ↓
[dpe-svc] ←→ [fea-svc] ←→ [cap-svc] ←→ [mat-svc] ←→ [res-svc]
     ↓              ↓
[web-ui release1]  [nlp-svc Copilot — R1 sidebar exposed]
```

**R1 deploy set**: db, redis, dpe, fea, cap, mat, connector, res, web-ui (+ ingress). Kong optional in kind (`values-dev.yaml`).

---

## 2. Phase 0 — COMPLETE

Evidence: tag `v9.4.0-p3`, `GATE-RESULTS-PHASE3.md`, `gate11-oq9-waiver.md`.

```powershell
# Verification (regression)
cd ipe
.\scripts\wave1\verify-copilot-r1-smoke.ps1
uv run pytest services/shared/tests/test_activity_eib.py -q
kubectl get pods -n ipe  # restabilize if needed
```

---

## 3. Wave 1 — IN PROGRESS (next: W1-03)

### 3.1 W1-03 Odoo Config v2 schema (dpe-svc or connector)

| Layer | Work |
|-------|------|
| API | `POST/GET /api/v1/admin/odoo-config` Pydantic v2 schema |
| DB | Alembic migration: config versioning table + RLS |
| Validation | JSON Schema for field mappings |
| Tests | Contract tests; invalid config → 422 |

### 3.2 W1-04 Connection test

| Layer | Work |
|-------|------|
| API | `POST .../odoo-config/test-connection` timeout 5s |
| Tests | Mock Odoo XML-RPC; success <5s SLA |

### 3.3 W1-05 Multi-entity + versioning

| Layer | Work |
|-------|------|
| API | Multiple Odoo instances per tenant; rollback |
| Tests | Version conflict; backward compat v1 configs |

### 3.4 W1-06 React UI

| Layer | Work |
|-------|------|
| UI | Admin tab under Platform hub; test-and-save |
| i18n | en + ar (NFR-017-04) |

### 3.5 W1-07–08 OTD dashboard

| Layer | Work |
|-------|------|
| Backend | Extend dpe-svc: aggregation consumer + REST 5 KPIs |
| Frontend | Recharts cards; filters supplier/line/region |
| Tests | RLS isolation Tenant A ≠ Tenant B |

---

## 4. Phase 1 parallel track (commercial)

Not engineering-gated on Wave 1, but **blocks UAT**:

| Item | Owner | Deliverable |
|------|-------|-------------|
| SOW | Legal/CEO | Signed contract |
| Staging | Customer IT | Odoo staging creds |
| FR-R1-05 | Engineering | stock.quant → cdm_inventory |
| FR-R1-16 | Engineering | OTD baseline migration + API |
| Arabic QA | Native speaker | Sign-off checklist |

---

## 5. Wave 2 plan (gated on Wave 1 + customer #2 signal)

| Service | Approach | Strategy note |
|---------|----------|---------------|
| mto-svc | Tenant provision API | Pull earlier (Sprint 15–17) |
| scn-svc | Scenario CRUD/compare | Build |
| dms-svc | **Simplified** exponential smoothing | Not full Prophet initially |
| pde-svc | Defer or minimal XGBoost | After 12mo customer data |

**CUT**: SAP B1 connector.

---

## 6. Wave 3 plan

- NL Schedule: nlp-svc intent + cap-svc preview/execute
- Supplier comms: `com-svc` SMTP + rule engine

---

## 7. Verification gates

| Wave | Gate | Status |
|------|------|--------|
| 0 | G11 ≥12/14 + OQ-9 + tag | ✅ |
| 1 | Copilot 12/12; Odoo v2 contracts; OTD RLS | 🔄 2/3 |
| 2 | Tenant E2E; forecast MAPE | ⬜ |
| 3 | NL >90%; email <60s | ⬜ |
| PH1 | Zero P0 UAT; OTD baseline | ⬜ |

---

## 8. Tech debt / ops

| Item | Action |
|------|--------|
| kind CrashLoopBackOff | Restabilize; optional CPU bump (#27 advisory) |
| 6 unpushed commits | Push master |
| feature.json stale | Updated 2026-07-10 |
| READINESS.md v8 | Update or supersede with Spec 017 rollup |

---

*Plan v3.0 — `/speckit.plan` 2026-07-10*
