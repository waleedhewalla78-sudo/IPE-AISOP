# Implementation Plan: Phase 6 Enterprise Agentic Platform

**Feature**: `027-phase6-enterprise-agentic` · **Constitution**: 1.3.0 → 1.4.0 (Principle X — Agentic Autonomy Governance)

## Approach

Build on existing patterns; do NOT recreate. Mirror the `phase4`/`phase5` core+API+test structure inside `dpe-svc`.

| Layer | Location | Pattern reused |
|-------|----------|----------------|
| Cores | `app/core/phase6/` | `app/core/phase4`, `app/core/phase5` (pure-logic dataclass/dict) |
| API | `app/api/v1/phase6_enterprise.py` (`/enterprise` prefix) | `phase4_premium.py`, `phase5_planning.py` (APIResponse, tenant header) |
| Router | `app/api/v1/router.py` | append include_router |
| Migrations | `migrations/versions/060–063` | `059_cdm_batch_group.py` RLS loop |
| Frontend | `features/intelligence/EnterpriseCommandPages.tsx` + hub tabs | `PlanningCockpitPage.tsx`, `IntelligenceHub.tsx` |
| Tests | `tests/test_phase6_*.py` | `test_phase4_premium.py`, `test_phase5_planning.py` |

## Agent → capability → reuse map

- **A13 Commercial** (`commercial_intel.py`): `optimize_price`, `analyze_deal_profitability`, `check_contract_compliance` — margin conventions from A11 `finance_intel`.
- **A14 Analytics** (`analytics_intel.py`): `detect_trend`, `detect_anomaly` (z-score), `predict_next` (linreg), `generate_insights`, `build_predictions`.
- **A15 Procurement Exec** (`procurement_exec.py`): `three_way_match`, `confirm_receipt`.
- **A16 Shop Floor** (`shop_floor.py`): `build_work_instructions`, `track_time`, `production_progress` (IoT stub).
- **A17 Orchestrator** (`orchestrator.py`): `RESOLUTION_HIERARCHY`, `resolve_conflict`, `enforce_policies` (6 policies), `cascade_event`, `orchestrate_atp` — reuses `promise_order` (Phase 5), `evaluate_decision_pnl` (Phase 4), `optimize_price` (A13).
- **Odoo Accounting** (`odoo_accounting.py`): `OdooAccountingConnector` scaffold, mock source, `is_live=False` (PH1-02).

## Governance (doc §4.3)

Levels 1 Autonomous / 2 Supervised / 3 Approved / 4 Escalated encoded in orchestrator decisions.

## Honesty guardrails

- Every live-integration capability returns `live: false` + `blocker` string.
- No COM blocker auto-closed. No tag application. No invented signatures.

## Waves

- **6A** (priority): A13, A14, M7, M8, Odoo Accounting scaffold — DONE
- **6B** (time-permitting): A15, A16, M9, minimal operator UI, IoT stub — DONE
- **6C** (time-permitting): A17 hierarchy + 6 policies + cascade + cross-functional ATP — DONE
- **6D**: deferred (tuning/cert/multi-plant)
