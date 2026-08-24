# BATCH1-5 — Performance baseline

**Date:** 2026-08-24  
**Prerequisite:** BATCH1-1..4 documented YELLOW (not GREEN).

## SLA targets (Delivery Plan)

| SLA | Target |
|-----|--------|
| Page load | <2s, 20 VU, 500 MOs |
| Feasibility recalc | <10s |
| Optimizer | <30s / 500 MOs |
| Excel upload | <60s / 10k rows |
| Copilot | <8s |
| Report | <15s |

## What ran

- Did **not** seed 500 MOs / 50 WCs (would disturb lab Star Trans 28-MO graph).
- Did **not** run 10-minute k6 (no new load dataset; existing `scripts/run-k6-slo.ps1` not re-executed this session).
- **No indexes added** — none proven low-risk against a 500-MO baseline.

## VERDICT

**YELLOW** — SLA table recorded; baseline JSON not produced; no blocking FAIL claimed because no load was executed. Not GREEN. Does not fake PASS.
