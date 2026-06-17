import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: ReactNode;
  className?: string;
}

export function KPICard({ title, value, subtitle, trend, icon, className }: KPICardProps) {
  return (
    <div className={cn('rounded-lg border border-ipe-border bg-white p-5 shadow-sm', className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-ipe-text-muted">{title}</p>
          <p className="mt-1 text-3xl font-bold text-ipe-text">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-ipe-text-muted">{subtitle}</p>}
        </div>
        {icon && <div className="text-ipe-text-muted">{icon}</div>}
      </div>
      {trend && (
        <div className="mt-2">
          <span
            className={cn('inline-flex items-center text-xs font-medium', {
              'text-green-600': trend === 'up',
              'text-red-600': trend === 'down',
              'text-ipe-text-muted': trend === 'neutral',
            })}
          >
            {trend === 'up' && '\u2191'}
            {trend === 'down' && '\u2193'}
            {trend === 'neutral' && '\u2192'}
          </span>
        </div>
      )}
    </div>
  );
}
