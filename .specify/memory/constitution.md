# IPE Platform Constitution

IPE (Intelligent Process Engine) is a microservices-based, event-driven platform for intelligent process automation. These principles are derived from the codebase architecture and V2 audit findings. They are binding on all changes.

## Core Principles

### I. Tenant Isolation via Row-Level Security (NON-NEGOTIABLE)

Every database migration MUST enforce Row-Level Security on every table bearing a `tenant_id` column.

- **RLS is not optional.** Any new table with `tenant_id` MUST have RLS enabled in the same migration (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY` followed by `CREATE POLICY tenant_isolation ... USING (tenant_id = current_setting('app.current_tenant')::uuid)`).
- **Existing gap MUST be closed.** Migrations 002-012 created 22 tables with `tenant_id` but NO RLS policies. Any change touching those migrations or their models MUST add the missing RLS policies.
- **Dynamic RLS loop is the pattern.** Migration 001's `FOR table IN (SELECT ...)` loop is the canonical pattern; new migrations SHOULD use the same procedural approach.
- **Cross-tenant queries MUST use `app.set_tenant()`.** Application code MUST set `app.current_tenant` via the `get_current_tenant` dependency before executing tenant-scoped queries.

**Rationale:** 22 tables without RLS represent a SOC 2 violation and a cross-tenant data exposure risk. Multi-tenant isolation is the platform's most critical security boundary.

### II. Service Authentication & Authorization

Every API endpoint MUST be protected by at least one authentication or authorization layer.

- **Zero open endpoints.** Every route MUST verify a valid JWT via the `get_current_user` dependency, except explicitly documented health/readiness probes (`/health`, `/ready`, `/metrics`).
- **RBAC is mandatory for state-changing operations.** POST/PUT/PATCH/DELETE endpoints MUST check role permissions via `require_role(...)` or equivalent. The 5 services with zero RBAC (mat-svc, cap-svc, fea-svc, res-svc, rec-svc) MUST be remediated before any deployment.
- **Rate limiting is required.** Every service MUST configure `slowapi` rate limits on its public endpoints.
- **API keys for machine-to-machine.** Internal service-to-service calls SHOULD use API keys or mTLS, not user JWTs.

**Rationale:** 3 alert-svc endpoints had zero authentication and 5 services had zero RBAC. This is not acceptable for production.

### III. Test-Backed Changes (NON-NEGOTIABLE)

Every behavioral change MUST be accompanied by automated tests.

- **Tests MUST pass before merge.** CI runs pytest with coverage across the matrix. Changes MUST pass on all configured platforms.
- **No regression in test categories.** Unit tests, integration tests (with Docker services), and end-to-end flow tests MUST all remain green.
- **Service-level test files required.** Every service MUST have at least `tests/test_api.py` (endpoint tests) and `tests/test_models.py` (model/DB tests). Services missing these MUST add them.
- **Event tests must verify produce AND consume.** Any change to event producers MUST include a test that the corresponding consumer can process the message.
- **No real network in tests.** External services (Kafka, PostgreSQL, Redis) MUST be stubbed or use testcontainers.

**Rationale:** The audit found no test execution was possible due to missing dev dependencies and infrastructure. This MUST be fixed.

### IV. Event-Driven Architecture Integrity

The event bus is the backbone of inter-service communication; all topics, schemas, and handlers MUST be explicitly declared.

- **Every topic MUST be created.** Topics are declared in `infrastructure/kafka/setup-topics.sh` or equivalent. The 11 topics referenced by code but NOT created in any script MUST be added before deployment.
- **Avro schemas are mandatory for production topics.** Every new event type MUST have a registered Avro schema in the Schema Registry. Schemas MUST be versioned.
- **Producers and consumers MUST be tested in pairs.** A change that adds a producer event MUST include or update the corresponding consumer handler, and vice versa.
- **Consumer resilience.** Every consumer MUST:
  - Implement idempotent processing (at-least-once delivery assumption)
  - Handle deserialization errors gracefully (dead-letter queue or log+skip)
  - Timeout after 30s of processing per message
- **`create_consumer()` pattern is the standard.** All services MUST use `ipe_shared.events.consumer.create_consumer()`. The alert-svc consumer crash (calling nonexistent function) MUST be fixed.

**Rationale:** 11 topics are being published to but never created; the alert-svc consumer references a nonexistent function. The event mesh will silently lose data.

### V. Service Architecture & API Consistency

All services follow a uniform layered architecture enforced by conventions.

- **Layered structure.** Every FastAPI-based service MUST follow: `app/api/v1/` (routes), `app/models/` (SQLAlchemy/Pydantic models), `app/services/` (business logic), `app/events/` (producers/consumers), `app/deps.py` (dependencies).
- **`/health`, `/ready`, `/metrics` on every service.** Health checks return 200, readiness checks verify DB/Kafka/Redis connectivity, metrics expose Prometheus-formatted output. Currently ZERO services mount `/metrics` -- this MUST be added.
- **Port scheme standardization.** All services MUST use the port numbers from `Dockerfile` (8001-8010). docker-compose.yml and Helm values MUST be reconciled to match -- see configuration drift analysis for the 3 incompatible schemes.
- **Import discipline.** Python files MUST NOT import from modules that don't exist. The dpe-svc `ctp.py` crash-on-import bug (importing `app.core.ctp` which doesn't exist) MUST never recur.
- **Frontend-backend contract alignment.** Every frontend API call in `apps/web/src/features/*/api.ts` MUST have a corresponding backend route. Named imports MUST match actual exports (e.g. `import { api }` requires `export const api`, not `export default api`).

**Rationale:** 3 port schemes, broken imports, and missing frontend routes make the system undeployable and unreachable.

### VI. Observability & Monitoring

Every service MUST be observable in both development and production.

- **`/metrics` is mandatory.** Every service MUST expose a Prometheus `/metrics` endpoint via `prometheus_fastapi_instrumentator`. Currently zero services do this.
- **Structured logging.** All services MUST use JSON-formatted logging via `ipe_shared.logging` with correlation IDs propagated from incoming requests.
- **Health checks.** Kubernetes readiness probes MUST use `/ready` (not `/health`). The Helm template currently uses `/health` -- this MUST be fixed.
- **Alerting.** Services MUST emit RED metrics (Rate, Errors, Duration) for key operations. alert-svc MUST have functioning consumers to process events.
- **Graceful degradation.** When downstream dependencies (DB, Kafka, Redis) are unavailable, services MUST surface this in `/ready` rather than crashing.

**Rationale:** Without `/metrics` on any service, there is zero operational visibility. Prometheus targets are incomplete and the alerting pipeline is broken.

## Security & Cross-Platform Constraints

- **Cross-platform.** Code MUST run on Linux and Windows. Shell scripts in `scripts/` MUST have PowerShell equivalents or be tested on both.
- **Secret management.** No hardcoded secrets in source code. The 3 instances of hardcoded DB passwords in migrations MUST use environment variables or secrets manager.
- **Input validation.** All API endpoints MUST validate inputs via Pydantic models. Path traversal, SQL injection, and XSS vectors MUST be rejected at the boundary.
- **Dependency scanning.** `pip-audit` or equivalent MUST pass on all Python services. The 59 known-vulnerability transitive dependencies MUST be addressed.
- **Formatting.** `ruff check`, `mypy --strict`, and `prettier` (frontend) MUST pass on all code.

## Development Workflow & Quality Gates

- **Branch naming.** `feat/<short-slug>`, `fix/<short-slug>`, `chore/<short-slug>`, `docs/<short-slug>`.
- **PR requirements.** Every PR MUST: pass CI (lint + test + type-check), include tests for new behavior, update API docs if routes change, and address any audit findings in the affected area.
- **Audit remediation tracking.** Issues from the V2 audit in `audit/v2/14-remediation-backlog.md` MUST be tracked in the project's issue tracker. P0 items block releases.
- **Pre-commit hooks.** AI agents MUST run `ruff check` and `mypy` before presenting code as complete.
- **Constitution compliance.** Every `/speckit.analyze` or `/speckit.implement` MUST verify compliance with these principles. Violations block merge.

## Governance

- **Authority.** Principles I-VI are binding gates. Violations MUST be resolved by changing the code, not by diluting a principle.
- **Amendments.** Changes to this document require PR with rationale and a SemVer version bump. Amendments MUST update the Sync Impact Report at the top of this file.
- **Versioning.** MAJOR = principled removal/redefinition; MINOR = new principle or materially expanded guidance; PATCH = clarifications.
- **Compliance review.** Every PR and review MUST verify compliance. Unjustified violations block merge.

**Version**: 1.0.0 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-06-20
