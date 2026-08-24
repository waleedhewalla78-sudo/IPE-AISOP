# T096 — Sunday customer ingest (Batch 0 continuation)

**Date:** 2026-08-24  
**Spec:** `040-startrans-demo-aug18`  
**Branch:** `033-phase9-wave9a`

## Trigger

Ingest a Star Trans–filled workbook **if it arrived** Sunday (T095 return). Otherwise use template sample rows + T092 seed fallback (`docs/qa/T095-CUSTOMER-EMAIL-SEND-CHECKLIST.md`).

## Search performed

| Location | Result |
|----------|--------|
| `C:\Users\HP\Downloads\` (`*.xlsx` / `*.xls` / `*.xlsm`) | **None** |
| `C:\Users\HP\Downloads\IPE\` | Prompt packages only (no workbook) |
| `ipe/docs/demo-data/startrans/` | Canonical **template** `IPE_Data_Template_StarTrans_v1.xlsx` only (not a customer-filled return) |

No file matching a customer-filled Star Trans workbook was found.

## Ingest

**Not run.** No customer payload. T092 seed (20 MOs, bands 3/5/4/8) remains the demo data source.

R2 stack was **down** at continuation time (see `BATCH0-CONTINUATION-2026-08-24.md`); even if a file appeared, live `/api/v1/data/upload` could not be executed until T090 ports are free.

## VERDICT

**N/A (GREEN for fallback)** — no customer file arrived as of 2026-08-24; seed fallback is valid. Do not invent an ingest.
