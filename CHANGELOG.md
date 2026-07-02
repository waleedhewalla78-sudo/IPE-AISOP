# Changelog

All notable changes to the IPE platform are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**Authoritative product spec:** [docs/PRD-IPE-COMPREHENSIVE-AS-IS.md](docs/PRD-IPE-COMPREHENSIVE-AS-IS.md)

---

## [Unreleased] — Release 1 (v9.0.0-r1 target)

### Added

- **Release 1 profile** — 8-service compose (`docker-compose.release1.yml`), Kong `kong.release1.yml`, web `VITE_RELEASE_PROFILE=release1`
- **Odoo sync engine** — XML-RPC full sync: products, work centers, BOMs, BOM lines, routing, MOs, demands, supply (`connector/app/odoo/sync_engine.py`)
- **Odoo 17/19 field mappers** — date_start/finished, scheduled_date, timezone-aware datetimes, BomLine tenant_id
- **Post-sync feasibility rescore** — commit before fea-svc rescore in full sync
- **Sync APIs** — `POST /sync/run`, `GET /sync/status`, `GET /sync/data-quality`
- **Odoo activate write-back** — `POST /sync/odoo/activate` (XML-RPC)
- **Star Trans Odoo seed** — `scripts/seed-odoo-startrans.py` (TR-500/TR-1000 BOMs + MOs)
- **R1 customer docs** — implementation playbook, training curriculum, data quality checklist, support guide
- **Arabic MVP** — Control Tower + nav (`locales/ar.json`)
- **Comprehensive PRD** — `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md`, executive one-pager

### Fixed

- Mapper `default_code=False` → null internal_ref
- MO sync Odoo 19 invalid fields (`date_planned_*`, `__last_update`)
- Supply/demand date parsing (string → timezone-aware datetime)
- `parse_odoo_datetime` definition order in mapper

---

## [v8.2.0] — 2026-06-28

### Added

- **U7 Design AI** — material-svc: engineering materials, design recommendations (CP28)
- **U8 Responsible procurement** — procurement-svc: spend, supplier compliance (CP29)
- **Sustainability demo** — sustain-svc dashboard (CP31)
- **Quality intelligence demo** — quality-svc SPC dashboard (CP32)
- **32/32 demo checkpoints** — Star Trans profile validation
- **Supply network seed** — migration 034 (4 plants, 6 lanes)
- **RLS INSERT policies** — migration 035
- **v8 integration tests** — `tests/integration/test_v8_e2e.py` (5/5)
- `docs/DEPLOYMENT-READINESS-v8.2.0.md`, `docs/PRD-IPE-v8.2.0-ENTERPRISE.md`

### Changed

- Speckit readiness **100/100**; audit ~92/100
- POST-B scaffolds: Keycloak, secrets vault, Stripe, SAP/D365 ERP base

---

## [v8.1.0] — 2026-06-27

### Added

- **U4 Supply orchestration** — supply-svc (CP25)
- **U5 Order management / ATP** — order-svc (CP26)
- **U6 Equipment intelligence** — equipment-svc (CP27)
- Migrations 030 (v8 phase 2 entities)

---

## [v8.0.0] — 2026-06-27

### Added

- **U1 Role-based Copilot sessions** — nlp-svc (CP30)
- **U2 Demand sensing & forecasting** — demand-svc (CP21–22)
- **U3 Scenario workbench** — scenario-svc (CP23–24)
- **Module hub consolidation** — 6 navigation hubs (spec 006)
- Migrations 029 (v8 phase 1 entities)

---

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
