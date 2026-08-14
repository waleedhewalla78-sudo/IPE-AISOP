/**
 * KpiTile — label + metric + optional trend + status accent bar.
 */
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ScoreTier } from '@/lib/scoreVisuals';

export type KpiStatus = Exclude<ScoreTier, 'pending'> | 'neutral';
export type KpiTrendDirection = 'up' | 'down' | 'flat';

interface KpiTileProps {
  label: string;
  metric: string | number;
  trend?: { direction: KpiTrendDirection; value?: string } | null;
  status?: KpiStatus;
  className?: string;
  onClick?: () => void;
}

const statusAccent: Record<KpiStatus, string> = {
  excellent: 'border-s-score-excellent',
  good: 'border-s-score-good',
  warning: 'border-s-score-warning',
  risk: 'border-s-score-risk',
  critical: 'border-s-score-critical',
  neutral: 'border-s-ipe-border-strong',
};

export function KpiTile({
  label,
  metric,
  trend = null,
  status = 'neutral',
  className,
  onClick,
}: KpiTileProps) {
  const TrendIcon =
    trend?.direction === 'up' ? TrendingUp : trend?.direction === 'down' ? TrendingDown : Minus;

  const body = (
    <>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-ipe-text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold tabular-nums text-ipe-text">{metric}</p>
      {trend ? (
        <p
          className={cn(
            'mt-1 inline-flex items-center gap-1 text-xs font-medium',
            trend.direction === 'up' && 'text-score-excellent',
            trend.direction === 'down' && 'text-score-risk',
            trend.direction === 'flat' && 'text-ipe-text-muted',
          )}
        >
          <TrendIcon size={12} aria-hidden />
          {trend.value ?? trend.direction}
        </p>
      ) : null}
    </>
  );

  const classes = cn(
    'rounded-lg border border-ipe-border border-s-4 bg-ipe-surface-card p-4 shadow-sm',
    statusAccent[status],
    onClick && 'cursor-pointer hover:bg-ipe-surface-alt/60',
    className,
  );

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={cn(classes, 'w-full text-start')} data-testid="kpi-tile">
        {body}
      </button>
    );
  }

  return (
    <div className={classes} data-testid="kpi-tile">
      {body}
    </div>
  );
}
