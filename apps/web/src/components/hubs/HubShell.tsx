import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';

export interface HubTab {
  to: string;
  label: string;
  /** Optional pill on the tab. Falsy values render nothing. */
  badge?: string | number | null;
}

export interface HubMoreItem {
  to: string;
  label: string;
  description?: string;
}

interface HubShellProps {
  title: string;
  subtitle?: string;
  tabs: HubTab[];
  /**
   * Legacy overflow slots — promoted into the primary tab row.
   * "More" bucket label removed (STREAM 3).
   */
  moreItems?: HubMoreItem[];
  /** Right-aligned header slot (e.g. persona lens chip, mode toggle). */
  headerAside?: React.ReactNode;
}

function TabLink({ tab }: { tab: HubTab }) {
  const location = useLocation();
  return (
    <NavLink
      to={tab.to}
      className={({ isActive }) => {
        const active = isActive || location.pathname.startsWith(`${tab.to}/`);
        return cn(
          'inline-flex items-center gap-2 rounded-t-md px-4 py-2 text-sm font-medium transition-colors',
          active
            ? 'border border-b-white border-ipe-border bg-white text-ipe-primary'
            : 'text-ipe-text-muted hover:bg-ipe-surface-alt hover:text-ipe-text',
        );
      }}
    >
      {tab.label}
      {tab.badge != null && tab.badge !== '' ? (
        <span className="rounded-full bg-ipe-primary/10 px-1.5 text-[10px] font-semibold text-ipe-primary tabular-nums">
          {tab.badge}
        </span>
      ) : null}
    </NavLink>
  );
}

export function HubShell({ title, subtitle, tabs, moreItems, headerAside }: HubShellProps) {
  const allTabs: HubTab[] = [
    ...tabs,
    ...(moreItems ?? []).map((it) => ({ to: it.to, label: it.label })),
  ];

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ipe-text">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-ipe-text-muted">{subtitle}</p> : null}
        </div>
        {headerAside ? <div className="flex flex-wrap items-center gap-2">{headerAside}</div> : null}
      </div>
      <nav className="flex flex-wrap items-end gap-1 border-b border-ipe-border pb-0">
        {allTabs.map((tab) => (
          <TabLink key={tab.to} tab={tab} />
        ))}
      </nav>
      <div className="flex-1 min-h-0">
        <Outlet />
      </div>
    </div>
  );
}
