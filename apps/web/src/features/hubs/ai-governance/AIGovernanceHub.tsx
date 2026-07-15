import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';

const TABS = [
  { to: ROUTES.AI_COPILOT, label: 'Copilot' },
  { to: ROUTES.AI_MEETING_PREP, label: 'Meeting Prep' },
  { to: ROUTES.AI_DESIGN, label: 'Design AI' },
  { to: ROUTES.AI_TRUST, label: 'AI Trust' },
  { to: ROUTES.AI_MDR, label: 'MDR Gate' },
  { to: ROUTES.AI_COMPLIANCE, label: 'Compliance' },
  { to: ROUTES.AI_QUALITY, label: 'Quality' },
  { to: ROUTES.AI_SUSTAINABILITY, label: 'Sustainability' },
];

export function AIGovernanceHub() {
  return (
    <HubShell
      title="AI & Governance"
      subtitle="Copilot, trust scores, and data quality gates"
      tabs={TABS}
    />
  );
}
