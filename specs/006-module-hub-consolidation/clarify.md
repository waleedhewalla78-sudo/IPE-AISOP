# Clarify — 006 Module Hub Consolidation

**Date**: 2026-06-27

## Decisions

| Question | Decision |
|----------|----------|
| Merge backend services? | **No** — UI composition only |
| Inventory module source? | **New tab** calling existing `GET /api/v1/material/inventory-summary` |
| Hidden modules (Quality, Compliance, MDR)? | **Surfaced** under AI & Governance |
| Default landing after login? | `/planning/dashboard` |
| Legacy URL handling? | **301-style React redirects** for all 14 old paths |
| Shop Floor standalone? | **Yes** — operator persona |
| Dashboard data | Live API aggregation; no new endpoints |

## Assumptions

- Host Ollama / demo stack unchanged
- Existing page components reused without refactor
- Tab state via nested React Router routes (not query params)
