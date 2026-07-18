# Plan — Spec 030 Phase 8 Wave 1 (8A)

**Date**: 2026-07-18 · **Constitution**: 1.4.2 · **Feature**: `specs/030-phase8-r1-production`

## Goal

Ship buildable R1 production scaffold: Ollama+degrade, 3-role context, Excel Wave 1 slice, Odoo write-back safety (mock until PH1-02), bilingual eng strings — without faking COM or live ERP.

## Architecture

```
ipe_shared/
  llm/ollama_client.py       # health + generate + degrade
  roles.py                   # AgentRoleContext ($1K/$10K/$50K)
  models/write_back_log.py   # ORM for cdm_write_back_log
  feature_flags/flags.py     # ipe.odoo.live_writeback (false), ipe.ollama.enabled
dpe-svc/
  api/v1/phase8_production.py
  core/phase8/{agents,narratives,write_back}.py
upload-svc/
  validator schemas: demand_forecast, quality_results, sop_sales_input
apps/web/
  AiDegradedBanner + MainLayout wire + en/ar keys + CT export hook
migrations/070_cdm_write_back_log.py   # RLS ON
ops/ollama/Modelfile.* + README        # stubs only
Kong: r2-phase8 / st-phase8 → /api/v1/phase8
```

## Constitution check

- Honesty VII: mock write-back; Ollama degrade explicit; G-R2-04 OPEN
- RLS I: 070 policies
- Tests III: shared + dpe + upload suites
- No tag without G-R2-04

## Implementation slices

| Slice | Work | Owner |
|-------|------|-------|
| A | Absorb peer Phase 8 code (already in tree) | Speckit |
| B | Kong phase8 routes (R2 + star-trans) | Speckit gap |
| C | Speckit docs + feature.json + AGENTS + PRODUCT-STATUS | Speckit |
| D | Full unit test campaign + PHASE8 + R1 readiness reports | Speckit |
| E | GH issues for open Wave 1 tasks / residuals | Speckit |
| F | Converge + commit (IPE Agent author) | Speckit |

## Test plan

```powershell
cd E:\AISOP\ipe
python -m pytest services/shared/tests/test_ollama_client.py services/shared/tests/test_agent_role_context.py -q
python -m pytest services/dpe-svc/tests/test_phase8_production.py -q
python -m pytest services/upload-svc/tests/test_phase8_uploads.py -q
# Optional regression if time: test_spec029_productionization.py
```

## Data model

See `data-model.md` — `cdm_write_back_log` statuses: dry_run / pending_approval / executed / failed / rolled_back (Wave 1 uses dry_run + pending_approval + queued messaging).

## Contracts

- `GET /api/v1/phase8/ai-status`
- `POST /api/v1/phase8/role-check`
- `POST /api/v1/phase8/write-back` (+ approve/list)
- `GET /api/v1/phase8/export/risk-queue.csv`, `/export/mps.csv`
- A18/A19/A20 stub endpoints under `/api/v1/phase8/agents/*`

## Out of scope this plan

Live 70B, fine-tuned weights in repo, live Odoo execute, full Excel matrix, full Arabic COM, 8B–8D, closing #70/#72/#110 without healthy stack.
