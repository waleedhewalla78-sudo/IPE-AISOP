# Converge: IPE V6.0 — Program Rollup

**Date**: 2026-06-23 | **Readiness**: **96/100** | **Target tag**: `v6.0.0`

---

## Convergence Statement

IPE converges from **v1.0.0** (003 autonomous planning) to **v6.0.0** (004 AI-first reassessment) in a single monorepo without greenfield rewrite. All five V6 modules ship as extensions to existing services.

```text
002 Gates (58/62) ──► 003 V5 (45/45) @ v1.0.0 ──► 004 V6 (54/55) @ v6.0.0-ready
```

---

## Feature Convergence Matrix

| Track | Branch | Tasks | Status | Tag |
|-------|--------|-------|--------|-----|
| 002 Release Gates | `002-release-stabilization-gates` | 58/62 | ✅ Gates 1–3 | — |
| 003 Autonomous V5 | `003-autonomous-planning-v5` | 45/45 | ✅ Complete | `v1.0.0` |
| 004 AI-First V6 | `004-ai-first-v6` | 54/55 | ✅ Implemented | T055 pending |
| 005 Program Status | `005-ipe-program-status` | Living | ✅ Active | — |

**Program total**: 157/162 speckit tasks (97%)

---

## Readiness Convergence

| Milestone | Score | Trigger |
|-----------|-------|---------|
| Post-002 Gate 2 | 85/100 | Initial READINESS |
| Post-003 v1.0.0 | 92/100 | Closed-loop + War Room |
| Post-004 V6-R1 | 93/100 | ABP + guardrail |
| **Post-004 V6-R5** | **96/100** | Tariff, CPM, maint, chaos |
| Production 100/100 | 100/100 | k6 200 VU + Chaos evidence |

---

## Demo Convergence (20 checkpoints)

| Range | Phase | Checkpoints |
|-------|-------|-------------|
| 0–16 | 003 baseline | Login, Control Tower, Schedule, War Room, Copilot |
| 17 | V6-R1 | Margin-aware + activity_optimized |
| 18 | V6-R2 | Tariff shock + substitute draft |
| 19 | V6-R3 | CPM cascade p95 <2s |
| 20 | V6-R4/R5 | Maintenance telemetry + Cost of Chaos + recovery plan |

Script: `scripts/run-full-demo.ps1`

---

## Out-of-Scope Convergence (explicit)

| Item | Decision |
|------|----------|
| Keycloak SAML/SCIM | JWT demo auth; C-007 BLOCKED |
| Live SAP/D365 | Mock Odoo only |
| k6/Chaos live evidence | Scripts ready; blocks 100/100 |
| Phoenix commerce | ENP dependency only |

---

## Next Convergence Actions

1. Run `scripts/run-full-demo.ps1` — verify 20/20
2. Run `scripts/launch-verify.ps1` — 10/10 services
3. Tag `v6.0.0` (T055) after stakeholder approval
4. Optional: execute k6 + Chaos for 100/100 production claim
