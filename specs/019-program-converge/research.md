# Research: 019-program-converge

## Decision 1 — Feature isolation

**Decision**: New `specs/019-program-converge/`  
**Rationale**: Avoid corrupting 017/018 sprint history; AGENTS.md allows dedicated program feature.  
**Alternatives**: Update 005 in place (rejected — mixes eras); append only to 018 (rejected — conflates R2 gate with program rollup).

## Decision 2 — Scenario promote semantics

**Decision**: Soft promote — set `status=promoted`; do not write schedule to ERP.  
**Rationale**: #40 asks for promotion UI; live schedule approve already exists on Resolution/Schedule paths.  
**Alternatives**: Promote = approve schedule to Odoo (rejected — duplicates cap/res flows).

## Decision 3 — mat-svc on R2 compose

**Decision**: Add service with `IPE_KAFKA_BOOTSTRAP_SERVERS=""` and AUTH_MODE=local.  
**Rationale**: nlp-svc already points at mat-svc; missing container is a compose bug.  
**Alternatives**: Remove MAT_SVC_URL (rejected — breaks Copilot tools).

## Decision 4 — stock.quant

**Decision**: Fix mock data; keep connector `sync_inventory()` as source of truth for eng E2E.  
**Rationale**: OPEN-ITEMS listed FR-R1-05 open because mock returned []. Staging Odoo remains PH1-02.  
**Alternatives**: CUT FR-R1-05 (rejected — path already coded).

## Decision 5 — Issue strategy

**Decision**: Implement #40; comment+defer #37/#38/#42–#46; no duplicates of closed Wave1 issues.  
**Rationale**: User instruction + OPEN-ITEMS.
