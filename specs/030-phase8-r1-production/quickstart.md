# Quickstart — Spec 030 Phase 8 Wave 1

```powershell
cd E:\AISOP\ipe
copy .env.template .env   # if missing

# Unit tests (no Ollama / Odoo required)
python -m pytest services/shared/tests/test_ollama_client.py `
  services/shared/tests/test_agent_role_context.py -q
python -m pytest services/dpe-svc/tests/test_phase8_production.py -q
python -m pytest services/upload-svc/tests/test_phase8_uploads.py -q

# Optional: local Ollama
# ollama pull llama3.1
# ollama create ipe-planner -f ops/ollama/Modelfile.ipe-planner
# $env:IPE_OLLAMA_URL = "http://localhost:11434"
# GET http://localhost:8020/api/v1/phase8/ai-status   # via dpe or Kong

# Kong routes (R2 / star-trans)
# /api/v1/phase8 → dpe-svc (r2-phase8 / st-phase8)
```

**Honesty:** `ipe.odoo.live_writeback` stays false until PH1-02. G-R2-04 / OQ-7 remain human OPEN.
