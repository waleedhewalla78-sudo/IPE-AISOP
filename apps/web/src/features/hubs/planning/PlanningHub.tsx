import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';

const TABS = [
  { to: ROUTES.PLANNING_DASHBOARD, label: 'Dashboard' },
  { to: ROUTES.PLANNING_DEMAND, label: 'Demand' },
  { to: ROUTES.PLANNING_SCENARIOS, label: 'Scenarios' },
  { to: ROUTES.PLANNING_CONTROL_TOWER, label: 'Control Tower' },
  { to: ROUTES.PLANNING_RESOLUTION, label: 'Resolution' },
  { to: ROUTES.PLANNING_SCHEDULE, label: 'Schedule' },
];

export function PlanningHub() {
  return (
    <HubShell
      title="Planning Hub"
      subtitle="Detect → decide → schedule"
      tabs={TABS}
    />
  );
}
