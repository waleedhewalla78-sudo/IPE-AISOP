# Audit Gap Analysis — v6.1.0 → 100/100

**Date:** 2026-06-26  
**Baseline audit estimate:** ~95/100 (post Wave 3)  
**Original audit:** `audit/v2/11-production-readiness-scorecard.md` (42/100 raw, June 20)  
**Target:** 100/100 for v7.0.0

---

## Closed Since Original Audit (Wave 0–3)

| ID | Finding | Status | Evidence |
|----|---------|--------|----------|
| C-01 | check-availability → `rule_based_atp` | ✅ | `fea0705`, tests |
| C-02 | Double `/api/v1` CTP prefix | ✅ | Verified OK |
| C-03 | TLS internal services | ✅ | `docs/runbooks/tls-internal.md` |
| C-04 | JWT rotation undocumented | ✅ | `docs/runbooks/jwt-rotation.md` |
| BUG-02 | MDR fail-open | ✅ | 503 fail-closed |
| BUG-03 | Approve version race | ✅ | 409 + optimistic lock |
| SEC-05 | password_hash column | ✅ | Migration 028 + auth verify |
| R-01 | Coverage 40% threshold | ✅ | 60% gate; cap/mat/dpe 65–68% |
| R-08 | No log aggregation | ✅ | Loki + Grafana MVP |
| R-016 | seed password_hash | ✅ | Migration 028 + seed-data.sh |

---

## Remaining Gaps (~5 points to 100)

### AG-01 — FR-P-13 Keycloak / C-007 (2 pts)

| Field | Value |
|-------|-------|
| **Finding** | Live SAML/SCIM IdP not validated |
| **Severity** | P1 (enterprise sales) |
| **Status** | **BLOCKED** — no IdP sandbox |
| **Remediation options** | (a) Full Keycloak compose + Kong JWKS (5–7 d) · (b) Mock adapter (2 d) · (c) ADR deferral to v8 |
| **Point value** | ~2/100 audit · ~3% Speckit FR-P |
| **v7.0.0** | Accept with ADR if all else 100 |

### AG-02 — Test coverage below 75% target (2 pts)

| Field | Value |
|-------|-------|
| **Finding** | R-021 extended; services below 75% |
| **Current** | cap 68%, mat 65%, dpe 66%, nlp 56%, alert 67%, fea 55% |
| **Target** | ≥75% per service for v7.0.0 |
| **Remediation** | P8 coverage push; raise `fail_under` incrementally |
| **Point value** | ~2/100 |

### AG-03 — Legacy RLS on migrations 002–012 (1 pt)

| Field | Value |
|-------|-------|
| **Finding** | R-001 partial — 024–027 have RLS; legacy tables debt |
| **Status** | POST-C3 backlog |
| **Remediation** | Alembic policy migration or document waiver + integration test |
| **Point value** | ~1/100 |

### AG-04 — Security hardening sweep incomplete (0.5 pt)

| Field | Value |
|-------|-------|
| **Finding** | Non-root containers, secret scan, CORS prod config |
| **Status** | Partial — Kong rate limit exists; dev secrets in compose |
| **Remediation** | P7-02 hardening sweep + `docs/security-hardening-sweep.md` |
| **Point value** | ~0.5/100 |

### AG-05 — Git remote / supply chain (0.5 pt)

| Field | Value |
|-------|-------|
| **Finding** | No origin; SBOM/scan not in CI (R-025) |
| **Status** | Open |
| **Remediation** | P12 remote + optional CI SBOM |
| **Point value** | ~0.5/100 |

---

## Original P0/P1 Audit Items — Reconciliation

Many June-20 P0 items are **obsolete** (demo proves stack works):

| ID | Original claim | Current state |
|----|----------------|---------------|
| R-003 | dpe-svc ctp crash | ✅ dpe-svc runs; demo 20/20 |
| R-004 | Frontend import bugs | ⚠️ Verify `pnpm typecheck` in P7 |
| R-005 | alert-svc consumer | ✅ CP20 chaos/recovery pass |
| R-006 | /metrics missing | ✅ `setup_observability` on services |
| R-002 | RBAC on 5 services | ⚠️ Partial — demo JWT + Kong |

---

## Scoring Model (v7.0.0 target)

| Dimension | v6.1 est. | v7.0 target | Gap driver |
|-----------|-----------|-------------|------------|
| Product completeness | 98 | 100 | Keycloak defer ADR |
| Testing | 88 | 95 | Coverage 75%+ |
| Security | 82 | 95 | Hardening sweep |
| Operations | 92 | 100 | Remote + DR tested |
| Documentation | 90 | 100 | P9 doc suite |
| **Overall** | **~95** | **100** | AG-01–05 |

---

## Recommended Phase 7 Order

1. P7-02 Security hardening sweep (quick wins)
2. P8 Coverage push (AG-02)
3. P10 Keycloak ADR or mock (AG-01)
4. P7-03 Re-score → `docs/audit-final-score-v7.md`
5. POST-C3 RLS (optional v7.1 if time-boxed)

---

## References

- `audit/v2/14-remediation-backlog.md`
- `audit/v2/11-production-readiness-scorecard.md`
- `docs/wave3-regression.md`
- `READINESS.md`
