# Sprint S10 Report — Supply Chain Intelligence

**Sprint**: S10  
**Date**: 2026-07-10  
**Status**: ✅ Complete  
**Spec**: `018-phase2-release2`

---

## Deliverables

| ID | Deliverable | Status |
|----|-------------|--------|
| S10-01 | Supplier risk API | ✅ |
| S10-02 | Inventory ABC / slow-moving | ✅ |
| S10-03 | Copilot SC tools | ✅ |
| S10-04 | Tests | ✅ |
| S10-05 | Migration `041_cdm_supplier_score` | ✅ |

---

## Endpoints (mat-svc)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/supply-chain/supplier-risk` | admin, planner, manager, procurement | Supplier reliability + risk tiers (`?persist=true`) |
| GET | `/api/v1/supply-chain/inventory-abc` | admin, planner, manager, procurement | ABC classification by on-hand share |
| GET | `/api/v1/supply-chain/slow-moving` | admin, planner, manager, procurement | SKUs with no recent receipts (`?stale_days=90`) |
| GET | `/api/v1/supply-chain/reorder-suggestions` | admin, planner, manager, procurement | Purchased materials below reorder point |

---

## Copilot Tools (nlp-svc)

| Tool | Description |
|------|-------------|
| `get_supplier_risk` | Proxy to mat-svc supplier risk |
| `get_inventory_abc` | ABC inventory classification |
| `get_slow_moving_inventory` | Slow-moving SKU list |
| `get_reorder_suggestions` | Reorder point suggestions |

---

## Migration

| ID | File | Purpose |
|----|------|---------|
| **041** | `migrations/versions/041_cdm_supplier_score.py` | `cdm_supplier_score` history with RLS |

---

## Tests

| File | Result |
|------|--------|
| `services/mat-svc/tests/test_supply_chain_intel.py` | **3/3 PASS** |
| `services/nlp-svc/tests/test_sop_reports.py` (tool coverage) | **includes get_supplier_risk** |

---

## Gate

Supply chain APIs return risk, ABC, slow-moving, and reorder data. Copilot tools wired for planner queries.
