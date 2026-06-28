# Analyze — 006 Cross-Artifact Consistency

**Date**: 2026-06-27

## Coverage matrix

| Artifact | Hub nav | Legacy redirect | Dashboard | Demo script | Build |
|----------|---------|-----------------|-----------|-------------|-------|
| spec.md FR-HUB-01–04 | ✅ Sidebar | ✅ router | ✅ | ✅ | — |
| plan.md | ✅ | ✅ | ✅ | — | ✅ |
| tasks.md T001–T012 | ✅ | ✅ | ✅ | ✅ | ✅ |

## Project status impact

| Area | Before | After |
|------|--------|-------|
| Sidebar items | 14 | 6 |
| Hidden routes | 4 (MDR, Quality, Compliance, Sustainability) | 0 — in AI hub |
| Demo UI paths | Flat | Hub-nested |
| API surface | Unchanged | Unchanged |
| E2E legacy URLs | `/control-tower` | Redirect preserved |

## Risks

| Risk | Mitigation |
|------|------------|
| Deep links in docs | Legacy redirects |
| E2E tests expect old URLs | Redirects; optional test update |
| Hub tab active state | NavLink absolute paths |

## Consistency with v7.0.0

- No impact on 20/20 API checkpoints
- Copilot, Ollama, Kong unchanged
- Production blockers unchanged (ADR-001)
