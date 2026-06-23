# IPE Platform — Deployment Readiness

**Version**: v1.0.0-rc1  
**Published**: 2026-06-22  
**Supersedes**: ad-hoc scores 74, 87, 90, 99 in draft artifacts

---

## Overall Score: 85/100

Post–Gate 2 validation (E2E 41/42 pass, critical path green, Gate 1 engineering green).

| Dimension | Score | Notes |
|-----------|-------|-------|
| Product completeness | 88 | Core APS + executive UX per End User Guide routes |
| Testing | 86 | 700+ unit tests; 25+16 integration E2E pass |
| Security | 76 | RBAC + RLS; dev JWT; Keycloak live BLOCKED |
| Operations | 82 | Docker stack verified; ipe-common.env aligned |
| Documentation | 80 | Speckit 002 + clarify/analysis; legacy sync in progress |

---

## Blocked Items

| Item | ID | Reason |
|------|-----|--------|
| Keycloak live IdP / SAML / SCIM | C-007 | No Azure AD/Okta sandbox |

---

## Out of Scope (this release)

- Stripe billing (FR-603)
- React Native mobile app (FR-505)
- WCAG 2.1 AA audit (FR-506)
- ML feature store (FR-405)
- Production K8s canary
- Live SAP/D365 connectors

---

## Residual Risks

- Coverage threshold at 40% (audit R-01)
- No log aggregation deployed (R-08)
- mTLS not enforced in Docker runtime (R-04)
- connector health endpoint flaky on port 8009 (R-11)
- SRE Lead unassigned (R-10)

---

## Evidence

- Gate 1: `specs/002-release-stabilization-gates/evidence/gate-1/`
- Gate 2: `specs/002-release-stabilization-gates/evidence/gate-2/`

---

## Canonical Repository Layout

| Path | Role |
|------|------|
| `D:/AISOP/ipe/` | **Canonical monorepo** — all development, Docker, tests |
| `D:/AISOP/services/` | **Orphan duplicate** — non-canonical; do not deploy or test from this tree |

---

## End User Guide Alignment

Application routes match `docs/END-USER-GUIDE.md`: Control Tower, Schedule, Resolution Center (`/resolution` + `/resolution-center`), Copilot (`/copilot`), Shop Floor, Executive, War Room, AI Trust, SCN Portal, MLOps, Onboarding.

**Login**: http://localhost:8082 — `admin@demo.com` / `demo` (see `GETTING-STARTED.md`). Auth + dashboard APIs in `dpe-svc`; Kong routes in `infrastructure/kong/kong.yml`.
