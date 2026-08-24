import { AlertTriangle, Bot, Building2, Gauge, Package, Truck } from 'lucide-react';
import { t } from '@/lib/i18n';
import { ROUTES } from '@/lib/constants';
import { KPICard } from './KPICard';
import type { WorkspaceKpis } from '../types';

interface KPIGridProps {
  kpis: WorkspaceKpis;
}

export function KPIGrid({ kpis }: KPIGridProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <KPICard
        label={t('workspace.kpi.at_risk', 'Orders at risk')}
        value={kpis.orders_at_risk.value}
        status={kpis.orders_at_risk.status}
        trend={kpis.orders_at_risk.trend}
        icon={AlertTriangle}
        delta={
          kpis.orders_at_risk.previous != null
            ? `${Number(kpis.orders_at_risk.value) - Number(kpis.orders_at_risk.previous) >= 0 ? '+' : ''}${Number(kpis.orders_at_risk.value) - Number(kpis.orders_at_risk.previous)} ${t('workspace.kpi.since_yesterday', 'since yesterday')}`
            : undefined
        }
        deltaDirection={
          Number(kpis.orders_at_risk.value) > Number(kpis.orders_at_risk.previous ?? 0) ? 'down' : 'flat'
        }
        actionLabel={kpis.orders_at_risk.value > 0 ? t('workspace.triage', 'Triage now') : undefined}
        actionUrl={ROUTES.PLANNING_CONTROL_TOWER}
      />
      <KPICard
        label={t('workspace.kpi.bottleneck', 'Bottleneck WC')}
        value={`${kpis.bottleneck_wc.value}%`}
        status={kpis.bottleneck_wc.status}
        trend={kpis.bottleneck_wc.trend}
        icon={Gauge}
        delta={
          kpis.bottleneck_wc.wc_name
            ? t('workspace.kpi.overloaded', '{name} overloaded', { name: kpis.bottleneck_wc.wc_name })
            : t('workspace.kpi.same', 'Same as yesterday')
        }
        deltaDirection={kpis.bottleneck_wc.status === 'critical' ? 'down' : 'flat'}
        actionLabel={t('workspace.actions.view', 'View')}
        actionUrl={ROUTES.PLANNING_SCHEDULE}
      />
      <KPICard
        label={t('workspace.kpi.supply', 'Supply health')}
        value={kpis.supply_health.value}
        status={kpis.supply_health.status}
        trend={kpis.supply_health.trend}
        icon={Package}
        delta={t('workspace.kpi.stockout_risk', 'Stockout risk items')}
        deltaDirection={Number(kpis.supply_health.value) > 0 ? 'down' : 'flat'}
        actionUrl={ROUTES.SUPPLY_INVENTORY}
      />
      <KPICard
        label={t('workspace.kpi.otd', 'On-time delivery')}
        value={kpis.otd.value}
        unit="%"
        status={kpis.otd.status}
        trend={kpis.otd.trend}
        icon={Truck}
        delta={
          kpis.otd.delta != null
            ? `${kpis.otd.delta >= 0 ? '+' : ''}${kpis.otd.delta}% ${t('workspace.kpi.vs_last_week', 'vs last week')}`
            : undefined
        }
        deltaDirection={(kpis.otd.delta ?? 0) >= 0 ? 'up' : 'down'}
        actionUrl={ROUTES.COMMAND_OTD_ANALYTICS}
      />
      <KPICard
        label={t('workspace.kpi.copilot_actions', 'Copilot actions today')}
        value={Number(kpis.ai_autonomy.value) > 0 ? kpis.ai_autonomy.value : '—'}
        status={Number(kpis.ai_autonomy.value) > 0 ? kpis.ai_autonomy.status : 'neutral'}
        icon={Bot}
        delta={t('workspace.kpi.user_initiated', 'User-initiated interactions')}
        deltaDirection="flat"
        actionUrl={ROUTES.AI_COPILOT}
      />
      <KPICard
        label={t('workspace.kpi.supplier', 'Supplier OTD')}
        value={kpis.supplier_otd.value > 0 ? `${kpis.supplier_otd.value}%` : '—'}
        status={kpis.supplier_otd.status}
        trend={kpis.supplier_otd.trend}
        icon={Building2}
        delta={t('workspace.kpi.stable', 'Stable this month')}
        deltaDirection="flat"
        actionUrl={ROUTES.SUPPLY_SUPPLIERS}
      />
    </div>
  );
}
