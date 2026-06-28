import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';

const TABS = [
  { to: ROUTES.COMMAND_DASHBOARD, label: 'Dashboard' },
  { to: ROUTES.COMMAND_WAR_ROOM, label: 'War Room' },
  { to: ROUTES.COMMAND_EXECUTIVE, label: 'Executive' },
  { to: ROUTES.COMMAND_EQUIPMENT, label: 'Equipment' },
  { to: ROUTES.COMMAND_COST_OF_CHAOS, label: 'Cost of Chaos' },
];

export function CommandCenterHub() {
  return (
    <HubShell
      title="Command Center"
      subtitle="Alerts, KPIs, and financial impact of disruption"
      tabs={TABS}
    />
  );
}
