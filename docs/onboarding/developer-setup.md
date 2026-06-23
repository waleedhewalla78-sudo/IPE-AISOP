# Developer Setup

## Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm 9+
- Docker Desktop
- uv (Python package manager)

## Quick Start

```bash
git clone <repo> && cd ipe
cp .env.template .env   # Linux/macOS — edit secrets before running tests
make setup
make docker-up
make migrate
make dev
```

### Environment variables

Copy `ipe/.env.template` to `ipe/.env` and set at minimum:

| Variable | Purpose |
|----------|---------|
| `IPE_JWT_SECRET_KEY` | Required for auth unit tests and local JWT signing |
| `IPE_DATABASE_URL` | PostgreSQL async connection string |
| `IPE_REDIS_URL` | Redis (`redis://localhost:6380/0` when using docker-compose) |
| `IPE_KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap (`localhost:9092`) |
| `IPE_ANTHROPIC_API_KEY` | Optional — NLP/Copilot falls back without it |

On Windows (PowerShell):

```powershell
Copy-Item .env.template .env
# Edit .env, then:
$env:IPE_JWT_SECRET_KEY = "dev-jwt-secret-change-in-production-min-32-chars"
.\scripts\run-all-tests.ps1
```

## Testing

```bash
make test         # All tests (Linux/macOS)
make lint         # All linting
cd apps/web && pnpm test -- --run  # Frontend tests only
```

Windows: `.\scripts\run-all-tests.ps1` runs all Python service suites plus frontend tests.
