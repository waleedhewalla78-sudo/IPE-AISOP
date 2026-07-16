# OPEN Items — Program (honest tracker)

**Updated:** 2026-07-16  
**Do not auto-close COM items.**

## Commercial / Human (OPEN)

| ID | Item | Owner | Blocks |
|----|------|-------|--------|
| OQ-7 | Licence / implementation price | Waleed | SOW send |
| OQ-1 | Odoo 17 vs 19 confirm | Star Trans IT | Staging clarity |
| PH1-01 | SOW send | COM | Depends OQ-7 |
| PH1-02 | Live Odoo staging | Ops / Customer IT | Live sync UAT |
| G-R2-04 | Arabic native QA sign-off | Native reviewer | `v9.1.1-r2` tag |
| OQ-9 | Gate 11 waiver signatures | Waleed | Formal waiver |

## Engineering residuals (OPEN)

| Item | Notes |
|------|-------|
| Spec 022 #70/#72 Docker validate | Re-run when R2 stack healthy |
| Spec 024 live Kong smoke of P3 APIs | Unit gate green; live re-verify optional |
| Spec 025 Digital Factory polish | Shop-floor linked only |
| Spec 025 live Odoo quality/finance/PO | Blocked on PH1-02 |
| Spec 026 collaborative planning conflict UI | Deferred beyond Wave 1 |
| Spec 026 WhatsApp / Comms Hub | Deferred |
| Spec 026 alert inbox SLA UI | Partial (ops live alerts only) |
| Spec 026 MPS/MRP persistence migrations | Wave 1 request-driven |
| Kong `/api/v1/enterprise/*` route | Missing route object → Phase 6 `/enterprise/*` 404 via Kong (200 direct-to-dpe-svc); add Kong route to expose |
| Spec 028 Phase 7 Digital Gemba live IoT/MES | STUB (`iot_live=false`) — PH1-02 |
| Spec 028 Phase 7 operator tablet UI (Standard Work) | Minimal Wave 1 |
| Spec 028 Phase 7 Andon DB persistence + notifications | Table 067 exists; Wave 1 board in-memory |
| Spec 028 Phase 7 S&OP interactive stage-gate | Deferred (governance modelled as config; was E2E-SOP-03 BLOCKED) |
| Spec 028 Phase 7 monetary net-saving in leveling | Deferred (was P5-LEV-02 SKIP) |

## Tags

| Tag | Status |
|-----|--------|
| v9.1.1-r2 | HOLD until G-R2-04 |
| v9.1.0-r2 | **Do not push** (stale) |

## Completed (eng)

| Item | Spec |
|------|------|
| Ops Phase 3 Wave 1 cores | 024 |
| Phase 4 Premium Wave 1 (A8–A12, M1–M6, autonomy, portal) | 025 |
| Phase 5 Planning-Command Wave 1 (cockpit/MPS/MRP/ops) | 026 |
| Phase 6 Enterprise Agentic Wave 1 (A13–A17, M7–M9) | 027 |
| Phase 7 Deep Planning Wave 1 (§1–§6, 5 disciplines) | 028 |
