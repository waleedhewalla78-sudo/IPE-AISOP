# Plan — Spec 030 Phase 8 Wave 1 (8A) — post-ship refresh

**Date**: 2026-07-18 · **Constitution**: 1.4.2  
**Shipped**: `38e78fa` (feat) · `6f51c02` (test evidence docs)

## Goal (remaining Speckit work only)

Align Speckit analyze → converge with **already shipped** Wave 1 code. **Do not rebuild** Ollama/roles/write-back/Excel/UI.

## Architecture (shipped — reference)

```
ipe_shared/llm/ollama_client.py + roles.py + models/write_back_log.py
dpe-svc/api/v1/phase8_production.py + core/phase8/*
upload-svc schemas + apps/web AiDegradedBanner
migrations/070 + Kong r2-phase8/st-phase8
ops/ollama/ Modelfile stubs
```

## This Speckit close-out slice

| Slice | Work |
|-------|------|
| A | Refresh analyze/plan/tasks against `38e78fa`/`6f51c02` |
| B | taskstoissues — residuals only (#136; document 8B–8D + COM) |
| C | implement.md — cite shipped commits; no new product code |
| D | converge — ENG COMPLETE Wave 1; list OPEN residuals |
| E | feature.json constitution **1.4.2** + readiness note |
| F | Commit Speckit artifacts (IPE Agent author) |

## Out of scope

Phase 8 feature rebuild, live Odoo, G-R2-04 close, `v9.1.1-r2` tag, 8B–8D implementation, fake validate PASS.
