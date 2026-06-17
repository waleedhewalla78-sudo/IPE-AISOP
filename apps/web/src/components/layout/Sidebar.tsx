import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';

const NAV_ITEMS = [
  { to: ROUTES.CONTROL_TOWER, label: 'Control Tower', icon: '📊' },
  { to: ROUTES.RESOLUTION_CENTER, label: 'Resolution Center', icon: '🔧' },
  { to: ROUTES.COPILOT, label: 'Copilot', icon: '🤖' },
  { to: ROUTES.SHOP_FLOOR, label: 'Shop Floor', icon: '🏭' },
  { to: ROUTES.ADMIN, label: 'Admin', icon: '⚙️' },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-64 flex-col border-r border-ipe-border bg-white">
      <div className="flex h-14 items-center border-b border-ipe-border px-4">
        <h1 className="text-lg font-bold text-ipe-primary">IPE</h1>
      </div>
      <nav className="flex-1 space-y-1 p-2">
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
