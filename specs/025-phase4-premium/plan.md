# Implementation Plan — Spec 025 Phase 4 Premium

**Date**: 2026-07-15  
**Constitution**: 1.2.8 (+ 1.3.0 absorb from Spec 024)  
**Wave**: MVP Wave 1 — agents A8–A12 + module pulse + autonomy + portal scaffold

## Approach

1. Extend existing services (do not invent finance-svc).
2. Add `dpe-svc/app/core/phase4/` for A8/A11/autonomy/pulse orchestration helpers.
3. Enrich procurement/quality/sustain/order APIs for A9/A10/A12/A8 portal.
4. Thin React pages under `features/intelligence` and `features/customer-portal`.
5. Register Spec 025 in feature.json / PRODUCT-STATUS; leave COM OPEN.

## Deferred (document, don’t fake)

- Full Digital Factory animation production polish
- Live Odoo quality.check / account.move sync
- Enterprise+ autonomous ERP write-back in production mode
- Phase 5 Planning Cockpit
- Ctrl+K contextual Copilot deep page wiring (Phase 3 morning brief remains)

## Phase 3 dependence

Consumes Spec 024: predictive, root-cause, batch, auction, orchestrator A1–A7, exceptions. Does not recreate.
