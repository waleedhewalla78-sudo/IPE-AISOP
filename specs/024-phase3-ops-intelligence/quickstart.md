# Quickstart — Spec 024 Ops Phase 3

## Prerequisites

```powershell
cd E:\AISOP\ipe
copy .env.template .env   # if missing
# Ensure IPE_DATABASE_URL, IPE_JWT_SECRET_KEY set
```

## Apply migrations (when DB up)

```powershell
cd E:\AISOP\ipe
# use project alembic entrypoint as documented in README / Makefile
alembic -c migrations/alembic.ini upgrade head
# head should include 059
```

## Run unit tests (no Docker required for core scorers)

```powershell
cd E:\AISOP\ipe
python -m pytest services/fea-svc/tests/test_predictive_scorer.py services/fea-svc/tests/test_root_cause_analyzer.py -q
python -m pytest services/cap-svc/tests/test_smart_batcher.py services/cap-svc/tests/test_capacity_auction.py -q
python -m pytest services/dpe-svc/tests/test_agent_orchestrator.py -q
```

## Manual API smoke (stack up)

```powershell
# After fea-svc up with JWT:
# GET /api/v1/feasibility/predict/{mo_id}
# GET /api/v1/feasibility/root-cause/{mo_id}
```

## Honesty checks

- Do not claim PH1-02 / G-R2-04 / OQ-7 closed.
- Do not push `v9.1.0-r2`.
