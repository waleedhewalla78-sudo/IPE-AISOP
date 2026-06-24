.PHONY: help setup dev test lint format migrate seed clean docker-up docker-down perf-test perf-k6 perf-k6-200 r4-verify e2e-test integration-e2e integration-unit shadow-validate docker-test-up docker-test-down mock-odoo-build launch-verify

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## One-time dev environment setup
	bash scripts/setup-dev.sh

dev: docker-up ## Start full development stack
	@echo "Starting services..."
	cd services/shared && uv run python -m pytest --co -q 2>/dev/null && echo "Shared lib OK"
	turbo run dev

docker-up: ## Start Docker infrastructure
	docker compose -f infrastructure/docker/docker-compose.yml up -d
	@echo "Waiting for Postgres..."
	@until docker compose -f infrastructure/docker/docker-compose.yml exec -T db pg_isready; do sleep 1; done
	@echo "Infrastructure ready."

docker-down: ## Stop Docker infrastructure
	docker compose -f infrastructure/docker/docker-compose.yml down

migrate: ## Run database migrations
	cd migrations && alembic upgrade head

seed: ## Load seed data (shell + Python dev data)
	bash scripts/seed-data.sh
	cd services/shared && uv run python ../../scripts/seed_dev_data.py

perf-test: ## Run Locust performance test (50 users, 2 min)
	docker run --rm --network=host \
		-v $(PWD)/tests/performance:/mnt/locust \
		-e LOCUST_LOCUSTFILE=/mnt/locust/locustfile.py \
		-e LOCUST_HOST=http://localhost:8000 \
		-e LOCUST_USERS=50 \
		-e LOCUST_SPAWN_RATE=5 \
		-e LOCUST_RUN_TIME=2m \
		-e LOCUST_HEADLESS=true \
		-e LOCUST_CSV=/mnt/locust/report \
		locustio/locust

perf-k6: ## Run k6 performance load test (smoke + load scenarios)
	k6 run tests/performance/k6/load-test.js

perf-k6-200: ## Run k6 200 VU re-cert (R4 SC-012 gate)
	k6 run tests/performance/k6/load-test-200vu.js

r4-verify: ## Run R4 production hardening checks (SAP/D365/Airflow)
	bash scripts/test-sap-sandbox.sh
	bash scripts/test-d365-sandbox.sh
	bash scripts/verify-airflow.sh

e2e-test: ## Run E2E critical path validation
	uv run python scripts/e2e/critical_path_test.py

launch-verify: ## Run backend test suites across all services (Windows: .\scripts\launch-verify.ps1)
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/launch-verify.ps1

full-cycle-heavy: ## Full product validation: unit tests + demo + mass data (Windows)
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-full-cycle-heavy.ps1

test: ## Run all tests
	cd services/shared && uv run pytest -v --cov=ipe_shared --cov-report=term-missing
	@for svc in dpe-svc mat-svc cap-svc fea-svc res-svc del-svc nlp-svc rec-svc alert-svc; do \
		echo "Testing $$svc..."; \
		cd services/$$svc && uv run pytest -v --cov=app --cov-report=term-missing; \
		cd ../..; \
	done
	cd apps/web && pnpm test -- --run

integration-e2e: docker-test-up seed ## Run integration + E2E tests against test stack
	uv run python scripts/e2e/critical_path_test.py
	uv run python tests/integration/test_rbac_tenant_isolation.py

integration-unit: ## Run integration unit tests (Redis/Kafka/WS mocks, auto-skip if infra unavailable)
	cd services/shared && uv run pytest tests/integration/ -v --tb=short
	uv run pytest tests/integration/test_idempotency.py tests/integration/test_consumer_rls.py tests/integration/test_mesh_tenant_isolation.py tests/integration/test_consumer_robustness.py tests/integration/test_ws_tenant_isolation.py tests/integration/test_ws_security.py -v --tb=short -m integration

shadow-validate: ## Run shadow mode E2E validation pipeline
	bash scripts/e2e/run_shadow_validation.sh

docker-test-up: ## Start test infrastructure stack
	docker compose -f infrastructure/docker/docker-compose.test.yml up -d
	@echo "Waiting for Postgres..."
	@until docker compose -f infrastructure/docker/docker-compose.test.yml exec -T postgres pg_isready; do sleep 1; done
	@echo "Test infrastructure ready."

docker-test-down: ## Stop test infrastructure stack
	docker compose -f infrastructure/docker/docker-compose.test.yml down -v

mock-odoo-build: ## Build mock-odoo-api Docker image
	docker build -t ipe-mock-odoo:latest services/mock-odoo-api

lint: ## Lint all code
	cd services/shared && uv run ruff check .
	@for svc in dpe-svc mat-svc cap-svc fea-svc res-svc del-svc nlp-svc rec-svc alert-svc; do \
		cd services/$$svc && uv run ruff check .; cd ../..; \
	done
	cd apps/web && pnpm lint

format: ## Format all code
	cd services/shared && uv run ruff format .
	@for svc in dpe-svc mat-svc cap-svc fea-svc res-svc del-svc nlp-svc rec-svc alert-svc; do \
		cd services/$$svc && uv run ruff format .; cd ../..; \
	done
	cd apps/web && pnpm format

clean: ## Remove all build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
