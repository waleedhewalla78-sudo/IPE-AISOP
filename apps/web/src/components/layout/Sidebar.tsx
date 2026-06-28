import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';

const NAV_ITEMS = [
  { to: ROUTES.PLANNING, label: 'Planning Hub', icon: '📊', match: ROUTES.PLANNING },
  { to: ROUTES.COMMAND_CENTER, label: 'Command Center', icon: '🎯', match: ROUTES.COMMAND_CENTER },
  { to: ROUTES.SUPPLY_CHAIN, label: 'Supply Chain', icon: '🌐', match: ROUTES.SUPPLY_CHAIN },
  { to: ROUTES.AI_GOVERNANCE, label: 'AI & Governance', icon: '🤖', match: ROUTES.AI_GOVERNANCE },
  { to: ROUTES.SHOP_FLOOR, label: 'Shop Floor', icon: '🏭', match: ROUTES.SHOP_FLOOR },
  { to: ROUTES.PLATFORM, label: 'Platform', icon: '⚙️', match: ROUTES.PLATFORM },
];

export function Sidebar() {
  const location = useLocation();

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
            end={item.to === ROUTES.SHOP_FLOOR}
            className={({ isActive }) => {
              const active =
                isActive ||
                (item.match !== ROUTES.SHOP_FLOOR && location.pathname.startsWith(`${item.match}/`));
              return cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-ipe-primary/10 text-ipe-primary'
                  : 'text-ipe-text-muted hover:bg-ipe-surface-alt hover:text-ipe-text',
              );
            }}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
