# Changelog

All notable changes to the IPE platform are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [v7.0.0] — 2026-06-27

### Added

- **Ollama local LLM backbone** — query orchestrator + tool-calling copilot (`ollama_tool_client.py`)
- Docker overlays: `docker-compose.ollama.yml`, `docker-compose.ollama-host.yml`
- `scripts/start-ollama-stack.ps1` with `-UseHostOllama` flag
- `docs/PRODUCT-STATUS.md`, `docs/PRODUCTION-BLOCKERS.md`, `docs/END-USER-GUIDE.md`
- `docs/AI-AGENTS-ARCHITECTURE.md` — full agent roles + Ollama deployment
- OpenRouter LLM provider for cloud fallback
- Phase 5 gap analysis reports (speckit, audit, coverage, documentation)
- Speckit 162/162 completion (T049–T051 closed; T053 cancelled)
- ADR-001 Keycloak deferral to v8.0.0
- Documentation suite: CONTRIBUTING, runbooks, architecture index, API reference

### Changed

- Kong nlp-svc upstream timeout → 300s (local LLM cold-start)
- `IPE_LLM_PRIMARY_PROVIDER` — auto | ollama | openrouter | anthropic
- Coverage gate ≥75% per service — all six core services pass
- READINESS.md and release checklist updated for v7.0.0 RC

### Fixed

- Copilot 503 — OpenRouter + Ollama integration; `IPE_*` env prefix
- Intent classifier fallback on LLM unavailable
- Tool-calling copilot Anthropic-only gap — Ollama tools supported
- CopilotPanel missing `X-Tenant-ID` header
- del-svc spurious `mock_anthropic_key` env var

---

## [v6.1.0] — 2026-06-26

### Added

- TLS internal services runbook (`docs/runbooks/tls-internal.md`)
- JWT rotation runbook (`docs/runbooks/jwt-rotation.md`)
- Migration 028: SEC-05 password_hash backfill
- Wave 3 live regression evidence (demo 20/20, chaos 6/6)

### Fixed

- Auth password verification for `{SHA-256}` hashed credentials
- MDR fail-closed gate (503) on capacity endpoints
- Optimistic locking on schedule approve (409 conflict)

---

## [v6.0.1] — 2026-06-25

### Fixed

- MDR internal JWT forwarding for cross-service calls
- Audit fixes C-01, BUG-02, BUG-03 live-verified

---

## [v6.0.0] — 2026-06-24

### Added

- V6 features: tariff shock, visual CPM, predictive maintenance, cost of chaos, war room
- Demo 20/20 live gate
- Speckit 004 AI-first V6 complete (55/55 tasks)

---

## [v1.0.0] — 2026-06-22

### Added

- Initial production release
- 14-service microservices architecture
- Kong API gateway with JWT auth
- Demo stack and critical path E2E (Gate 2 passed)
- PostgreSQL CDM with tenant RLS (migrations 024+)
