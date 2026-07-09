# Implementation Plan: IPE First Release Plan (017)

**Version**: 2.0 | **Date**: 2026-07-09  
**Stack**: Python 3.12 · FastAPI · SQLAlchemy · PostgreSQL 16 RLS · React 18 · Kong · Kafka (optional) · kind/Helm

---

## Tech stack by wave

| Layer | Choice |
|-------|--------|
| API | FastAPI + Pydantic v2 + `ipe_shared` |
| DB | PostgreSQL 16, Alembic, RLS per migration |
| Events | Kafka + Avro (full); direct activity POST (R1) |
| Auth | Keycloak OIDC (enterprise); JWT (R1 demo) |
| UI | React 18, Vite, Tailwind, Recharts (OTD) |
| ML | Prophet, statsmodels SES, XGBoost, SHAP |
| Deploy | Docker Compose (R1), Helm/kind (Phase 3) |

---

## Phase 0 (Week 1) — detail

```powershell
# Cluster
kubectl delete hpa -n ipe --all
kubectl scale deployment -n ipe dpe-svc fea-svc cap-svc connector mat-svc --replicas=1

# Gate 11
.\scripts\k8s\verify-gate11.ps1 -BaseUrl "http://localhost"

# Migration 038
uv run alembic -c migrations/alembic.ini upgrade head
.\scripts\k8s\migrate-k8s-db.ps1

# Tests
uv run pytest services/shared/tests/test_activity_eib.py -q
```

---

## Wave 1 (Weeks 2–5)

| Week | Backend | Frontend |
|------|---------|----------|
| W2 | Odoo config v2 schema + test-connection | Copilot smoke test ✅ nav done |
| W3–4 | Config versioning, multi-entity | Odoo config v2 UI |
| W2–4 | OTD aggregation consumer + REST | OTD dashboard 5 KPIs |

**New services**: extend dpe-svc for OTD (avoid new svc until Wave 2 ops split).

---

## Wave 2 (Weeks 6–11)

| Service | Port (proposed) | Depends on |
|---------|-----------------|------------|
| mto-svc | 8021 | v9.4.0-p3 tag |
| scn-svc (extend) | 8014 | existing scaffold |
| dms-svc | 8022 | Odoo config v2 data |
| pde-svc | 8023 | 12mo order history |

---

## Wave 3 (Weeks 12–15)

- NL Schedule: extend nlp-svc + cap-svc mutation API  
- Supplier comms: new `com-svc` (email SMTP, Kafka triggers)

---

## Verification gates per wave

| Wave | Gate |
|------|------|
| 0 | Gate 11 ≥12/14; migration 038; tag |
| 1 | Copilot 401 unauth; OTD RLS test; Odoo v2 contract tests |
| 2 | Tenant provision E2E; MAPE/AUC thresholds |
| 3 | NL accuracy >90%; email delivery <60s |

---

*Plan v2.0 — `/speckit.plan` 2026-07-09*
