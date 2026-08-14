/**
 * Empty table/page state with helpful message + optional action (STREAM-6.4).
 * Supports both legacy props (description/action/tone) and demo props (message/actionLabel).
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { t } from '@/lib/i18n';
import { cn } from '@/lib/utils';

interface Props {
  title?: string;
  /** Preferred demo API */
  message?: string;
  /** Legacy alias for message */
  description?: string;
  actionLabel?: string;
  actionTo?: string;
  onAction?: () => void;
  /** Legacy: React node action (e.g. Button) */
  action?: ReactNode;
  tone?: 'default' | 'success' | 'warning' | 'danger' | string;
  className?: string;
  children?: ReactNode;
}

export function EmptyState({
  title,
  message,
  description,
  actionLabel,
  actionTo,
  onAction,
  action,
  tone = 'default',
  className,
  children,
}: Props) {
  const body = message ?? description ?? '';

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-2 px-4 py-10 text-center',
        tone === 'success' && 'text-score-excellent',
        className,
      )}
      data-testid="empty-state"
    >
      {title ? <p className="text-sm font-semibold text-ipe-text">{title}</p> : null}
      {body ? <p className="max-w-md text-sm text-ipe-text-muted">{body}</p> : null}
      {action}
      {actionTo && actionLabel ? (
        <Link
          to={actionTo}
          className="mt-2 rounded-md bg-ipe-primary px-3 py-1.5 text-xs font-medium text-white"
        >
          {actionLabel}
        </Link>
      ) : null}
      {onAction && actionLabel && !actionTo ? (
        <button
          type="button"
          className="mt-2 rounded-md bg-ipe-primary px-3 py-1.5 text-xs font-medium text-white"
          onClick={onAction}
        >
          {actionLabel}
        </button>
      ) : null}
      {children}
      {!actionLabel && !action ? (
        <p className="text-[10px] text-ipe-text-muted">
          {t('empty.hint', 'Seed demo data or upload Excel to populate this view.')}
        </p>
      ) : null}
    </div>
  );
}
