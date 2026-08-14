/**
 * Executive Home layout (STREAM-4.2) — KPI row, Copilot band, risk + heatmap, scenarios.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { KpiTile } from '@/components/planning/KpiTile';
import { FeasibilityBadge } from '@/components/planning/FeasibilityBadge';
import { ConstraintChip } from '@/components/planning/ConstraintChip';
import { fetchRiskQueue } from '@/features/control-tower/api';
import type { MORiskItem } from '@/features/control-tower/types';
import type { WorkspaceDashboard } from '@/features/hubs/workspace/types';
import { ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';
import { DateCell } from '@/components/ui/DateCell';

interface Props {
  dashboard: WorkspaceDashboard;
}

function healthStatus(score: number): 'excellent' | 'good' | 'warning' | 'risk' | 'critical' {
  if (score >= 85) return 'excellent';
  if (score >= 70) return 'good';
  if (score >= 50) return 'warning';
  if (score >= 30) return 'risk';
  return 'critical';
}

export function ExecutiveHome({ dashboard }: Props) {
  const [risk, setRisk] = useState<MORiskItem[]>([]);

  useEffect(() => {
    void fetchRiskQueue().then((q) => setRisk(q.slice(0, 5)));
  }, []);

  const factory = dashboard.health.factory_score;
  const otd = dashboard.health.otd_current;
  const chaos = dashboard.kpis.orders_at_risk?.value ?? risk.length;
  const summary =
    dashboard.actions[0]?.title ??
    t(
      'home.exec.summaryFallback',
      `${risk.filter((r) => r.feasibility_score < 70).length} orders need attention; factory health ${Math.round(factory)}.`,
    );

  return (
    <div className="space-y-4" data-testid="executive-home" data-role="executive">
      {/* Row 1 — 200px KPI band */}
      <div className="grid h-[200px] grid-cols-1 gap-3 sm:grid-cols-3">
        <KpiTile
          label={t('home.exec.factoryHealth', 'Factory Health')}
          metric={Math.round(factory)}
          status={healthStatus(factory)}
          trend={{
            direction:
              dashboard.health.factory_trend === 'improving'
                ? 'up'
                : dashboard.health.factory_trend === 'declining'
                  ? 'down'
                  : 'flat',
          }}
        />
        <KpiTile
          label={t('home.exec.otd', 'OTD')}
          metric={`${Math.round(otd)}%`}
          status={healthStatus(otd)}
          trend={{
            direction: (dashboard.health.otd_previous ?? otd) <= otd ? 'up' : 'down',
            value: `${Math.round(otd - (dashboard.health.otd_previous ?? otd))} pts`,
          }}
        />
        <KpiTile
          label={t('home.exec.costOfChaos', 'Cost of Chaos')}
          metric={chaos}
          status={chaos > 5 ? 'risk' : chaos > 2 ? 'warning' : 'good'}
          onClick={() => {
            window.location.href = ROUTES.COMMAND_COST_OF_CHAOS;
          }}
        />
      </div>

      {/* Row 2 — Copilot summary band */}
      <div
        className="flex h-20 items-center gap-3 rounded-lg border border-ai-accent/30 bg-ai-accent/5 px-4"
        data-testid="exec-copilot-band"
      >
        <span className="text-[10px] font-bold uppercase tracking-widest text-ai-accent">
          {t('home.exec.copilot', 'Copilot')}
        </span>
        <p className="line-clamp-2 text-sm text-ipe-text">{summary}</p>
        <Link to={ROUTES.AI_COPILOT} className="ms-auto shrink-0 text-xs font-medium text-ipe-primary">
          {t('home.exec.openCopilot', 'Open')}
        </Link>
      </div>

      {/* Row 3 — Top 5 at risk + bottleneck heatmap */}
      <div className="grid h-[400px] grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="flex flex-col overflow-hidden rounded-lg border border-ipe-border bg-ipe-surface-card">
          <header className="border-b border-ipe-border px-4 py-2 text-sm font-semibold">
            {t('home.exec.topRisk', 'Top 5 Orders at Risk')}
          </header>
          <div className="flex-1 overflow-auto">
            {risk.length === 0 ? (
              <p className="p-4 text-sm text-ipe-text-muted">
                {t('home.empty.risk', 'No orders at risk. Seed Star Trans data or open Control Tower.')}
              </p>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-ipe-surface-alt text-xs text-ipe-text-muted">
                  <tr>
                    <th className="px-3 py-2">MO</th>
                    <th className="px-3 py-2">Product</th>
                    <th className="px-3 py-2">Due</th>
                    <th className="px-3 py-2">Score</th>
                    <th className="px-3 py-2">Constraint</th>
                  </tr>
                </thead>
                <tbody>
                  {risk.map((r) => (
                    <tr key={r.mo_id} className="border-t border-ipe-border/60">
                      <td className="px-3 py-2 font-mono text-xs">{r.mo_id}</td>
                      <td className="px-3 py-2">{r.product_name || '—'}</td>
                      <td className="px-3 py-2">
                        <DateCell value={r.required_date} />
                      </td>
                      <td className="px-3 py-2">
                        <FeasibilityBadge score={r.feasibility_score} size="sm" />
                      </td>
                      <td className="px-3 py-2">
                        {r.primary_constraint ? (
                          <ConstraintChip type={r.primary_constraint} />
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <section className="flex flex-col overflow-hidden rounded-lg border border-ipe-border bg-ipe-surface-card">
          <header className="border-b border-ipe-border px-4 py-2 text-sm font-semibold">
            {t('home.exec.bottleneck', 'Bottleneck heatmap')}
          </header>
          <div className="grid flex-1 grid-cols-2 gap-2 overflow-auto p-3 sm:grid-cols-3">
            {dashboard.capacity.length === 0 ? (
              <p className="col-span-full text-sm text-ipe-text-muted">
                {t('home.empty.capacity', 'No work center load yet.')}
              </p>
            ) : (
              dashboard.capacity.map((c) => {
                const u = Math.round(c.utilisation);
                const bg =
                  u >= 95
                    ? 'bg-score-critical/80 text-white'
                    : u >= 85
                      ? 'bg-score-risk/70 text-white'
                      : u >= 70
                        ? 'bg-score-warning/50'
                        : 'bg-score-good/40';
                return (
                  <div
                    key={c.wc_name}
                    className={`flex flex-col justify-between rounded-md p-3 ${bg}`}
                    title={`${c.wc_name}: ${u}%`}
                  >
                    <span className="text-xs font-medium">{c.wc_name}</span>
                    <span className="text-lg font-bold tabular-nums">{u}%</span>
                  </div>
                );
              })
            )}
          </div>
        </section>
      </div>

      {/* Row 4 — Scenarios + Delivery calendar */}
      <div className="grid h-[300px] grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-ipe-border bg-ipe-surface-card p-4">
          <h2 className="mb-2 text-sm font-semibold">{t('home.exec.scenarios', 'Active Scenarios')}</h2>
          <ul className="space-y-2 text-sm">
            <li className="rounded-md bg-ipe-surface-alt px-3 py-2">
              Baseline schedule — current week
            </li>
            <li className="rounded-md bg-ipe-surface-alt px-3 py-2">
              Expedite coil shortage recovery
            </li>
            <li className="rounded-md bg-ipe-surface-alt px-3 py-2">
              OT capacity +10% what-if
            </li>
          </ul>
          <Link to={ROUTES.PLANNING_SCENARIOS} className="mt-3 inline-block text-xs text-ipe-primary">
            {t('home.exec.openScenarios', 'Open Scenario Workbench')}
          </Link>
        </section>
        <section className="rounded-lg border border-ipe-border bg-ipe-surface-card p-4">
          <h2 className="mb-2 text-sm font-semibold">{t('home.exec.calendar', 'Delivery Calendar')}</h2>
          <div className="grid grid-cols-7 gap-1 text-center text-[10px] text-ipe-text-muted">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
              <div key={d} className="font-semibold">
                {d}
              </div>
            ))}
            {Array.from({ length: 14 }).map((_, i) => {
              const has = risk[i % Math.max(risk.length, 1)];
              return (
                <div
                  key={i}
                  className={`rounded py-2 ${has && i < risk.length ? 'bg-score-warning/30 font-medium text-ipe-text' : 'bg-ipe-surface-alt'}`}
                >
                  {i + 1}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
