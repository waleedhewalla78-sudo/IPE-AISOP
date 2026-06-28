# Analyze — 009 v8 Phase 3

## Dependencies

- Migration 030 (Phase 2) must be applied before 031
- Kong gateway routes new paths through existing `:8000` entry
- Web dev proxy unchanged (`/api` → Kong)

## Risks

| Risk | Mitigation |
|------|------------|
| `/api/v1/suppliers` path collision | No existing Kong route; dpe demo portal uses different prefix |
| Empty supplier table in demo | Compliance check returns NOT_FOUND; seed script suppliers work once migrated |
| material-svc catalog duplication | Tenant-scoped lazy seed only when table empty |

## Reuse

- Phase 1/2 service scaffold (FastAPI + ipe_shared + TenantContext)
- `Supplier` ORM extended, not duplicated
- Hub tab pattern from Phase 2
