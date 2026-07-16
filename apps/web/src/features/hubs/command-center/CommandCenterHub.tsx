import { HubShell } from '@/components/hubs/HubShell';

import { ROUTES } from '@/lib/constants';

import { IS_RELEASE1 } from '@/lib/releaseProfile';

import { t } from '@/lib/i18n';



const ALL_TABS = [

  { to: ROUTES.COMMAND_DASHBOARD, label: 'Dashboard', release1: false },

  { to: ROUTES.COMMAND_OPS_LIVE, label: 'Ops Live', release1: false },

  { to: ROUTES.COMMAND_WAR_ROOM, label: 'War Room', release1: false },

  { to: ROUTES.COMMAND_OUTCOMES, labelKey: 'outcomes.title', label: 'Outcomes' },

  { to: ROUTES.COMMAND_OTD_ANALYTICS, labelKey: 'analytics.otd.title', label: 'OTD Analytics', release1: true },

  { to: ROUTES.COMMAND_EXECUTIVE, label: 'Executive', release1: false },

  { to: ROUTES.COMMAND_EQUIPMENT, label: 'Equipment', release1: false },

  { to: ROUTES.COMMAND_COST_OF_CHAOS, label: 'Cost of Chaos', release1: false },
  { to: ROUTES.COMMAND_SOP_REPORT, label: 'S&OP Report', release1: false },
  { to: ROUTES.COMMAND_OPERATIONS_DEEP, label: 'Operations Deep', release1: false },

];



const TABS = ALL_TABS.filter((tab) => !IS_RELEASE1 || tab.release1 !== false).map((tab) => ({

  to: tab.to,

  label: tab.labelKey ? t(tab.labelKey, tab.label) : tab.label,

}));



export function CommandCenterHub() {

  return (

    <HubShell

      title="Command Center"

      subtitle="Alerts, KPIs, and financial impact of disruption"

      tabs={TABS}

    />

  );

}

