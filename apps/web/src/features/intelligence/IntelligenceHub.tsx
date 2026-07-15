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
];

export function IntelligenceHub() {
  return (
    <HubShell
      title="Manufacturing Intelligence"
      subtitle="Six command modules · 12 agents · autonomous overnight actions"
      tabs={TABS}
    />
  );
}
