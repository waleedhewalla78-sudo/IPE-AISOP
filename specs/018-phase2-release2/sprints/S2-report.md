# Sprint S2 Report — Copilot Live Planning Data

**Gate**: G-R2-02  
**Date**: 2026-07-10  
**Sprint**: S2 — Copilot integration with live planning data  
**Authority**: `docs/PHASE2-IMPLEMENTATION-GUIDE.md` Sprint 2

---

## Summary

Connected nlp-svc Copilot tool registry to live planning service APIs with tenant-scoped httpx calls, shadow mode default, R2 LLM fallback chain, frontend timeout handling, and unit tests.

---

## Deliverables

| Task | File | Status |
|------|------|--------|
| S2-01 Planning tools (7) | `services/nlp-svc/app/core/copilot_tools.py` | ✅ |
| S2-02 Shadow mode default | `services/nlp-svc/app/core/copilot_agent.py` | ✅ |
| S2-03 LLM fallback chain | `services/nlp-svc/app/core/llm_router.py`, `llm_client.py` | ✅ |
| S2-04 Copilot panel tenant + timeout | `apps/web/src/features/copilot/components/CopilotPanel.tsx` | ✅ |
| S2-05 Unit tests | `services/nlp-svc/tests/test_copilot_tools_r2.py` | ✅ |

---

## Tools Added (R2)

| Tool | Service | Endpoint |
|------|---------|----------|
| `get_mo_status` | dpe-svc | `GET /api/v1/dashboard/mos` |
| `get_feasibility_queue` | fea-svc | `GET /api/v1/feasibility/queue` |
| `get_schedule` | cap-svc | `GET /api/v1/capacity/schedule/active` |
| `get_otd_metrics` | dpe-svc | `GET /api/v1/dashboard/analytics` (fallback: `/analytics/otd-baseline`) |
| `get_material_availability` | mat-svc | `POST /api/v1/material/check-availability` |
| `get_sync_status` | connector | `GET /api/v1/sync/status` |
| `get_resolution_scenarios` | dpe-svc → res-svc | `GET /api/v1/resolution/scenarios/{mo_id}` (fallback: res-svc query) |

All tools pass `X-Tenant-ID` on every request.

---

## Shadow Mode

- `IPE_COPILOT_SHADOW_MODE=true` (default) in nlp-svc config
- `run_agent_with_tools(..., shadow_mode=None)` defaults to shadow mode
- System prompt instructs suggest-only behavior; no live write-backs

---

## LLM Fallback (R2)

Tier 1 / `auto` preference order:

1. Anthropic (`IPE_ANTHROPIC_API_KEY`)
2. OpenRouter (`IPE_OPENROUTER_API_KEY`)
3. Ollama (`IPE_OLLAMA_ENDPOINT_URL`)
4. `LLMUnavailableError` if none available

Verified via `get_r2_fallback_chain()` in `llm_client.py` and updated `test_llm_router.py`.

---

## Frontend

- `CopilotPanel` sends `X-Tenant-ID` from JWT `tenant_id` claim
- `fetchWithTimeout` uses 300s (`COPILOT_TIMEOUT_MS`) matching Kong upstream
- Timeout surfaces user-friendly message (not raw abort)

---

## Test Results

| Suite | Command | Result |
|-------|---------|--------|
| R2 tool unit tests | `pytest tests/test_copilot_tools_r2.py` | **9/9 PASS** |
| LLM tier1 fallback | `test_llm_router.py` (tier1 chain) | **1/1 PASS** |
| W1-02 smoke (12 tests) | `scripts/wave1/verify-copilot-r1-smoke.ps1` | **12/12 PASS** |

### W1-02 smoke breakdown

| Step | Tests | Result |
|------|-------|--------|
| Vitest CopilotPanel | 2 | PASS |
| Vitest copilot-r1-smoke | 5 | PASS |
| nlp-svc 401 unauthenticated | 1 | PASS |
| Playwright copilot e2e | 4 | PASS |

Smoke fix: removed pre-Playwright kill of port 8082 so `webServer` can start (`verify-copilot-r1-smoke.ps1`).

---

## Gate G-R2-02 Criteria

| Criterion | Status |
|-----------|--------|
| 7 planning tools with tenant header | ✅ |
| Shadow mode default | ✅ |
| LLM fallback Anthropic → OpenRouter → Ollama | ✅ |
| CopilotPanel X-Tenant-ID + 300s timeout | ✅ |
| `test_copilot_tools_r2.py` | ✅ |
| W1-02 smoke 12/12 | ✅ |

---

## Notes

- `get_otd_metrics` and `get_resolution_scenarios` include res-svc / analytics fallbacks when dpe-svc guide paths are not yet deployed.
- `IPE_CONNECTOR_SVC_URL` added to nlp-svc settings for sync status tool.

---

*S2 report — G-R2-02*
