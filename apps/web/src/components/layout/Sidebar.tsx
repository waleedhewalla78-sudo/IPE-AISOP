import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';

const NAV_ITEMS = [
  { to: ROUTES.CONTROL_TOWER, label: 'Control Tower', icon: '📊' },
  { to: ROUTES.SCHEDULE, label: 'Schedule', icon: '📅' },
  { to: ROUTES.RESOLUTION_CENTER, label: 'Resolution Center', icon: '🔧' },
  { to: ROUTES.COPILOT, label: 'Copilot', icon: '🤖' },
  { to: ROUTES.EXECUTIVE, label: 'Executive', icon: '📈' },
  { to: ROUTES.COST_OF_CHAOS, label: 'Cost of Chaos', icon: '💸' },
  { to: ROUTES.TARIFF, label: 'Tariff', icon: '🌐' },
  { to: ROUTES.WAR_ROOM, label: 'War Room', icon: '🚨' },
  { to: ROUTES.AI_TRUST, label: 'AI Trust', icon: '🛡️' },
  { to: ROUTES.SHOP_FLOOR, label: 'Shop Floor', icon: '🏭' },
  { to: ROUTES.SCN_PORTAL, label: 'SCN Portal', icon: '🤝' },
  { to: ROUTES.ML_OPS, label: 'MLOps', icon: '⚡' },
  { to: ROUTES.ONBOARDING, label: 'Onboarding', icon: '🚀' },
  { to: ROUTES.ADMIN, label: 'Admin', icon: '⚙️' },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-64 flex-col border-r border-ipe-border bg-white">
      <div className="flex h-14 items-center border-b border-ipe-border px-4">
        <h1 className="text-lg font-bold text-ipe-primary">IPE</h1>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-ipe-primary/10 text-ipe-primary'
                  : 'text-ipe-text-muted hover:bg-ipe-surface-alt hover:text-ipe-text',
              )
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
