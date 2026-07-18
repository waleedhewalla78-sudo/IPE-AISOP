# Research — Spec 030 / Phase 8 Wave 1

## Decision: Spec 030 vs extend 029

**Chosen:** Spec 030. Spec 029 converge verdict is ENG COMPLETE Wave 1; Phase 8 adds Ollama/roles/Excel/write-back safety as a new production-agent track. Residuals from 029 (validate #70/#72/#110) remain OPEN and are referenced, not re-scoped into greenfield 029 work.

## Ollama

- Default `IPE_OLLAMA_URL=http://localhost:11434`
- Health: `GET /api/tags`
- Models `ipe-planner` / `ipe-analyst` are **ops stubs** (Modelfile only); runtime falls back to `llama3.1` tag name or rule-based text
- Copilot (A7) remains Claude-first per existing nlp-svc design
- UI amber banner copy matches Phase 8 v2 §1.1

## Write-back

- Table `cdm_write_back_log` with dry_run / pending_approval / executed / failed / rolled_back
- Live execute gated by `ipe.odoo.live_writeback` (default false) + PH1-02
- Wave 1 store may be in-memory for unit speed with ORM/migration present for deploy path

## Roles

- Exact thresholds from Phase 8 v2 §2.3: employee $1K, supervisor $10K, manager $50K
- JWT aliases: planner→supervisor, admin/executive→manager, operator/viewer→employee

## Excel Wave 1 slice

- New schemas only (not full §3.1 matrix): demand_forecast, quality_results, sop_sales_input
- Exports: risk queue + MPS CSV (template rows acceptable when live queue not injected)

## Alternatives considered

| Option | Why rejected |
|--------|--------------|
| Extend Spec 029 | Thrash converged feature; mix concerns |
| Full 8A–8D in one Speckit run | Violates honesty / COM; 30-week scope |
| Require live GPU for merge | Blocks CI; degrade path is the product requirement |
