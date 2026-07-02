import { NavLink, Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';

export interface HubTab {
  to: string;
  label: string;
}

interface HubShellProps {
  title: string;
  subtitle?: string;
  tabs: HubTab[];
}

export function HubShell({ title, subtitle, tabs }: HubShellProps) {
  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-ipe-text-muted">{subtitle}</p> : null}
      </div>
      <nav className="flex flex-wrap gap-1 border-b border-ipe-border pb-0">
        {tabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              cn(
                'rounded-t-md px-4 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'border border-b-white border-ipe-border bg-white text-ipe-primary'
                  : 'text-ipe-text-muted hover:bg-ipe-surface-alt hover:text-ipe-text',
              )
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <div className="flex-1 min-h-0">
        <Outlet />
      </div>
    </div>
  );
}
