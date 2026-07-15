import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
  tone?: 'neutral' | 'success';
}

export function EmptyState({
  title,
  description,
  action,
  className,
  tone = 'neutral',
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed border-ipe-border bg-white px-6 py-12 text-center',
        tone === 'success' && 'border-emerald-200 bg-emerald-50/40',
        className,
      )}
    >
      <p className="text-base font-medium text-ipe-text">{title}</p>
      <p className="mt-2 max-w-md text-sm text-ipe-text-muted">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
