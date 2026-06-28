# Plan — 006 Module Hub Consolidation

**Stack**: React 18, React Router 6, Vite, Tailwind, existing IPE UI components

## Architecture

```
MainLayout
  Sidebar (6 hubs)
  Outlet
    HubShell (title + tabs)
      Outlet → existing *Page components
```

## File plan

| Path | Purpose |
|------|---------|
| `components/hubs/HubShell.tsx` | Shared tab chrome |
| `features/hubs/planning/*` | Planning hub + dashboard |
| `features/hubs/command-center/*` | Command hub + dashboard |
| `features/hubs/supply-chain/*` | Supply hub + inventory |
| `features/hubs/ai-governance/AIGovernanceHub.tsx` | AI tabs shell |
| `features/hubs/platform/PlatformHub.tsx` | Platform tabs shell |
| `app/router.tsx` | Nested routes + legacy redirects |
| `lib/constants.ts` | ROUTES hub paths |
| `components/layout/Sidebar.tsx` | 6-item nav |

## Implementation phases

1. HubShell + constants + router skeleton
2. Wire existing pages into nested routes
3. Build Planning + Command dashboards
4. Inventory tab + sidebar
5. Legacy redirects + demo script
6. Build verify + demo 20/20
7. Code-split hub routes via `React.lazy` + vendor chunks (T018)
