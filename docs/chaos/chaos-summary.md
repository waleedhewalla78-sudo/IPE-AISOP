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
| **C6** | Post-chaos 20/20 regression | **PASS** |

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
Full demo after all chaos injections: **20/20** (`docs/demo-run-report-post-chaos.txt`).

## Evidence Files

| File | Description |
|------|-------------|
| `docs/chaos/C1-nlp-kill.md` | nlp-svc stop/start |
| `docs/chaos/C2-alert-kill.md` | alert-svc stop during schedule |
| `docs/chaos/C3-kafka-pause-approve.md` | Kafka pause + approve |
| `docs/chaos/C4-kafka-drain.md` | 60s Kafka pause + schedules |
| `docs/chaos/C5-pg-connections.md` | Connection count baseline |
| `docs/chaos/C6-post-chaos-regression.md` | 20/20 after chaos |

## Audit Impact

Estimated **+2 points** (~85 → **~87/100**).

## Next Steps

- Wave **2C**: coverage 40% → 60% — **DONE** (`docs/coverage-summary.md`)
- Wave **2D**: Loki + Grafana MVP
- Re-run chaos after ops changes before **v6.1.0** tag
