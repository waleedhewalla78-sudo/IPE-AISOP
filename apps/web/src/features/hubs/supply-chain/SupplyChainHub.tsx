import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';

const TABS = [
  { to: ROUTES.SUPPLY_PLANNING, label: 'Supply Planning' },
  { to: ROUTES.SUPPLY_ORDERS, label: 'Orders' },
  { to: ROUTES.SUPPLY_PROCUREMENT, label: 'Procurement' },
  { to: ROUTES.SUPPLY_SUPPLIERS, label: 'Suppliers' },
  { to: ROUTES.SUPPLY_TARIFF, label: 'Tariff' },
  { to: ROUTES.SUPPLY_SCN, label: 'SCN Portal' },
  { to: ROUTES.SUPPLY_INVENTORY, label: 'Inventory' },
];

export function SupplyChainHub() {
  return (
    <HubShell
      title="Supply Chain Hub"
      subtitle="Suppliers, landed cost, and inventory"
      tabs={TABS}
    />
  );
}
