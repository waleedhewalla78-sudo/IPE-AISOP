import { format } from 'date-fns';
import { cn } from '@/lib/utils';

const EPOCH_MS = Date.parse('1970-01-01T00:00:00.000Z');

/** True for null/undefined/invalid/Unix-epoch dates (renders as "Not set"). */
export function isUnsetDate(value: string | number | Date | null | undefined): boolean {
  if (value == null || value === '') return true;
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return true;
  // Epoch / near-epoch (common sentinel for missing dates)
  if (d.getTime() <= EPOCH_MS + 86_400_000) return true;
  // Local 1/1/1970 display quirk
  if (d.getFullYear() === 1970 && d.getMonth() === 0 && d.getDate() === 1) return true;
  return false;
}

export interface DateCellProps {
  value: string | number | Date | null | undefined;
  /** date-fns format string; default DD MMM YYYY style */
  pattern?: string;
  className?: string;
  emptyLabel?: string;
}

/**
 * Renders a date or muted "Not set" for null/epoch values.
 * Use in tables instead of raw toLocaleDateString().
 */
export function DateCell({
  value,
  pattern = 'dd MMM yyyy',
  className,
  emptyLabel = 'Not set',
}: DateCellProps) {
  if (isUnsetDate(value)) {
    return (
      <span className={cn('text-ipe-text-muted', className)} data-testid="date-cell-empty">
        {emptyLabel}
      </span>
    );
  }
  const d = value instanceof Date ? value : new Date(value as string | number);
  return (
    <span className={className} data-testid="date-cell">
      {format(d, pattern)}
    </span>
  );
}
