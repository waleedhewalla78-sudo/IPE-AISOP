import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';
import { IS_RELEASE1 } from '@/lib/releaseProfile';
import { t } from '@/lib/i18n';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

const ALL_NAV = [
  { to: ROUTES.PLANNING, labelKey: 'nav.planning', icon: '📊', match: ROUTES.PLANNING },
  { to: ROUTES.COMMAND_CENTER, labelKey: 'nav.commandCenter', icon: '🎯', match: ROUTES.COMMAND_CENTER },
  { to: ROUTES.SUPPLY_CHAIN, labelKey: 'nav.supplyChain', icon: '🌐', match: ROUTES.SUPPLY_CHAIN, release1: false },
  { to: ROUTES.AI_GOVERNANCE, labelKey: 'nav.aiGovernance', icon: '🤖', match: ROUTES.AI_GOVERNANCE, release1: false },
  { to: ROUTES.SHOP_FLOOR, labelKey: 'nav.shopFloor', icon: '🏭', match: ROUTES.SHOP_FLOOR, release1: false },
  { to: ROUTES.PLATFORM, labelKey: 'nav.platform', icon: '⚙️', match: ROUTES.PLATFORM },
];

const NAV_ITEMS = ALL_NAV.filter((item) => !IS_RELEASE1 || item.release1 !== false);

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-ipe-border bg-white">
      <div className="flex h-14 items-center justify-between border-b border-ipe-border px-4">
        <h1 className="text-lg font-bold text-ipe-primary">IPE</h1>
        <LanguageSwitcher />
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
            <span>{t(item.labelKey, item.labelKey)}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
