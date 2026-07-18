# Feature Specification: Phase 8 Wave 1 (8A) — R1 Production Scaffold

**Feature Branch**: `030-phase8-r1-production`  
**Created**: 2026-07-18  
**Status**: Active — Wave 1 (8A)  
**Constitution**: 1.4.2  
**Input**: `IPE-Phase8-Production-Ready-v2.md` + OPEN-TOPICS-REGISTER + Specs 022–029

## Why Spec 030 (not extend 029)

Spec **029-productionization** is **ENG COMPLETE Wave 1** (Kong enterprise, Andon dual-write, RLS 068, MPS/MRP 069, S&OP stage-gate, QA notes). Extending 029 would thrash a converged feature and mix Kong/RLS residuals with production-agent scope.

**Phase 8 Wave 1 (8A)** is tracked as **Spec 030**. Spec 029 residuals (#70/#72/#110 validate) are absorbed into Phase 8 testing honesty — not re-implemented.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Ollama degrade without crash (Priority: P1)

As a planner, when local Ollama is unreachable I still see Control Tower and resolution options; AI narratives fall back to rule-based text and an amber banner explains the degrade.

**Why this priority**: Non-negotiable from Phase 8 v2 §1 — core planning must continue without cloud LLM.

**Independent Test**: Unit tests with unreachable Ollama URL; `GET /api/v1/phase8/ai-status` returns `ollama_available=false` + banner messages EN/AR.

**Acceptance Scenarios**:

1. **Given** Ollama is down, **When** agents request narrative, **Then** rule-based text is returned (`source=rule_based`, `degraded=true`) and no exception propagates.
2. **Given** Ollama is down, **When** UI loads MainLayout, **Then** amber `AiDegradedBanner` is shown.
3. **Given** Ollama returns `/api/tags`, **When** health is checked, **Then** `ollama_available=true` and banner is suppressed.

---

### User Story 2 — Role-gated decisions (Priority: P1)

As Employee / Supervisor / Manager, agent actions respect $1K / $10K / $50K financial thresholds and approval rights from Phase 8 v2 §2.3.

**Why this priority**: Prevents unauthorized high-impact approvals in R1 demos and production.

**Independent Test**: `AgentRoleContext.can_execute` unit matrix + `POST /api/v1/phase8/role-check`.

**Acceptance Scenarios**:

1. **Given** employee + $1,500 impact, **When** approve_resolution, **Then** denied / escalation required.
2. **Given** supervisor + $5,000 impact, **When** approve_resolution, **Then** allowed.
3. **Given** manager + A11 context, **When** get_context, **Then** full financial visibility; non-managers see cost_impact only for A11.

---

### User Story 3 — Write-back safety before live Odoo (Priority: P1)

As a supervisor, I can dry-run an Odoo schedule write-back, see the proposed change logged, and approve it without executing live ERP mutation while PH1-02 is OPEN.

**Why this priority**: Phase 8 v2 §4.2 safety rules; honesty VII — never fake live write-back.

**Independent Test**: Propose dry-run → approve with `execute=true` still queues without live when `ipe.odoo.live_writeback=false`.

**Acceptance Scenarios**:

1. **Given** default flags, **When** propose write-back with `dry_run=true`, **Then** entry logged with `is_live=false`.
2. **Given** live flag false + PH1-02 OPEN, **When** approve with execute, **Then** status is queued/pending message citing live flag or PH1-02 — never claims Odoo updated.
3. **Given** migration 070, **Then** `cdm_write_back_log` has RLS enabled.

---

### User Story 4 — Excel-native Wave 1 expansion (Priority: P2)

As a planner, I can upload demand forecast / quality results / S&OP sales Excel schemas and export Control Tower risk queue + MPS as CSV.

**Why this priority**: Phase 8 v2 §3 Wave 1 slice (not full “Excel everywhere” — that is 8C).

**Independent Test**: upload-svc schema presence tests; `GET /api/v1/phase8/export/*.csv`.

**Acceptance Scenarios**:

1. **Given** file type `demand_forecast` / `quality_results` / `sop_sales_input`, **When** validated, **Then** required columns are defined.
2. **Given** authenticated user, **When** export risk-queue CSV, **Then** CSV headers and rows stream successfully.

---

### User Story 5 — Arabic Phase 8 strings without COM sign-off (Priority: P2)

As an Arabic UI user, new Phase 8 banner and write-back labels appear in AR; G-R2-04 native QA remains OPEN.

**Why this priority**: Engineering bilingual coverage ≠ commercial Arabic sign-off.

**Independent Test**: Locale key audit for `ai.degradedBanner` and `phase8.writeBackDryRun` in en.json + ar.json.

**Acceptance Scenarios**:

1. **Given** locale=ar, **When** degrade banner shows, **Then** Arabic message is used.
2. **Given** G-R2-04, **Then** status docs still mark COM OPEN — never auto-close.

---

### User Story 6 — A18/A19/A20 stubs (Priority: P3)

As engineering, multi-site / learning / exception-monitor agents exist as stubs with unit tests; full behaviour deferred to 8B+.

**Independent Test**: Stub functions return structured payloads with `stub=true` or equivalent honesty flags.

### Edge Cases

- Ollama timeout mid-generate → degrade, do not hang UI beyond client timeout.
- Unknown JWT role alias → normalize to employee.
- Write-back approve by employee → denied by role gate.
- Empty plant capacities for A18 → safe empty/zero split, no crash.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Shared `OllamaClient` with health (`/api/tags`), generate, and rule-based degrade; env `IPE_OLLAMA_URL` default `http://localhost:11434`.
- **FR-002**: `GET /api/v1/phase8/ai-status` exposes `ollama_available`, banner EN/AR, degrade flags.
- **FR-003**: `AgentRoleContext` with employee/supervisor/manager thresholds $1K/$10K/$50K.
- **FR-004**: Write-back propose/approve/list APIs + in-memory/store path + model + migration **070** with RLS.
- **FR-005**: Feature flag `ipe.odoo.live_writeback` defaults **false**.
- **FR-006**: Upload schemas for `demand_forecast`, `quality_results`, `sop_sales_input`.
- **FR-007**: CSV exports for risk queue and MPS under `/api/v1/phase8/export/*`.
- **FR-008**: Kong routes `r2-phase8` / `st-phase8` for `/api/v1/phase8`.
- **FR-009**: Arabic keys for Phase 8 UI strings; G-R2-04 remains OPEN.
- **FR-010**: A18/A19/A20 stubs + unit tests; 8B–8D deferred in docs.
- **FR-011**: Ops Modelfile stubs + README — no claim of fine-tuned weights in repo.
- **FR-012**: Docs: `PHASE8-EXECUTION-AND-TEST-REPORT.md`, `R1-RELEASE-READINESS.md`, PRODUCT-STATUS / feature.json / AGENTS updated.

### Non-Functional / Honesty

- **NFR-001**: Never fake COM (OQ-7, PH1-02, G-R2-04, SOW).
- **NFR-002**: Never push stale `v9.1.0-r2`; `v9.1.1-r2` HOLD on G-R2-04.
- **NFR-003**: Unit tests green for Ollama, roles, write-back, phase8 APIs, upload schemas.

## Success Criteria (Wave 1)

- Unit suites for Spec 030 green.
- AI status API + amber banner wired.
- Live write-back flag default false with PH1-02 cited on execute path.
- Speckit artifacts complete through converge; COM OPEN documented.

## Out of scope / Deferred (8B–8D)

| Sub-phase | Focus |
|-----------|-------|
| 8B | Multi-site A18 live + Odoo write-back expansion |
| 8C | Full Arabic completion + Excel everywhere + SOC 2 prep |
| 8D | Full integration test + partner programme + launch |

Live 70B cluster, fine-tuned weights, live Odoo bi-directional success, native Arabic COM sign-off, OQ-7 pricing — **never claimed in Wave 1**.
