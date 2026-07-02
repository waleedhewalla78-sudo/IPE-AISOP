# Analyze — 012 Star Trans Client Demo

**Date**: 2026-06-29  
**Cross-artifact scope**: spec ↔ seed scripts ↔ demo runner ↔ guides ↔ v8.2.0 platform

---

## Coverage Matrix

| Artifact | Star Trans need | Current state | Gap | Action |
|----------|-----------------|---------------|-----|--------|
| `seed-data.sh` | Master products/WCs | Generic Widget A | Names | Overlay UPDATE |
| `seed-demo-client.sql` | MO graph 10+8 scenarios | MO-DEMO-* | IDs + copy | Overlay UPDATE |
| `034_demo_supply_network_seed.py` | Multi-plant | DEMO-HAMBURG etc. | Display names | Overlay UPDATE |
| `run-full-demo.ps1` | 32/32 validation | Hardcodes Widget A | Profile param | `-Profile startrans` |
| `ProjectPlanUpload` | Live upload | ✅ Exists | Sample file | CSV + schema doc |
| `prepare-demo.ps1` | Stack + Ollama | ✅ | Star Trans entry | `prepare-startrans-demo.ps1` |
| `FULL-DEMO-GUIDE.md` | Generic 45–60 min | ✅ | Client guide | `STARTRANS-DEMO-GUIDE.md` |
| Copilot / nlp-svc | Live queries | Reads DB names | Pre-run | Overlay + cheat sheet |
| ERP connector | N/A demo | Scaffold | — | Talking points only |
| `demand/signal/ingest` | Optional | API only | No UI | POST-demo |

## Data Dependency Graph (must stay consistent)

```
cdm_product (names)
    ├── cdm_manufacturing_order (erp_mo_id MO-ST-*)
    │       ├── cdm_resolution_scenario (descriptions)
    │       ├── cdm_delay_event (cause_detail)
    │       └── cdm_work_order (shop floor)
    ├── cdm_demand_line (forecast history)
    └── Copilot material_status intent

cdm_work_center (names) → Schedule Gantt, shop floor, delays
cdm_supplier (names) → SCN portal, resolution scenarios
cdm_plant (names) → Supply network CP25
```

## Risk Register

| ID | Risk | Sev | Mitigation |
|----|------|-----|------------|
| R-ST-1 | Docker down | P0 | T-90 `prepare-startrans-demo.ps1`; backup screenshots |
| R-ST-2 | Copilot timeout | P1 | Pre-run CP10–11; cheat sheet fallback |
| R-ST-3 | Overlay run before base seed | P1 | Script enforces order |
| R-ST-4 | Excel upload WC code mismatch | P2 | Use WC001–WC003 in sample (unchanged erp_source_id) |
| R-ST-5 | C-suite bored by ops detail | P2 | 50–55 exec KPIs; shorten schedule deep-dive |

## Consistency Checks (post-implement)

```powershell
grep -r "MO-DEMO" docs/demo-data/STARTRANS*   # expect 0 (except mapping table)
grep -r "Widget A" docs/demo-data/STARTRANS*  # expect 0
.\scripts\run-full-demo.ps1 -Profile startrans -ReportPath docs/demo-data/startrans-pre-demo.txt
```

## Verdict

**Feasible today** with overlay + docs + profile param. No new microservices required. Integration gaps covered by pre-seed + Schedule upload + live API actions (sense, scenario, order).
