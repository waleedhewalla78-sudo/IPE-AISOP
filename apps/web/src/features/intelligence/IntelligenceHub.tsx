import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';

const TABS = [
  { to: ROUTES.INTELLIGENCE_PULSE, label: "Today's Pulse" },
  { to: ROUTES.INTELLIGENCE_DEMAND, label: 'M1 Demand' },
  { to: ROUTES.INTELLIGENCE_PRODUCTION, label: 'M2 Production' },
  { to: ROUTES.INTELLIGENCE_SUPPLY, label: 'M3 Supply' },
  { to: ROUTES.INTELLIGENCE_QUALITY, label: 'M4 Quality' },
  { to: ROUTES.INTELLIGENCE_FINANCE, label: 'M5 Finance' },
  { to: ROUTES.INTELLIGENCE_CUSTOMER, label: 'M6 Customer' },
  { to: ROUTES.INTELLIGENCE_ANALYTICS, label: 'M7 Analytics' },
  { to: ROUTES.INTELLIGENCE_COMMERCIAL, label: 'M8 Commercial' },
  { to: ROUTES.INTELLIGENCE_PROCUREMENT, label: 'M9 Procurement' },
  { to: ROUTES.INTELLIGENCE_SOP_DEEP, label: 'S&OP Deep' },
  { to: ROUTES.INTELLIGENCE_DEMAND_DEEP, label: 'Demand Deep' },
  { to: ROUTES.INTELLIGENCE_PRODUCTION_DEEP, label: 'Production Deep' },
];

export function IntelligenceHub() {
  return (
    <HubShell
      title="Manufacturing Intelligence"
      subtitle="Nine command modules · 17 agents · autonomous cross-functional orchestration"
      tabs={TABS}
    />
  );
}
