/** 5-tier continuous severity gradient (IPE-UIUX-STRUCTURAL-ANALYSIS Priority 2). */

export type ScoreTier = 'excellent' | 'good' | 'warning' | 'risk' | 'critical' | 'pending';

export function scoreTier(score: number | null | undefined): ScoreTier {
  if (score == null || Number.isNaN(score)) return 'pending';
  if (score >= 90) return 'excellent';
  if (score >= 80) return 'good';
  if (score >= 70) return 'warning';
  if (score >= 50) return 'risk';
  return 'critical';
}

export function scoreTierLabelKey(tier: ScoreTier): string {
  switch (tier) {
    case 'excellent':
      return 'controlTower.scoreExcellent';
    case 'good':
      return 'controlTower.scoreGood';
    case 'warning':
      return 'controlTower.scoreWarning';
    case 'risk':
      return 'controlTower.scoreRisk';
    case 'critical':
      return 'controlTower.scoreCritical';
    default:
      return 'controlTower.pending';
  }
}

/** Text color classes for score numbers / badges. */
export function scoreTextClass(score: number | null | undefined): string {
  switch (scoreTier(score)) {
    case 'excellent':
      return 'text-score-excellent';
    case 'good':
      return 'text-score-good';
    case 'warning':
      return 'text-score-warning';
    case 'risk':
      return 'text-score-risk';
    case 'critical':
      return 'text-score-critical';
    default:
      return 'text-ipe-text-muted';
  }
}

export function scoreBadgeClass(score: number | null | undefined): string {
  switch (scoreTier(score)) {
    case 'excellent':
      return 'bg-score-excellent/15 text-score-excellent ring-1 ring-score-excellent/30';
    case 'good':
      return 'bg-score-good/15 text-score-good ring-1 ring-score-good/30';
    case 'warning':
      return 'bg-score-warning/15 text-score-warning ring-1 ring-score-warning/30';
    case 'risk':
      return 'bg-score-risk/15 text-score-risk ring-1 ring-score-risk/30';
    case 'critical':
      return 'bg-score-critical/20 text-score-critical ring-1 ring-score-critical/40';
    default:
      return 'bg-ipe-surface-alt text-ipe-text-muted';
  }
}

export function scoreRowBg(score: number | null | undefined): string {
  switch (scoreTier(score)) {
    case 'excellent':
      return 'bg-emerald-50/80';
    case 'good':
      return 'bg-teal-50/70';
    case 'warning':
      return 'bg-amber-50/80';
    case 'risk':
      return 'bg-red-50/80';
    case 'critical':
      return 'bg-red-100/90';
    default:
      return '';
  }
}

/** Gradient fill for score badge (0–100). */
export function scoreGradientStyle(score: number | null | undefined): Record<string, string> | undefined {
  if (score == null) return undefined;
  const pct = Math.max(0, Math.min(100, score));
  return {
    background: `linear-gradient(90deg, var(--score-critical) 0%, var(--score-risk) 25%, var(--score-warning) 50%, var(--score-good) 75%, var(--score-excellent) 100%)`,
    backgroundSize: '100% 100%',
    clipPath: `inset(0 ${100 - pct}% 0 0)`,
  };
}

export function constraintIcon(constraint: string | null | undefined): string {
  if (!constraint) return '✓';
  const key = constraint.toLowerCase();
  const icons: Record<string, string> = {
    material: '📦',
    capacity: '⚙️',
    bom: '📋',
    demand: '📅',
    delivery: '📅',
    labor: '👷',
    labour: '👷',
  };
  return icons[key] ?? '?';
}

export function constraintLabelKey(constraint: string): string {
  const key = constraint.toLowerCase();
  if (key === 'labour') return 'resolution.constraint.labor';
  return `resolution.constraint.${key}`;
}

/** Normalize constraint to one of the 3 primary APS types (or other). */
export type ConstraintKind = 'material' | 'capacity' | 'labor' | 'other';

export function constraintKind(constraint: string | null | undefined): ConstraintKind {
  if (!constraint) return 'other';
  const key = constraint.toLowerCase();
  if (key === 'material' || key === 'bom' || key === 'supply') return 'material';
  if (key === 'capacity' || key === 'machine' || key === 'wc') return 'capacity';
  if (key === 'labor' || key === 'labour' || key === 'operator') return 'labor';
  return 'other';
}

/** Tailwind text/bg helpers for ConstraintChip. */
export function constraintChipClass(constraint: string | null | undefined): string {
  switch (constraintKind(constraint)) {
    case 'material':
      return 'bg-constraint-material/15 text-constraint-material ring-1 ring-constraint-material/30';
    case 'capacity':
      return 'bg-constraint-capacity/15 text-constraint-capacity ring-1 ring-constraint-capacity/30';
    case 'labor':
      return 'bg-constraint-labor/15 text-constraint-labor ring-1 ring-constraint-labor/30';
    default:
      return 'bg-ipe-surface-alt text-ipe-text-muted ring-1 ring-ipe-border';
  }
}

/** Human band label for FeasibilityBadge (EN fallback). */
export function scoreBandLabel(score: number | null | undefined): string {
  switch (scoreTier(score)) {
    case 'excellent':
      return 'Excellent';
    case 'good':
      return 'Good';
    case 'warning':
      return 'Review';
    case 'risk':
      return 'Action today';
    case 'critical':
      return 'Escalate';
    default:
      return 'Pending';
  }
}
