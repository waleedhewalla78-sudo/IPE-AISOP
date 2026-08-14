/**
 * FeasibilityBadge — score circle + band label (+ optional trend).
 * Wraps ScoreBadge / scoreVisuals for Streams 4–6.
 */
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { ScoreBadge } from '@/components/ScoreBadge';
import { cn } from '@/lib/utils';
import { t } from '@/lib/i18n';
import { scoreBandLabel, scoreTextClass, scoreTier, scoreTierLabelKey } from '@/lib/scoreVisuals';

export type FeasibilityTrend = 'up' | 'down' | 'flat';

interface FeasibilityBadgeProps {
  score: number | null | undefined;
  showLabel?: boolean;
  trend?: FeasibilityTrend | null;
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  className?: string;
}

export function FeasibilityBadge({
  score,
  showLabel = true,
  trend = null,
  size = 'md',
  onClick,
  className,
}: FeasibilityBadgeProps) {
  const tier = scoreTier(score);
  const label =
    score == null
      ? t('controlTower.pending', 'Pending')
      : t(scoreTierLabelKey(tier), scoreBandLabel(score));
  const n = score == null || Number.isNaN(score) ? null : Math.round(score);

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  const body = (
    <>
      {n == null ? (
        <span
          className={cn(
            'inline-flex items-center justify-center rounded-full bg-ipe-surface-alt text-ipe-text-muted',
            size === 'sm' && 'h-6 w-6 text-[10px]',
            size === 'md' && 'h-8 w-8 text-sm',
            size === 'lg' && 'h-10 w-10 text-base',
          )}
          aria-label={label}
        >
          —
        </span>
      ) : (
        <ScoreBadge score={n} size={size} />
      )}
      {showLabel ? (
        <span className={cn('text-xs font-medium', scoreTextClass(score))}>{label}</span>
      ) : null}
      {trend ? (
        <TrendIcon
          size={12}
          className={cn(
            trend === 'up' && 'text-score-excellent',
            trend === 'down' && 'text-score-risk',
            trend === 'flat' && 'text-ipe-text-muted',
          )}
          aria-hidden
        />
      ) : null}
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-md text-start hover:bg-ipe-surface-alt/80',
          className,
        )}
        data-testid="feasibility-badge"
        data-tier={tier}
      >
        {body}
      </button>
    );
  }

  return (
    <span
      className={cn('inline-flex items-center gap-1.5', className)}
      data-testid="feasibility-badge"
      data-tier={tier}
    >
      {body}
    </span>
  );
}
