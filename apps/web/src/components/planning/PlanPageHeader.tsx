import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface PlanPageHeaderProps {
  title: string;
  subtitle?: string;
  badge?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

/** Consistent Plan-domain page chrome. */
export function PlanPageHeader({ title, subtitle, badge, actions, className }: PlanPageHeaderProps) {
  return (
    <div
      className={cn(
        'flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between',
        className,
      )}
      data-testid="plan-page-header"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-ipe-text">{title}</h1>
          {badge}
        </div>
        {subtitle ? <p className="mt-1 max-w-2xl text-sm text-ipe-text-muted">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
