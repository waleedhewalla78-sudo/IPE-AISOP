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
make setup
make docker-up
make migrate
make dev
```

## Testing

```bash
make test         # All tests
make lint         # All linting
cd apps/web && pnpm test -- --run  # Frontend tests only
```
