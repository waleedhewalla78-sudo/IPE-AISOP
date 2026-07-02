# Chaos Engineering Results — IPE v6.0.1

**Date:** 2026-06-26  
**Runner:** `scripts/run-chaos-scenarios.ps1`  
**Stack:** Demo overlay (docker-compose.demo.yml)

## Summary

| Scenario | Test | Result |
|----------|------|--------|
| **C1** | Kill `nlp-svc` — non-NLP APIs | **PASS** |
| **C2** | Kill `alert-svc` — schedule POST | **PASS** |
| **C3** | Kafka pause — approve during outage | **PASS** |
| **C4** | Kafka pause 60s — 3 schedules | **PASS** |
| **C5** | PG connections under k6 smoke | **PASS** |
| **C6** | Post-chaos 30/30 regression | **PASS** |

**Overall: 6/6 passed**

## Highlights

### C3 — Validates BUG-01 / MDR regression class
During Kafka pause, approve returned:
- HTTP **200**
- `activated_count: 2`
- `erp_event_published: false`
- `error.code: ERP_EVENT_PUBLISH_FAILED`

CDM persisted; ERP sync correctly deferred (fail-visible, not silent).

### C4 — Scheduling resilient to Kafka outage
Three consecutive `POST /capacity/schedule` calls during Kafka pause: **200, 200, 200**.

### C6 — No lasting damage
Full demo after all chaos injections: **30/30** (`docs/demo-run-report-post-chaos.txt`).

## Post-v8 Chaos Validation (2026-06-28)

Re-validated C1–C6 against v8 stack (7 additional services, 30→32 demo checkpoints).

| Scenario | Result | Notes |
|----------|--------|-------|
| C1 | PASS | nlp-svc kill — non-NLP APIs unaffected |
| C2 | PASS | alert-svc kill — schedule POST resilient |
| C3 | PASS | Kafka pause — approve defers ERP publish |
| C4 | PASS | 3 schedules during Kafka pause — all 200 |
| C5 | PASS | PG connections within baseline |
| C6 | PASS | **30/30** demo post-chaos (pre-CP31/32 extension) |

**Demo after v8.2.0 closure:** 32/32 with sustain + quality checkpoints (CP31–32).

All historical **20/20** references superseded by **30/30** (v8) and **32/32** (v8.2.0 extended demo).

## Evidence Files

| File | Description |
|------|-------------|
| `docs/chaos/C1-nlp-kill.md` | nlp-svc stop/start |
| `docs/chaos/C2-alert-kill.md` | alert-svc stop during schedule |
| `docs/chaos/C3-kafka-pause-approve.md` | Kafka pause + approve |
| `docs/chaos/C4-kafka-drain.md` | 60s Kafka pause + schedules |
| `docs/chaos/C5-pg-connections.md` | Connection count baseline |
| `docs/chaos/C6-post-chaos-regression.md` | 30/30 after chaos |

## Audit Impact

Estimated **+2 points** (~85 → **~87/100**).

## Next Steps

- Wave **2C**: coverage 40% → 60% — **DONE** (`docs/coverage-summary.md`)
- Wave **2D**: Loki + Grafana MVP
- Re-run chaos after ops changes before **v6.1.0** tag
