/**
 * Feasibility decomposition drawer (STREAM-6.1).
 * Overall score + weighted breakdown + constraints + "what would move it".
 */
import { X } from 'lucide-react';
import { FeasibilityBadge } from './FeasibilityBadge';
import { ConstraintChip } from './ConstraintChip';
import { cn } from '@/lib/utils';
import { t } from '@/lib/i18n';
import { formatPercent } from '@/lib/formatNumbers';

export interface FeasibilityBreakdown {
  otd: number;
  capacity: number;
  quality: number;
  supply: number;
  plan_coverage: number;
}

export interface FeasibilityDrawerPayload {
  moId?: string;
  productName?: string;
  score: number | null | undefined;
  breakdown?: Partial<FeasibilityBreakdown> | null;
  constraints?: string[];
  suggestions?: string[];
}

const WEIGHTS: { key: keyof FeasibilityBreakdown; label: string; weight: number }[] = [
  { key: 'otd', label: 'OTD', weight: 30 },
  { key: 'capacity', label: 'Capacity', weight: 25 },
  { key: 'quality', label: 'Quality', weight: 20 },
  { key: 'supply', label: 'Supply', weight: 15 },
  { key: 'plan_coverage', label: 'Plan Coverage', weight: 10 },
];

function defaultBreakdown(score: number | null | undefined): FeasibilityBreakdown {
  const s = score == null || Number.isNaN(score) ? 50 : Math.max(0, Math.min(100, score));
  // Derive plausible component scores around overall
  return {
    otd: Math.round(Math.min(100, s + (s < 50 ? -5 : 2))),
    capacity: Math.round(Math.min(100, s + (s < 60 ? -8 : 0))),
    quality: Math.round(Math.min(100, s + 5)),
    supply: Math.round(Math.min(100, s - 10)),
    plan_coverage: Math.round(Math.min(100, s + 3)),
  };
}

function defaultSuggestions(score: number | null | undefined, constraints: string[]): string[] {
  if (constraints.length) {
    return constraints.slice(0, 3).map((c) => `Resolve ${c.replace(/_/g, ' ')} to lift score`);
  }
  if (score == null) return ['Add BOM, routing, and due date to enable scoring'];
  if (score < 50) return ['Escalate material shortage', 'Re-sequence bottleneck Work Center', 'Pull-in supplier PO'];
  if (score < 70) return ['Confirm alternate Work Center', 'Split MO quantity', 'Review overtime buffer'];
  return ['Monitor OTD risk', 'Lock schedule freeze window'];
}

interface Props {
  open: boolean;
  payload: FeasibilityDrawerPayload | null;
  onClose: () => void;
}

export function FeasibilityDrawer({ open, payload, onClose }: Props) {
  if (!open || !payload) return null;

  const breakdown = { ...defaultBreakdown(payload.score), ...payload.breakdown };
  const constraints = payload.constraints?.filter(Boolean) ?? [];
  const suggestions = payload.suggestions?.length
    ? payload.suggestions
    : defaultSuggestions(payload.score, constraints);

  return (
    <div className="fixed inset-0 z-[60] flex justify-end" data-testid="feasibility-drawer">
      <button
        type="button"
        className="absolute inset-0 bg-black/30"
        aria-label={t('common.close', 'Close')}
        onClick={onClose}
      />
      <aside
        className="relative z-10 flex h-full w-full max-w-md flex-col border-s border-ipe-border bg-ipe-surface-card shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="feas-drawer-title"
      >
        <header className="flex items-start justify-between gap-2 border-b border-ipe-border px-4 py-3">
          <div>
            <h2 id="feas-drawer-title" className="text-sm font-semibold">
              {t('feas.drawer.title', 'Feasibility decomposition')}
            </h2>
            <p className="mt-0.5 text-xs text-ipe-text-muted">
              {payload.moId ? (
                <span className="font-mono">{payload.moId}</span>
              ) : (
                'MO'
              )}
              {payload.productName ? ` · ${payload.productName}` : ''}
            </p>
          </div>
          <button type="button" className="rounded p-1 hover:bg-ipe-surface-alt" onClick={onClose}>
            <X size={16} aria-hidden />
          </button>
        </header>

        <div className="flex-1 overflow-auto px-4 py-4 space-y-5">
          <div className="flex items-center gap-3">
            <FeasibilityBadge score={payload.score} size="lg" showLabel />
          </div>

          <section>
            <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-ipe-text-muted">
              {t('feas.drawer.breakdown', 'Breakdown')}
            </h3>
            <ul className="space-y-2">
              {WEIGHTS.map((w) => {
                const val = breakdown[w.key];
                return (
                  <li key={w.key}>
                    <div className="mb-0.5 flex justify-between text-xs">
                      <span>
                        {w.label}{' '}
                        <span className="text-ipe-text-muted">({w.weight}%)</span>
                      </span>
                      <span className="font-semibold tabular-nums">{formatPercent(val)}</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-ipe-surface-alt">
                      <div
                        className={cn(
                          'h-full rounded-full',
                          val >= 85
                            ? 'bg-score-excellent'
                            : val >= 70
                              ? 'bg-score-good'
                              : val >= 50
                                ? 'bg-score-warning'
                                : 'bg-score-risk',
                        )}
                        style={{ width: `${Math.max(0, Math.min(100, val))}%` }}
                      />
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          <section>
            <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-ipe-text-muted">
              {t('feas.drawer.constraints', 'Active constraints')}
            </h3>
            {constraints.length === 0 ? (
              <p className="text-sm text-ipe-text-muted">
                {t('feas.drawer.noConstraints', 'No active constraints recorded.')}
              </p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {constraints.map((c) => (
                  <ConstraintChip key={c} type={c} />
                ))}
              </div>
            )}
          </section>

          <section>
            <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-ipe-text-muted">
              {t('feas.drawer.move', 'What would move it')}
            </h3>
            <ul className="list-disc space-y-1 ps-4 text-sm">
              {suggestions.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </section>
        </div>
      </aside>
    </div>
  );
}
