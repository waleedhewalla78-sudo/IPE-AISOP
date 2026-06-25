# IPE Platform — Deployment Readiness

**Version**: v6.0.0 (004 complete)  
**Published**: 2026-06-23  
**Supersedes**: v1.0.0 + V6-R1 (93/100)

---

## Overall Score: 96/100

Post–003 autonomous planning (45/45) plus **004 V6-R1–R5 complete** (54/55 tasks; T055 git tag pending approval). Suitable for **client demo, staging launch, and v6.0.0 promotion**. Production at **100/100** requires executed k6 200 VU + Chaos Mesh evidence (scripts ready).

| Dimension | Score | Notes |
|-----------|-------|-------|
| Product completeness | 98 | V5 loop + V6 tariff/CPM/maintenance/chaos/war-room |
| Testing | 92 | 870+ backend tests; launch-verify + demo checkpoints 17–20 |
| Security | 76 | RBAC + RLS; JWT demo auth; Keycloak live BLOCKED |
| Operations | 88 | Airflow, launch checklist, CPM Prometheus metric |
| Documentation | 95 | clarify-v6, analyze-v6, speckit 005, LAUNCH-CHECKLIST |

See `specs/004-ai-first-v6/clarify-v6.md` and `specs/003-autonomous-planning-v5/clarify.md`.

---

## V6.0 Deliverables (004)

| Phase | Exit Gate | Demo Checkpoint |
|-------|-----------|-----------------|
| V6-R1 Activity-Based Planning | ≥8% activity-cost delta | 17 |
| V6-R2 Tariff & Landed Cost | Shock + substitute draft | 18 |
| V6-R3 Visual CPM | p95 cascade <2s | 19 |
| V6-R4 Predictive Maintenance | RUL → block published | 20 |
| V6-R5 Cost of Chaos + War Room | ≥3 chaos categories; recovery top-3 | 20 |

**New routes**: `/tariff`, `/cost-of-chaos`, CPM drag on `/schedule`, MS Project export, War Room recovery cards.

---

## Blocked Items

| Item | ID | Reason |
|------|-----|--------|
| Keycloak live IdP / SAML / SCIM | C-007 | Demo uses JWT; no Azure AD/Okta sandbox |

---

## Out of Scope (this release)

- Stripe billing (FR-603)
- React Native mobile app (FR-505)
- WCAG 2.1 AA audit (FR-506)
- Production K8s canary
- Live SAP/D365 connectors (mock Odoo only)

---

## Residual Risks (96 → 100)

- **k6 200 VU** — script at `tests/performance/k6/load-test-200vu.js`; not executed in CI evidence
- **Chaos Mesh** — `infrastructure/chaos/` + `scripts/r4-verify.ps1`; evidence not attached
- Keycloak SAML/SCIM (C-007) — BLOCKED
- Coverage threshold at 40% (audit R-01)

---

## Evidence

- Gate 1–2: `specs/002-release-stabilization-gates/evidence/`
- 003 R4: `specs/003-autonomous-planning-v5/evidence/r4/` (mappers; k6/Chaos pending)
- **Launch verification**: `scripts/launch-verify.ps1`
- **Demo**: `scripts/run-full-demo.ps1` (20 checkpoints)
- **V6 analysis**: `specs/004-ai-first-v6/analyze-v6.md`

---

## Canonical Repository Layout

| Path | Role |
|------|------|
| `E:/AISOP/ipe/` | **Canonical monorepo** |
| `E:/AISOP/services/` | Orphan duplicate — do not deploy |
| `E:/AISOP/.specify/` | Spec Kit config (program feature: 005) |

---

## End User Guide Alignment

Routes: Control Tower (+ Tariff panel), Schedule (CPM + export), `/tariff`, `/cost-of-chaos`, War Room (recovery plan), Resolution Center, Copilot, Executive, Shop Floor, MDR, AI Trust, SCN Portal.

**Login**: http://localhost:8082 — `admin@demo.com` / `demo`
