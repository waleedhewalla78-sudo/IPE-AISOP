# Feature Specification: IPE v8.1.0 Phase 2 Expansion

**Feature Branch**: `008-v8-phase2-expansion`  
**Created**: 2026-06-27  
**Status**: Implemented (MVP)  
**Input**: SAP Gap Analysis Phase 2 — U4, U5, U6

---

## What We Build

| Stream | Deliverable | Service | Port |
|--------|-------------|---------|------|
| **U4** | Multi-echelon supply orchestration | `supply-svc` | 8060 |
| **U5** | Customer order management + ATP/CTP | `order-svc` | 8070 |
| **U6** | Equipment intelligence + predictive maintenance dashboard | `equipment-svc` | **8061** (8080 reserved for Kafka UI) |

### UI

- **Supply Chain Hub**: Supply Planning, Orders (+ existing Tariff/SCN/Inventory)
- **Command Center**: Equipment Health tab

---

## Requirements

### FR-P2-01 Supply network
Expose plants, transfer lanes, inventory positions, generate replenishment plan.

### FR-P2-02 Order lifecycle
Create/list customer orders; ATP/CTP promise; exception queue.

### FR-P2-03 Equipment intelligence
Fleet health from telemetry; RUL predictions; maintenance schedule + critical alerts.

### FR-P2-04 Integration
Orchestrate existing mat/scn/cap IoT without duplicating solvers.

---

## User Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-P2-1 | Planner generates multi-echelon supply plan | Network + transfers returned |
| US-P2-2 | Planner promises customer order | ATP or CTP dates persisted |
| US-P2-3 | Supervisor views equipment health | Fleet list + RUL alerts |
| US-P2-4 | cap-svc IoT telemetry still works | No breaking change to `/iot/telemetry` |

---

## Out of Scope

- Full ERP order-to-cash
- Stochastic multi-echelon optimizer (Phase 2.1)
- Moving cap-svc IoT ingest to equipment-svc exclusively
