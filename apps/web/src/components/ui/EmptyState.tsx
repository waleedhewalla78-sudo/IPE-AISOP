/**
 * Empty table state with helpful message + action (STREAM-6.4).
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { t } from '@/lib/i18n';

interface Props {
  title?: string;
  message: string;
  actionLabel?: string;
  actionTo?: string;
  onAction?: () => void;
  children?: ReactNode;
}

export function EmptyState({
  title,
  message,
  actionLabel,
  actionTo,
  onAction,
  children,
}: Props) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center"
      data-testid="empty-state"
    >
      {title ? <p className="text-sm font-semibold text-ipe-text">{title}</p> : null}
      <p className="max-w-md text-sm text-ipe-text-muted">{message}</p>
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
      {!actionLabel ? (
        <p className="text-[10px] text-ipe-text-muted">
          {t('empty.hint', 'Seed demo data or upload Excel to populate this view.')}
        </p>
      ) : null}
    </div>
  );
}
