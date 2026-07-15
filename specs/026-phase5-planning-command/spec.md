# Feature Specification: Phase 5 Planning & Command Deep

**Feature Branch**: `026-phase5-planning-command`

**Created**: 2026-07-15

**Status**: Active — Wave 1 eng COMPLETE

**Input**: `IPE-Phase5-Planning-Command-Deep.md`. Build Planning Center working surface (cockpit, MPS, MRP, ATP/CTP, leveling) and Command Center nerve center (ops live, war room, shift handover, action tracker). Depends on Spec 024/025.

**Out of scope**: Live Odoo PH1-02, G-R2-04 Arabic COM, OQ-7, collaborative multi-user conflict locking full UI, WhatsApp Comms Hub.

---

## User Scenarios

### US1 — Planning Cockpit (P1)
Planner opens cockpit and sees plan health + attention queue.

### US2 — MPS / MRP / Promise (P1)
Planner runs MPS, explodes MRP, promises ATP/CTP order.

### US3 — Ops Live + War Room (P1)
Ops views live WC utilisation; activates war room on incident.

### US4 — Shift handover + actions (P2)
Structured handover + action tracker create/complete.

---

## Requirements
- FR-001 Planning cockpit API
- FR-002 MPS builder with draft MOs
- FR-003 MRP explosion with PO flags
- FR-004 ATP/CTP promise
- FR-005 Production leveling
- FR-006 Ops dashboard + war room
- FR-007 Shift handover + action tracker
- FR-008 UI cockpit + ops-live pages
- FR-009 PHASE5 report + PRODUCT-STATUS honesty

## Success Criteria
- SC-001 Phase 5 unit tests GREEN
- SC-002 APIs under `/api/v1/planning-command/*`
- SC-003 COM blockers remain OPEN
