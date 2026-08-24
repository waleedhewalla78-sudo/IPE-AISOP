import { AlertTriangle, Bot, Building2, CircleDollarSign, Factory, Gauge, Package, Target, Truck } from 'lucide-react';
import { t } from '@/lib/i18n';
import { ROUTES } from '@/lib/constants';
import { KPICard } from './KPICard';
import type { PersonaId } from '@/lib/personaHome';
import type { HealthStatus, WorkspaceDashboard } from '../types';

/**
 * PersonaWidgetGrid — Spec 039 Wave 2.
 *
 * Renders the same underlying KPI catalogue but ordered per persona lens.
 * Everyone still gets the honest numbers (no fake KPIs); only the ranking
 * and CTA emphasis change.
 */

interface WidgetSpec {
  id: string;
  render: (dashboard: WorkspaceDashboard) => JSX.Element | null;
}

function delta(current: number, previous: number | null | undefined, suffix?: string): string | undefined {
  if (previous == null) return undefined;
  const diff = current - previous;
  const sign = diff >= 0 ? '+' : '';
  return `${sign}${diff}${suffix ?? ''}`;
}

function ordersAtRisk(dashboard: WorkspaceDashboard): JSX.Element {
  const k = dashboard.kpis.orders_at_risk;
  return (
    <KPICard
      key="orders_at_risk"
      label={t('workspace.kpi.at_risk', 'Orders at risk')}
      value={k.value}
      status={k.status}
      trend={k.trend}
      icon={AlertTriangle}
      delta={delta(Number(k.value), k.previous ?? null, ` ${t('workspace.kpi.since_yesterday', 'since yesterday')}`)}
      deltaDirection={Number(k.value) > Number(k.previous ?? 0) ? 'down' : 'flat'}
      actionLabel={Number(k.value) > 0 ? t('workspace.triage', 'Triage now') : undefined}
      actionUrl={ROUTES.PLANNING_CONTROL_TOWER}
    />
  );
}

function otd(dashboard: WorkspaceDashboard): JSX.Element {
  const k = dashboard.kpis.otd;
  return (
    <KPICard
      key="otd"
      label={t('workspace.kpi.otd', 'On-time delivery')}
      value={k.value}
      unit="%"
      status={k.status}
      trend={k.trend}
      icon={Truck}
      delta={
        k.delta != null
          ? `${k.delta >= 0 ? '+' : ''}${k.delta}% ${t('workspace.kpi.vs_last_week', 'vs last week')}`
          : undefined
      }
      deltaDirection={(k.delta ?? 0) >= 0 ? 'up' : 'down'}
      actionUrl={ROUTES.COMMAND_OTD_ANALYTICS}
    />
  );
}

function bottleneck(dashboard: WorkspaceDashboard): JSX.Element {
  const k = dashboard.kpis.bottleneck_wc;
  return (
    <KPICard
      key="bottleneck"
      label={t('workspace.kpi.bottleneck', 'Bottleneck WC')}
      value={`${k.value}%`}
      status={k.status}
      trend={k.trend}
      icon={Gauge}
      delta={
        k.wc_name
          ? t('workspace.kpi.overloaded', '{name} overloaded', { name: k.wc_name })
          : t('workspace.kpi.same', 'Same as yesterday')
      }
      deltaDirection={k.status === 'critical' ? 'down' : 'flat'}
      actionLabel={t('workspace.actions.view', 'View')}
      actionUrl={ROUTES.PLANNING_SCHEDULE}
    />
  );
}

function supply(dashboard: WorkspaceDashboard): JSX.Element {
  const k = dashboard.kpis.supply_health;
  return (
    <KPICard
      key="supply"
      label={t('workspace.kpi.supply', 'Supply health')}
      value={k.value}
      status={k.status}
      trend={k.trend}
      icon={Package}
      delta={t('workspace.kpi.stockout_risk', 'Stockout risk items')}
      deltaDirection={Number(k.value) > 0 ? 'down' : 'flat'}
      actionUrl={ROUTES.SUPPLY_INVENTORY}
    />
  );
}

function supplierOtd(dashboard: WorkspaceDashboard): JSX.Element {
  const k = dashboard.kpis.supplier_otd;
  return (
    <KPICard
      key="supplier_otd"
      label={t('workspace.kpi.supplier', 'Supplier OTD')}
      value={k.value > 0 ? `${k.value}%` : '—'}
      status={k.status}
      trend={k.trend}
      icon={Building2}
      delta={t('workspace.kpi.stable', 'Stable this month')}
      deltaDirection="flat"
      actionUrl={ROUTES.SUPPLY_SUPPLIERS}
    />
  );
}

function copilotActions(dashboard: WorkspaceDashboard): JSX.Element {
  // Prefer real interaction count when present; hide zero-autonomy vanity tile.
  const k = dashboard.kpis.ai_autonomy;
  const value = Number(k.value);
  if (!Number.isFinite(value) || value <= 0) {
    return (
      <KPICard
        key="copilot_actions"
        label={t('workspace.kpi.copilot_actions', 'Copilot actions today')}
        value="—"
        status="neutral"
        icon={Bot}
        delta={t('workspace.kpi.copilot_hint', 'Ask Copilot from the AI domain')}
        deltaDirection="flat"
        actionLabel={t('workspace.ask_ai', 'Ask AI')}
        actionUrl={ROUTES.AI_COPILOT}
      />
    );
  }
  return (
    <KPICard
      key="copilot_actions"
      label={t('workspace.kpi.copilot_actions', 'Copilot actions today')}
      value={value}
      status={k.status}
      icon={Bot}
      delta={t('workspace.kpi.user_initiated', 'User-initiated interactions')}
      deltaDirection="flat"
      actionUrl={ROUTES.AI_COPILOT}
    />
  );
}

function chaos(dashboard: WorkspaceDashboard): JSX.Element {
  // Derived from actions — count of critical severity as chaos proxy.
  const criticalCount = dashboard.actions.filter((a) => a.severity === 'critical').length;
  const status: HealthStatus = criticalCount === 0 ? 'healthy' : criticalCount < 3 ? 'warning' : 'critical';
  return (
    <KPICard
      key="chaos"
      label={t('workspace.kpi.chaos', 'Cost of chaos (7d)')}
      value={criticalCount > 0 ? `${criticalCount}× ${t('workspace.kpi.critical', 'critical')}` : t('workspace.kpi.calm', 'Calm')}
      status={status}
      icon={CircleDollarSign}
      actionLabel={t('workspace.kpi.see_money', 'See financial impact')}
      actionUrl={ROUTES.COMMAND_COST_OF_CHAOS}
    />
  );
}

function shopFloorPulse(dashboard: WorkspaceDashboard): JSX.Element {
  const criticals = dashboard.actions.filter((a) => a.severity === 'critical').length;
  const status: HealthStatus = criticals === 0 ? 'healthy' : 'warning';
  return (
    <KPICard
      key="shopfloor"
      label={t('workspace.kpi.shopfloor', 'Shop floor')}
      value={criticals === 0 ? t('workspace.kpi.running', 'Running') : t('workspace.kpi.attention', 'Needs attention')}
      status={status}
      icon={Factory}
      actionLabel={t('workspace.kpi.open_shopfloor', 'Open shop floor')}
      actionUrl={ROUTES.SHOP_FLOOR}
    />
  );
}

function customerFocus(dashboard: WorkspaceDashboard): JSX.Element {
  const k = dashboard.kpis.otd;
  return (
    <KPICard
      key="customer"
      label={t('workspace.kpi.customer_promise', 'Customer promise')}
      value={`${k.value}%`}
      status={k.status}
      icon={Target}
      delta={t('workspace.kpi.customer_focus', 'Late orders + at-risk promises')}
      deltaDirection={(k.delta ?? 0) >= 0 ? 'up' : 'down'}
      actionLabel={t('workspace.kpi.view_outcomes', 'View customer outcomes')}
      actionUrl={ROUTES.COMMAND_OUTCOMES}
    />
  );
}

const WIDGETS: Record<string, WidgetSpec> = {
  ordersAtRisk: { id: 'ordersAtRisk', render: ordersAtRisk },
  otd: { id: 'otd', render: otd },
  bottleneck: { id: 'bottleneck', render: bottleneck },
  supply: { id: 'supply', render: supply },
  supplierOtd: { id: 'supplierOtd', render: supplierOtd },
  autonomy: { id: 'autonomy', render: copilotActions },
  chaos: { id: 'chaos', render: chaos },
  shopFloor: { id: 'shopFloor', render: shopFloorPulse },
  customer: { id: 'customer', render: customerFocus },
};

/**
 * Persona → widget order. First entry is the anchor / most prominent card.
 * Every persona still gets ~6 widgets — the difference is emphasis, not
 * information hiding, because the constitution requires honesty.
 */
const PERSONA_ORDER: Record<PersonaId, string[]> = {
  CEO: ['otd', 'chaos', 'customer', 'ordersAtRisk', 'autonomy', 'supply'],
  Ops: ['ordersAtRisk', 'bottleneck', 'otd', 'supply', 'autonomy', 'chaos'],
  Sales: ['customer', 'otd', 'ordersAtRisk', 'supply', 'autonomy', 'supplierOtd'],
  SC: ['supply', 'supplierOtd', 'ordersAtRisk', 'bottleneck', 'otd', 'autonomy'],
  Material: ['supply', 'supplierOtd', 'bottleneck', 'ordersAtRisk', 'otd', 'autonomy'],
  Production: ['bottleneck', 'ordersAtRisk', 'supply', 'otd', 'autonomy', 'chaos'],
  Scheduler: ['bottleneck', 'ordersAtRisk', 'otd', 'supply', 'autonomy', 'chaos'],
  Finance: ['chaos', 'otd', 'ordersAtRisk', 'supply', 'autonomy', 'customer'],
  Demand: ['customer', 'otd', 'ordersAtRisk', 'chaos', 'autonomy', 'supply'],
  Frontline: ['shopFloor', 'bottleneck', 'ordersAtRisk', 'supply', 'otd', 'autonomy'],
};

interface PersonaWidgetGridProps {
  dashboard: WorkspaceDashboard;
  persona: PersonaId;
}

export function PersonaWidgetGrid({ dashboard, persona }: PersonaWidgetGridProps): JSX.Element {
  const order = PERSONA_ORDER[persona] ?? PERSONA_ORDER.Ops;
  const rendered = order
    .map((id) => WIDGETS[id])
    .filter((w): w is WidgetSpec => Boolean(w))
    .map((w) => w.render(dashboard))
    .filter((node): node is JSX.Element => node !== null);

  return (
    <div
      className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
      data-testid="persona-widget-grid"
      data-persona={persona}
    >
      {rendered}
    </div>
  );
}

export const _testExports = { PERSONA_ORDER, WIDGETS };
