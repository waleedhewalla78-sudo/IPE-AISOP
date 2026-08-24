# IPE Governing Principles & Development Guidelines

**Active Speckit feature:** Spec **040** Star Trans Demo Aug 18 (`specs/040-startrans-demo-aug18`); prior Phase 9 parent Spec **033** / **033a** scaffolds remain in tree  
**Amended:** 2026-08-14 · **Ratified:** 2026-06-20  
**Constitution:** `ipe/.specify/memory/constitution.md` **v1.4.7** (canonical)

This document shares the binding project constitution for stakeholders. If conflict arises, the constitution file wins.

---

## Identity

IPE (Intelligent Planning Engine) is a microservices, event-driven platform for **feasibility-first manufacturing planning** in MENA mid-market discrete manufacturing (Odoo-native, Arabic-capable).

**Canonical codebase:** `ipe/` only (not orphan root `services/`).

---

## Core Principles (binding)

### I. Tenant Isolation via RLS (NON-NEGOTIABLE)
- Every `tenant_id` table MUST have RLS in the same migration.
- App MUST set `app.current_tenant` / `app.current_tenant_id` before tenant queries.
- Cross-tenant leakage is a release blocker.

### II. Service Authentication & Authorization
- Zero open endpoints except `/health`, `/ready`, `/metrics`.
- State-changing ops MUST enforce RBAC.
- Kong rate limits on public paths; production secrets in Vault — never git.

### III. Test-Backed Changes (NON-NEGOTIABLE)
- Behavioral changes need automated tests; tests MUST pass before merge.
- No real network in unit tests; Odoo changes need mapper + mock + e2e/fixture coverage.

### IV. Event-Driven Architecture Integrity
- Full platform: Kafka/EIB as documented.
- R1: Kafka MAY be omitted (`IPE_KAFKA_BOOTSTRAP_SERVERS=""`).
- **Phase 9A additive:** Redis Streams (`ipe_events`) for targeted agent cascade; publishes MUST be durable (`cdm_event_log` + RLS) when DB available.
- Consumers: idempotent, timeouts, Streams XPENDING/XCLAIM DLQ.

### V. Service Architecture & API Consistency
- Layered `app/api|models|services|events`; health endpoints on every deployed service.
- Ports reconciled across Dockerfile, compose, Kong, Helm.
- R1 customer slice is the small compose set; new services need compose+Kong before enablement.

### VI. Observability & Monitoring
- `/metrics`, structured logs, correlation IDs.
- k6 SLO + stress are separate gates.
- Sync and agent runs MUST be observable in UI/logs.

### VII. Customer-First Release Slicing
- Odoo connector is the #1 product path; one ERP first.
- Three screens minimum: Control Tower, Resolution, OTD.
- Arabic eng keys ≠ G-R2-04 human sign-off (OPEN).
- **Honesty:** never invent pricing, live Odoo, Arabic QA, or SOW signature.

### VIII. Enterprise Gate Verification
- No enterprise tag without scripted gate evidence.
- Never push stale `v9.1.0-r2`; `v9.1.1-r2` only after G-R2-04.

### IX. Operations Intelligence Program
- Ops Blueprint phase numbers ≠ Platform K8s phase numbers.
- Specs 024–030 Wave 1 ENG COMPLETE; COM blockers stay OPEN.

### X. Agentic Autonomy Governance
- L1–L4 governance ladder; A17 sole cross-functional arbiter.
- Live Odoo accounting / IoT / FX remain MOCK/STUB until PH1-02.
- Auto-PO / write-back default dry-run until written approval + flag.
- Phase 9B–9F Wave 1 MUST ship soft stubs (`live:false` / scaffold badges) — never claim production ML accuracy, live SAP B1, or OCR Arabic sign-off.

---

## Development Workflow Guidelines

| Rule | Practice |
|------|----------|
| Branch | `feat/`, `fix/`, `chore/`, or Speckit `NNN-name` |
| Spec before code | Speckit: constitution → specify → clarify → plan → tasks → implement → converge |
| Migrations | Linear Alembic; Phase 9A **072–077**; Phase 9B–9F Wave 1 **078+** |
| Kong | Every new public API prefix needs a route (JWT); Phase 9 under `/api/v1/phase9` |
| i18n | New UI strings EN + AR |
| Roles | Use `AgentRoleContext` for financial/autonomy gates |
| COM | OQ-7, PH1-01, PH1-02, G-R2-04, OQ-1, OQ-9, OQ-3, OQ-8 — never auto-close |

## Active vs deferred (2026-08-01)

| Item | Status |
|------|--------|
| Specs 022–032 Wave 1 | ENG COMPLETE |
| Spec 033a Wave 9A | ENG COMPLETE scaffold |
| Specs 033b–033f Wave 1 | **ENG scaffolds IN SCOPE** (soft commercial) |
| Program verdict | ENG READY / COM CONDITIONAL |

## Amendment policy

- MAJOR: remove/redefine principles  
- MINOR: new principle  
- PATCH: clarification  
- PR required; Sync Impact Report HTML comment at top of constitution  

**Full text:** `ipe/.specify/memory/constitution.md`
