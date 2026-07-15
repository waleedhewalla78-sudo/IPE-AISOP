import { Link } from 'react-router-dom';
import { ROUTES } from '@/lib/constants';

const MODULE_META: Record<string, { title: string; blurb: string; links: { to: string; label: string }[] }> = {
  demand: {
    title: 'M1 Demand Command',
    blurb: 'Forecast, anomalies, ATP/CTP alignment with A1 + A8.',
    links: [
      { to: ROUTES.PLANNING_DEMAND, label: 'Demand forecast' },
      { to: ROUTES.SUPPLY_ORDERS, label: 'Orders' },
    ],
  },
  production: {
    title: 'M2 Production Command',
    blurb: 'Schedule, feasibility, resolution — A3/A4/A5 + Phase 3 predictive risk.',
    links: [
      { to: ROUTES.PLANNING_CONTROL_TOWER, label: 'Control tower' },
      { to: ROUTES.PLANNING_PREDICTIONS, label: 'Predictions' },
      { to: ROUTES.PLANNING_SCHEDULE, label: 'Schedule' },
    ],
  },
  supply: {
    title: 'M3 Supply Command',
    blurb: 'Stock health, PO recommendations (A9), supplier risk.',
    links: [
      { to: ROUTES.SUPPLY_INVENTORY, label: 'Inventory' },
      { to: ROUTES.SUPPLY_PROCUREMENT, label: 'Procurement' },
      { to: ROUTES.SUPPLY_SUPPLIERS, label: 'Suppliers' },
    ],
  },
  quality: {
    title: 'M4 Quality Command',
    blurb: 'SPC, defect prediction, CAPA (A10).',
    links: [{ to: ROUTES.AI_QUALITY, label: 'Quality dashboard' }],
  },
  finance: {
    title: 'M5 Finance Command',
    blurb: 'MO margin, decision P&L, cash sketch (A11).',
    links: [
      { to: ROUTES.COMMAND_COST_OF_CHAOS, label: 'Cost of chaos' },
      { to: ROUTES.COMMAND_EXECUTIVE, label: 'Executive' },
    ],
  },
  customer: {
    title: 'M6 Customer Command',
    blurb: 'Customer health, delay notices, portal (A8).',
    links: [
      { to: ROUTES.CUSTOMER_PORTAL, label: 'Customer portal' },
      { to: ROUTES.SUPPLY_ORDERS, label: 'Order management' },
    ],
  },
};

export function ModuleShellPage({ moduleKey }: { moduleKey: keyof typeof MODULE_META }) {
  const meta = MODULE_META[moduleKey];
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-ipe-text">{meta.title}</h2>
      <p className="max-w-2xl text-sm text-ipe-text-muted">{meta.blurb}</p>
      <ul className="space-y-2">
        {meta.links.map((l) => (
          <li key={l.to}>
            <Link className="text-ipe-primary hover:underline" to={l.to}>
              {l.label} ▸
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function DemandCommandPage() {
  return <ModuleShellPage moduleKey="demand" />;
}
export function ProductionCommandPage() {
  return <ModuleShellPage moduleKey="production" />;
}
export function SupplyCommandPage() {
  return <ModuleShellPage moduleKey="supply" />;
}
export function QualityCommandPage() {
  return <ModuleShellPage moduleKey="quality" />;
}
export function FinanceCommandPage() {
  return <ModuleShellPage moduleKey="finance" />;
}
export function CustomerCommandPage() {
  return <ModuleShellPage moduleKey="customer" />;
}
