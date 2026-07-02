# Release 1 + Release 2 Demo Status — Star Trans / Odoo 19

**Date:** 2026-07-02  
**R1 integration score:** **13/13 PASS** (re-run after `docker compose` rebuild: re-seed + post-sync MDR boost)  
**R2 commercial score:** **5/5 PASS** — [release2-demo.txt](./release2-demo.txt)  
**Full platform score:** **13/32 PASS**, **19 SKIP** (hybrid-only), **0 FAIL** (bugs)  
**Stack:** 9 services (db, redis, kong, dpe-svc, fea-svc, cap-svc, res-svc, connector, web-ui) + Odoo 19 live  
**Note:** 32/32 full platform demo requires hybrid stack (22+ services) — see [HYBRID-STACK-GAP-ANALYSIS.md](./HYBRID-STACK-GAP-ANALYSIS.md)

**Evidence:**
- Integration: [release1-integration-demo-final.txt](./release1-integration-demo-final.txt)
- Full platform: [startrans-full-demo-final.txt](./startrans-full-demo-final.txt)
- Raw step responses: [release1-step-responses.json](./release1-step-responses.json)

---

## Integration path (13 steps)

| Step | Checkpoint | Status | Notes |
|------|------------|--------|-------|
| 1 | IPE login | PASS | Ahmed@nour / admin |
| 2 | Odoo connection | PASS | Odoo 19.0, uid=2 |
| 3 | Odoo config (vault) | PASS | KMS encrypted (`odoo_password_enc`) |
| 4 | Odoo → CDM sync | PASS | 70 products, 2 MOs updated/rescored |
| 5 | Sync status audit | PASS | Per-entity counts in `cdm_sync_run.entity_counts` |
| 6 | Data quality | PASS | 0 flags |
| 7 | Feasibility queue | PASS | 12 MOs (10 hero + 2 Odoo), scores 45–95% |
| 8 | Feasibility KPIs | PASS | avg 76.2, 1 at risk |
| 9 | Resolution scenarios | PASS | 16 scenarios via Kong → res-svc:8005 |
| 10 | OR-Tools schedule | PASS | MDR 100%, 8 ops scheduled |
| 11 | Schedule → Odoo writeback | PASS | 2 MOs activated (direct ERP mode) |
| 12 | OTD baseline | PASS | API reachable |
| 13 | ROI metrics | PASS | API reachable |

---

## Full platform (32 checkpoints on Release 1 stack)

| # | Checkpoint | Status | Notes |
|---|------------|--------|-------|
| 0 | Login | PASS | |
| 1 | Control Tower queue | PASS | 12 MOs |
| 2 | Control Tower KPIs | PASS | |
| 3 | Resolution scenarios | PASS | res-svc |
| 4 | Schedule Gantt | PASS | cap-svc + MDR gate |
| 5 | Shop Floor work orders | SKIP | requires del-svc — hybrid only |
| 6 | SCN Portal scorecards | SKIP | requires scn-svc — hybrid only |
| 7 | Executive delay breakdown | PASS | dpe-svc analytics |
| 8 | Executive OTD summary | PASS | |
| 9 | Dashboard alerts | PASS | dpe-svc dashboard |
| 10 | Copilot FG stock | SKIP | requires nlp-svc + Ollama — hybrid only |
| 11 | Copilot at-risk orders | SKIP | requires nlp-svc — hybrid only |
| 12 | AI Trust scores | SKIP | requires rec-svc — hybrid only |
| 13 | Admin tenant config | PASS | |
| 14 | Inventory summary | SKIP | requires mat-svc — hybrid only |
| 15 | Schedule persist + approve | PASS | |
| 17 | Margin-aware priority | PASS | dpe-svc demand + cap-svc |
| 18 | Tariff shock | PASS | dpe-svc |
| 19 | CPM cascade | PASS | cap-svc |
| 20 | IoT telemetry + Cost of Chaos | SKIP | requires alert-svc / iot routes — hybrid only |
| 21 | Demand forecast | SKIP | requires demand-svc — hybrid only |
| 22 | Demand sense cycle | SKIP | requires demand-svc — hybrid only |
| 23 | Scenario sandbox | SKIP | requires scenario-svc — hybrid only |
| 24 | Scenario simulate | SKIP | requires scenario-svc — hybrid only |
| 25 | Supply network | SKIP | requires supply-svc — hybrid only |
| 26 | Customer orders | SKIP | requires order-svc — hybrid only |
| 27 | Equipment fleet | SKIP | requires equipment-svc — hybrid only |
| 28 | Design AI materials | SKIP | requires material-svc — hybrid only |
| 29 | Procurement spend | SKIP | requires procurement-svc — hybrid only |
| 30 | Copilot role agents | SKIP | requires nlp-svc — hybrid only |
| 31 | Sustainability dashboard | SKIP | requires sustain-svc — hybrid only |
| 32 | Quality intelligence | SKIP | requires quality-svc — hybrid only |

---

## MDR and seed data (post-fix)

| Metric | Value |
|--------|-------|
| MDR composite score | **100%** (threshold 70%) |
| BOMs (tenant) | 7 (3 hero + Odoo + Office Combo) |
| Hero BOM component lines | 20 |
| Lead time coverage | 100% of products |
| Inventory coverage | 100% of products |
| Routing MO coverage | 100% |

Seed script: `scripts/seed-startrans-demo.ps1` (overlay + MDR boost SQL)

---

## Sync entity coverage

Full sync (`POST /api/v1/sync/run {"entity":"all"}`) covers:

| Entity | Sync method |
|--------|-------------|
| products | `sync_products` |
| work_centers | `sync_work_centers` |
| customers | `sync_customers` |
| suppliers | `sync_suppliers` |
| boms + bom_details | `sync_boms` + `sync_bom_details` |
| inventory | `sync_inventory` |
| manufacturing_orders | `sync_manufacturing_orders` |
| demands | `sync_demands` |
| supply | `sync_supply` |

IPE-native seeded BOMs (erp_source_id `BOM-*`, `ST-*`) are **preserved** on sync — Odoo sync only upserts by Odoo erp_source_id and does not delete IPE-native records.

---

## Fixes applied (2026-06-30)

1. **Kong:** `/api/v1/resolution` routed to `res-svc:8005` (was incorrectly on dpe-svc)
2. **Compose:** `res-svc` added to `docker-compose.release1.yml`
3. **MDR seed:** `scripts/seed-startrans-mdr-boost.sql` — transformer BOM lines, inventory, lead times, routing
4. **Demo script:** retries, post-sync pause, JSON response capture, PASS/FAIL/SKIP summary

---

## Release 2 (014) checkpoints

| Step | Checkpoint | Status | Notes |
|------|------------|--------|-------|
| 1 | OTD baseline API | PASS | `GET /api/v1/analytics/otd-baseline` |
| 2 | ROI metrics API | PASS | `GET /api/v1/analytics/roi-metrics` |
| 3 | Auto-propose after sync | PASS | connector → res-svc when score &lt; 75% |
| 4 | Resolution scenarios | PASS | ≥1 proposed scenarios |
| 5 | Copilot Lite | PASS | `POST /api/v1/planner-assist/query` |

**New UI:** Outcomes tab (Command Center), Planner Copilot Lite panel (Control Tower)  
**New APIs:** planner-assist, `POST /api/v1/erp/odoo/resolution-notify` (feature flag off by default)  
**Script:** `scripts/run-release2-demo.ps1`  
**Spec:** `specs/014-release2-growth/`

---

## Enterprise program (015)

Strategic roadmap imported to `docs/strategy/IPE_Enterprise_Deployment_Roadmap.md`.  
Program status: `docs/strategy/ENTERPRISE-PROGRAM-STATUS.md`  
Speckit: `specs/015-enterprise-production-readiness/` (Phases 0–4, 36 weeks)
