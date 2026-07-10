# Phase 2 Release 2 — Implementation Log (master rollup)

**Feature**: `018-phase2-release2`  
**Sprint window**: 2026-07-01 → 2026-07-10 (ops cutover)  
**Release head**: `ad494e0` (+6 commits ahead of `v9.4.0-p3` tag per `feature.json`)

## Executive summary

Release 2 scaffolding (compose profile, demand/scenario/nlp routes, frontend hubs, migrations 039–043) is landed in-tree. Wave 1 bridge remains **25%** (Spec 017). Kind cluster restabilized **2026-07-10** after probe-induced CrashLoop; compose Release 2 stack not running on demo host — **G-R2-01 FAIL**, **G-R2-05 PASS (Kind partial)**.

## Sprint rollup

| Sprint | Theme | Outcome | Evidence |
|--------|-------|---------|----------|
| W1 bridge | Odoo v2 + OTD | In progress | `specs/017-first-release-plan/tasks.md` |
| S1 | R2 infrastructure | Done | `infrastructure/docker/docker-compose.release2.yml`, `scripts/deploy-release2.ps1` |
| S2 | Copilot live data | Done (smoke partial) | `services/nlp-svc/app/core/copilot_tools.py`, tests |
| S3–S4 | Demand + Scenarios | Done (SES-first) | `demand-svc`, `scenario-svc`, UI pages |
| S5 | Arabic 8+ | Done | `docs/qa/arabic-qa-r2.md` |
| S6–S7 | OTD extended + Odoo polish | Done in tree | migrations `039`, OTD APIs |
| S8–S11 | Ops, intel, S&OP | Done in tree | migrations `040`–`042`, ops/supply_chain/sop_report |
| S12 | SAP B1 | **CUT** | `specs/018-phase2-release2/sprints/S12-CUT.md` |

## Ops events (2026-07-10)

1. Removed HPAs (none present); scaled all `ipe` deployments to 1 replica.
2. Diagnosed CrashLoop: liveness `timeoutSeconds=1` vs health latency ~1.3s; SIGTERM exit 143; kind API token mount timeouts.
3. Full pod recycle → **8/8 Ready**.
4. Extended `scripts/run-release2-demo.ps1` for gate **G-R2-05**; report written.

## Open items

- [ ] Bring up Release 2 compose and capture `release2-smoke.ps1` log (G-R2-01).
- [ ] Complete W1-03–W1-08 verification (G-R2-03).
- [ ] Helm: increase probe timeouts for kind dev profile.
- [ ] Tag `v9.1.0-r2` after full gate matrix green.

## Doc index

- Gates: `specs/018-phase2-release2/GATES.md`
- Spec: `specs/018-phase2-release2/spec.md`
- Tasks: `specs/018-phase2-release2/tasks.md`
- Kind QA: `docs/qa/kind-restabilize-2026-07-10.txt`
- Demo: `docs/demo-data/release2-demo-g-r2-05.txt`
