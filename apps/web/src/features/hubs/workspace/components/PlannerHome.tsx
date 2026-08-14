/**
 * Planner Home layout (STREAM-4.3) — feasibility heatmap, MO risk queue, exceptions + Copilot.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { FeasibilityBadge } from '@/components/planning/FeasibilityBadge';
import { ConstraintChip } from '@/components/planning/ConstraintChip';
import { DateCell } from '@/components/ui/DateCell';
import { fetchRiskQueue } from '@/features/control-tower/api';
import type { MORiskItem } from '@/features/control-tower/types';
import type { WorkspaceDashboard } from '@/features/hubs/workspace/types';
import { ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';
import { scoreTier } from '@/lib/scoreVisuals';

interface Props {
  dashboard: WorkspaceDashboard;
}

export function PlannerHome({ dashboard }: Props) {
  const [queue, setQueue] = useState<MORiskItem[]>([]);

  useEffect(() => {
    void fetchRiskQueue().then(setQueue);
  }, []);

  const scored = useMemo(
    () => queue.filter((q) => q.feasibility_score != null && q.feasibility_score > 0),
    [queue],
  );

  const bandCounts = useMemo(() => {
    const counts = { escalate: 0, action: 0, review: 0, good: 0, excellent: 0 };
    for (const m of scored) {
      const tier = scoreTier(m.feasibility_score);
      if (tier === 'critical' || tier === 'risk') counts.escalate += 1;
      else if (tier === 'warning') counts.action += 1;
      else if (tier === 'good') counts.review += 1;
      else if (tier === 'excellent') counts.excellent += 1;
      else counts.good += 1;
    }
    return counts;
  }, [scored]);

  const materials = dashboard.actions.filter(
    (a) =>
      a.source?.toLowerCase().includes('material') ||
      a.title?.toLowerCase().includes('material') ||
      a.detail?.toLowerCase().includes('bom'),
  );

  return (
    <div className="space-y-4" data-testid="planner-home" data-role="planner">
      {/* Feasibility heatmap */}
      <section className="rounded-lg border border-ipe-border bg-ipe-surface-card p-4">
        <h2 className="mb-3 text-sm font-semibold">
          {t('home.planner.heatmap', 'Schedule feasibility heatmap')}
        </h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {(
            [
              ['escalate', bandCounts.escalate, 'bg-score-critical/20 border-score-critical'],
              ['action', bandCounts.action, 'bg-score-risk/20 border-score-risk'],
              ['review', bandCounts.review, 'bg-score-warning/20 border-score-warning'],
              ['good', bandCounts.good, 'bg-score-good/20 border-score-good'],
              ['excellent', bandCounts.excellent, 'bg-score-excellent/20 border-score-excellent'],
            ] as const
          ).map(([key, n, cls]) => (
            <div key={key} className={`rounded-md border px-3 py-4 text-center ${cls}`}>
              <p className="text-2xl font-bold tabular-nums">{n}</p>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-ipe-text-muted">
                {key}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* MO risk queue */}
      <section className="rounded-lg border border-ipe-border bg-ipe-surface-card">
        <header className="flex items-center justify-between border-b border-ipe-border px-4 py-2">
          <h2 className="text-sm font-semibold">{t('home.planner.queue', 'MO risk queue')}</h2>
          <Link to={ROUTES.PLANNING_CONTROL_TOWER} className="text-xs text-ipe-primary">
            {t('home.planner.openCT', 'Control Tower')}
          </Link>
        </header>
        {scored.length === 0 ? (
          <p className="p-4 text-sm text-ipe-text-muted">
            {t(
              'home.empty.queue',
              'No scored MOs yet. Run seed-startrans-demo.ps1 or upload Excel data.',
            )}{' '}
            <Link to={ROUTES.ADMIN_DATA_UPLOAD} className="text-ipe-primary">
              Upload
            </Link>
          </p>
        ) : (
          <div className="max-h-80 overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-ipe-surface-alt text-xs text-ipe-text-muted">
                <tr>
                  <th className="px-3 py-2">MO</th>
                  <th className="px-3 py-2">Product</th>
                  <th className="px-3 py-2">Due</th>
                  <th className="px-3 py-2">Feasibility</th>
                  <th className="px-3 py-2">Constraint</th>
                </tr>
              </thead>
              <tbody>
                {scored.slice(0, 20).map((r) => (
                  <tr key={r.mo_id} className="border-t border-ipe-border/50">
                    <td className="px-3 py-2 font-mono text-xs">{r.mo_id}</td>
                    <td className="px-3 py-2">{r.product_name || '—'}</td>
                    <td className="px-3 py-2">
                      <DateCell value={r.required_date} />
                    </td>
                    <td className="px-3 py-2">
                      <FeasibilityBadge score={r.feasibility_score} size="sm" />
                    </td>
                    <td className="px-3 py-2">
                      {r.primary_constraint ? <ConstraintChip type={r.primary_constraint} /> : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Material exceptions + Copilot prompt */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-ipe-border bg-ipe-surface-card p-4">
          <h2 className="mb-2 text-sm font-semibold">
            {t('home.planner.materials', 'Material exceptions')}
          </h2>
          {materials.length === 0 ? (
            <ul className="space-y-2 text-sm text-ipe-text-muted">
              <li>{t('home.planner.noMat', 'No open material exceptions.')}</li>
              <li className="text-ipe-text">Check BOM coverage on escalate-band MOs.</li>
            </ul>
          ) : (
            <ul className="space-y-2 text-sm">
              {materials.slice(0, 5).map((a) => (
                <li key={a.id} className="rounded-md bg-ipe-surface-alt px-3 py-2">
                  <p className="font-medium">{a.title}</p>
                  <p className="text-xs text-ipe-text-muted">{a.detail}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="rounded-lg border border-ai-accent/30 bg-ai-accent/5 p-4">
          <h2 className="mb-2 text-sm font-semibold text-ai-accent">
            {t('home.planner.copilotPrompt', 'Copilot prompt')}
          </h2>
          <p className="text-sm text-ipe-text">
            {t(
              'home.planner.copilotHint',
              'Ask: “Which MOs will miss OTD this week and what is the cheapest recovery?”',
            )}
          </p>
          <Link
            to={ROUTES.AI_COPILOT}
            className="mt-3 inline-block rounded-md bg-ipe-primary px-3 py-1.5 text-xs font-medium text-white"
          >
            {t('home.planner.openCopilot', 'Open Copilot')}
          </Link>
        </section>
      </div>
    </div>
  );
}
