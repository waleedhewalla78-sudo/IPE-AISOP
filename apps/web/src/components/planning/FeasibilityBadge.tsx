/**
 * FeasibilityBadge — score circle + band label (+ optional trend).
 * Click opens global FeasibilityDrawer unless onClick is provided.
 */
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { ScoreBadge } from '@/components/ScoreBadge';
import { cn } from '@/lib/utils';
import { t } from '@/lib/i18n';
import { scoreBandLabel, scoreTextClass, scoreTier, scoreTierLabelKey } from '@/lib/scoreVisuals';
import { useFeasibilityDrawer } from './FeasibilityDrawerContext';

export type FeasibilityTrend = 'up' | 'down' | 'flat';

interface FeasibilityBadgeProps {
  score: number | null | undefined;
  showLabel?: boolean;
  trend?: FeasibilityTrend | null;
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  className?: string;
  moId?: string;
  productName?: string;
  constraints?: string[];
}

export function FeasibilityBadge({
  score,
  showLabel = true,
  trend = null,
  size = 'md',
  onClick,
  className,
  moId,
  productName,
  constraints,
}: FeasibilityBadgeProps) {
  const { openFeasibility } = useFeasibilityDrawer();
  const tier = scoreTier(score);
  const label =
    score == null
      ? t('controlTower.pending', 'Pending')
      : t(scoreTierLabelKey(tier), scoreBandLabel(score));
  const n = score == null || Number.isNaN(score) ? null : Math.round(score);

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  const handleClick = () => {
    if (onClick) {
      onClick();
      return;
    }
    openFeasibility({
      moId,
      productName,
      score,
      constraints,
    });
  };

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

  return (
    <button
      type="button"
      onClick={handleClick}
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
