# Contributing to IPE

Thank you for contributing to the Intelligent Planning Engine platform.

---

## Development Environment

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker Desktop (for full stack)
- Node.js 20+ and pnpm (for frontend)
- PowerShell 7+ (Windows) or bash (Linux/macOS)

### Setup

```powershell
# Clone and enter repo
cd E:\AISOP\ipe

# Install shared tooling
make setup

# Start demo stack
.\scripts\rel-demo-stack.ps1
```

### Running Tests

```powershell
# Single service (unit tests, no integration)
cd services\cap-svc
uv run pytest tests/ -m "not integration" --cov=app --cov-report=term

# Full demo regression
python scripts\run_demo.py --all
```

---

## Coding Standards

- **Python:** Ruff formatter/linter; type hints on public APIs
- **FastAPI:** Pydantic models for all request/response bodies
- **Tests:** pytest; mark integration tests with `@pytest.mark.integration`
- **Migrations:** Alembic in `migrations/versions/`; never edit applied migrations
- **Secrets:** Never commit `.env`, `.kms_keys/`, or real credentials

---

## Pull Request Process

1. Create a feature branch from `master`
2. Write tests for new behavior
3. Ensure `pytest` passes with coverage gate met
4. Update relevant docs in `docs/`
5. Open PR with summary and test plan

---

## Speckit Workflow

Feature specs live under `specs/`. Active program: `specs/005-ipe-program-status/`.

Before merging release work:

- Update `READINESS.md` scores
- Link evidence in `specs/002-release-stabilization-gates/evidence/`
- Run demo 20/20 if touching API contracts

---

## Commit Message Format

```
<type>(<scope>): <description>

Types: feat, fix, docs, test, chore, release
Examples:
  feat(cap-svc): add network optimize endpoint
  docs: update JWT rotation runbook
  test: coverage push for mat-svc netting
```
