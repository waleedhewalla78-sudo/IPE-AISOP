# Ollama ops stubs — Phase 8 Wave 1

IPE does **not** claim production fine-tuned `ipe-planner` / `ipe-analyst` weights
are present in this repository. These Modelfiles are stubs for ops to create
tagged models from a base Llama (or Mixtral) already installed on the GPU host.

```powershell
# Prerequisites: Ollama installed; base model pulled
ollama pull llama3.1
ollama create ipe-planner -f ops/ollama/Modelfile.ipe-planner
ollama create ipe-analyst -f ops/ollama/Modelfile.ipe-analyst
$env:IPE_OLLAMA_URL = "http://localhost:11434"
```

Health probe used by IPE: `GET {IPE_OLLAMA_URL}/api/tags`

When unreachable, agents automatically degrade to rule-based text and the UI
shows an amber banner. Copilot (A7) remains Claude-first per nlp-svc design.
