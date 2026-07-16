import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';
import { IS_RELEASE1, SHOW_R2_PLANNING_TABS } from '@/lib/releaseProfile';
import { t } from '@/lib/i18n';

const ALL_TABS = [
  { to: ROUTES.PLANNING_DASHBOARD, label: 'Dashboard', release1: false },
  { to: ROUTES.PLANNING_COCKPIT, label: 'Cockpit', release1: false },
  { to: ROUTES.PLANNING_HORIZONS, label: 'Horizons', release1: false },
  { to: ROUTES.PLANNING_DEMAND, label: 'Demand', release1: false },
  { to: ROUTES.PLANNING_SCENARIOS, label: 'Scenarios', release1: false },
  { to: ROUTES.PLANNING_CONTROL_TOWER, labelKey: 'controlTower.title', label: 'Control Tower' },
  { to: ROUTES.PLANNING_RESOLUTION, labelKey: 'resolution.title', label: 'Resolution' },
  { to: ROUTES.PLANNING_SCHEDULE, label: 'Schedule' },
  { to: ROUTES.PLANNING_PREDICTIONS, labelKey: 'predictions.title', label: 'Predictions' },
  { to: ROUTES.PLANNING_ROOT_CAUSE, labelKey: 'rootCause.title', label: 'Root Cause' },
];

const TABS = ALL_TABS.filter((tab) => {
  if (tab.release1 === false && IS_RELEASE1 && !SHOW_R2_PLANNING_TABS) return false;
  return true;
}).map((tab) => ({
  to: tab.to,
  label: tab.labelKey ? t(tab.labelKey, tab.label) : tab.label,
}));
export function PlanningHub() {
  return (
    <HubShell
      title="Planning Hub"
      subtitle="Detect → decide → schedule"
      tabs={TABS}
    />
  );
}
