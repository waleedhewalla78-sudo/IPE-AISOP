# 08 — Test Quality Assessment (V2 Audit)

**Generated**: 2026-06-20 | **Methodology**: Evaluate test effectiveness by mapping tests to critical paths.

## Test Execution Results

Tests could NOT be executed due to:
- Venv destroyed and recreated without dev dependencies (ruff, pytest)
- `uv run --directory services/shared pytest` fails — pytest not in dependencies
- Shared pyproject.toml has no `[dependency-groups]` for dev tools
- Pipeline would need `uv sync --dev` or `--group dev` which isn't configured

**Status**: CANNOT_VERIFY (test execution blocked by missing dev tooling config)

## Test Inventory (from code inspection)

| Layer | Files | Approx. Count | Location |
|-------|-------|---------------|----------|
| Unit tests (Python) | 77 | ~580 | `services/*/tests/` |
| Shared library tests | 18 | ~126 | `services/shared/tests/` |
| Integration tests | 8 | ~49 | `tests/integration/` |
| Frontend unit (Vitest) | 10 | 17 | `apps/web/tests/` |
| Playwright E2E | 1 | 7 | `apps/web/e2e/` |
| Python E2E script | 1 | 5 steps | `scripts/e2e/critical_path_test.py` |
| k6 performance | 1 | 5 thresholds | `tests/performance/k6/` |
| Locust performance | 1 | 2 user classes | `tests/performance/locustfile.py` |
| **Total** | **117** | **~785** | |

## Coverage Configuration Warning

All service `pyproject.toml` files have:
```ini
[tool.coverage.report]
fail_under = 40  # Temporarily lowered to 40%
```

This means tests passing at 40% coverage are declared "passing." The previous threshold was 85%.

## Critical Flow Test Coverage

| Business Flow | Unit | Integration | E2E | Perf | Status |
|---------------|------|-------------|-----|------|--------|
| Demand→Classify | ✅ dpe-svc/test_priority.py | ✅ test_sprint2_e2e.py | ✅ critical_path_test.py | ❌ | PARTIALLY TESTED |
| Classify→Material ATP | ✅ mat-svc/test_atp_*.py | ✅ test_sprint2_e2e.py | ✅ | ❌ | PARTIALLY TESTED |
| ATP→Capacity Schedule | ✅ cap-svc/test_api_capacity.py | ✅ test_sprint2_e2e.py | ✅ | ❌ | PARTIALLY TESTED |
| Schedule→Feasibility | ✅ fea-svc/test_*.py | ✅ test_sprint2_e2e.py | ✅ | ❌ | PARTIALLY TESTED |
| Feasibility→Resolution | ✅ res-svc/test_strategy.py | ✅ test_sprint2_e2e.py | ✅ | ❌ | PARTIALLY TESTED |
| Resolution→Odoo Export | ❌ | ❌ | ❌ | ❌ | UNTESTED |
| Copilot Chat | ✅ nlp-svc/test_core.py | ❌ | ❌ | ❌ | IMPLEMENTED_NOT_TESTED |
| Alert→Notification | ✅ alert-svc/test_*.py | ❌ | ❌ | ❌ | IMPLEMENTED_NOT_TESTED |
| Quality Events | ✅ del-svc/test_quality_processor.py | ❌ | ❌ | ❌ | IMPLEMENTED_NOT_TESTED |
| Multi-Plant Network | ✅ cap-svc/test_network_optimizer.py | ❌ | ❌ | ❌ | IMPLEMENTED_NOT_TESTED |
| Green Schedule | ✅ cap-svc/test_green_scheduler.py | ❌ | ❌ | ❌ | IMPLEMENTED_NOT_TESTED |
| CTP Engine | ✅ mat-svc/test_ctp_solver.py | ❌ | ❌ | ❌ | IMPLEMENTED_NOT_TESTED |
| Financial Projection | ✅ dpe-svc/test_financial_projection.py | ❌ | ❌ | ❌ | IMPLEMENTED_NOT_TESTED |

## Test Quality Observations

### Strengths
- Broad unit test coverage across all services
- Integration tests cover the core 6-service pipeline
- Playwright tests include aXe accessibility + 3 viewports
- k6 tests include Prometheus remote write
- Idempotency, RLS, tenant isolation tested via integration stubs

### Weaknesses
1. **40% coverage threshold masks gaps** — services could have 60% "untested" code and still "pass"
2. **8 integration tests skipped** — require infrastructure not available in CI
3. **Zero performance regression testing in CI** — k6 is manual only
4. **No chaos/fuzz/security testing** — no adversarial test patterns
5. **Playwright coverage is file-level only** — `critical-path.spec.ts` has only 7 tests across entire frontend
6. **mock-odoo-api has ZERO tests** — only empty `__init__.py` in tests/
7. **No boundary/injection/saturation tests** for OR-Tools CP-SAT solver
8. **E2E test only covers 5-step critical path** — no error-path, concurrent-user, or data-corruption scenarios
9. **Frontend tests are render-only** — 17 tests, mostly checking page titles render. Zero interaction/state/error tests
10. **Cannot execute tests** — dev tooling not configured for `uv run pytest` from workspace

## Test Effectiveness Score

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Unit test breadth | 75 | Most services have reasonable unit test files |
| Unit test depth | 40 | 40% coverage threshold = most code paths untested |
| Integration test coverage | 55 | Core pipeline tested, 8 skipped |
| E2E test coverage | 35 | 7 Playwright tests + 5-step Python E2E |
| Performance testing | 40 | k6 exists but manual, no CI integration |
| Security testing | 10 | Zero security-specific tests |
| Test execution reliability | 30 | Cannot execute without infra |
| **Overall** | **41/100** | Testing maturity is LOW for production |

---

# 12 — Configuration Drift Analysis (V2 Audit)

**Generated**: 2026-06-20

## Port Drift: 3 Incompatible Schemes

| Service | Dockerfile EXPOSE | Compose Maps | K8s Individual | Helm values | Prometheus | README |
|---------|-------------------|--------------|----------------|-------------|------------|--------|
| dpe-svc | 8001 | 8002 | 8001 | 8002 | 8001 | 8001 |
| mat-svc | 8002 | 8003 | 8002 | 8003 | 8002 | 8002 |
| cap-svc | 8003 | 8004 | 8003 | 8004 | 8003 | 8003 |
| fea-svc | 8004 | 8006 | 8004 | 8005 | 8004 | 8004 |
| res-svc | 8005 | 8005 | 8005 | 8006 | 8005 | 8005 |
| del-svc | 8006 | 8007 | 8006 | 8007 | 8006 | 8006 |
| nlp-svc | 8007 | 8009 | 8007 | 8008 | 8007 | 8007 |
| rec-svc | 8008 | 8008 | — | 8009 | 8008 | 8008 |
| alert-svc | 8010 | 8010 | — | 8010 | **MISSING** | 8010 |
| connector | 8009 | **MISSING** | — | 8001 | 8009 | 8009 |

**Result**: 4 service ports are inconsistent. Compose ports differ from all other layers for half the services.

## Environment Variable Naming Drift

| Variable | .env.example | docker-compose.yml |
|----------|-------------|-------------------|
| Database URL | `IPE_DATABASE_URL` | `DATABASE_URL` (no IPE_ prefix) |
| Kafka Servers | `IPE_KAFKA_BOOTSTRAP_SERVERS` | `KAFKA_BOOTSTRAP_SERVERS` (no IPE_ prefix) |
| Redis URL | `IPE_REDIS_URL` | `REDIS_URL` (no IPE_ prefix) |
| Service URLs | `IPE_DPE_SVC_URL` | `DPE_SVC_URL` (no IPE_ prefix + port mismatch) |

**Result**: Compose uses non-prefixed names; .env.example uses `IPE_` prefix. The Settings class in ipe_shared must handle both conventions, or one side must be fixed.

## Helm Template Issues

| Issue | File | Line |
|-------|------|------|
| Resources indentation off-by-1 | `_service.tpl` | 40 |
| Readiness probe uses `/health` instead of `/ready` | `_service.tpl` | ~65 |
| ENVIRONMENT var uses no `IPE_` prefix | `_service.tpl` | env section |

## Composer Service Gaps

| Service | In docker-compose.yml | In docker-compose.test.yml |
|---------|-----------------------|--------------------------|
| dpe-svc | ✅ | ✅ |
| mat-svc | ✅ | ✅ |
| cap-svc | ✅ | ✅ |
| fea-svc | ✅ | ✅ |
| res-svc | ✅ | ✅ |
| del-svc | ✅ | ✅ |
| nlp-svc | ✅ | ✅ |
| rec-svc | ✅ | ✅ |
| alert-svc | ✅ | ✅ |
| connector | **MISSING** | **MISSING** |
| mock-odoo-api | **MISSING** | ✅ (test only) |
