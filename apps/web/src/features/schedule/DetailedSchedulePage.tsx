/**
 * Detailed Schedule — /plan/detailed-schedule (STREAM-5.3)
 * KPI band + frappe-gantt + task detail panel + Day/Week + WC/status filters.
 */
import { useEffect, useMemo, useState } from 'react';
import { KpiTile } from '@/components/planning/KpiTile';
import { FeasibilityBadge } from '@/components/planning/FeasibilityBadge';
import { FrappeGanttChart } from './components/FrappeGanttChart';
import { fetchActiveSchedule } from './api';
import {
  extractWorkCenters,
  rowsToFrappeTasks,
  type FrappeGanttTask,
} from './ganttAdapter';
import type { GanttRow } from './types';
import { t } from '@/lib/i18n';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/lib/constants';

export function DetailedSchedulePage() {
  const [rows, setRows] = useState<GanttRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'Day' | 'Week'>('Week');
  const [wcFilter, setWcFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState<FrappeGanttTask | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const active = await fetchActiveSchedule();
        if (!cancelled) setRows(active.rows);
      } catch {
        if (!cancelled) setRows([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const workCenters = useMemo(() => extractWorkCenters(rows), [rows]);

  const tasks = useMemo(
    () =>
      rowsToFrappeTasks(rows, {
        workCenterFilter: wcFilter || undefined,
        statusFilter: statusFilter || undefined,
      }),
    [rows, wcFilter, statusFilter],
  );

  const opCount = rows.reduce((n, r) => n + r.operations.length, 0);
  const moCount = rows.length;
  const delayed = rows.reduce(
    (n, r) => n + r.operations.filter((o) => o.status === 'delayed').length,
    0,
  );
  const avgFeas =
    rows.filter((r) => r.feasibility_score != null).length === 0
      ? null
      : Math.round(
          rows.reduce((s, r) => s + (r.feasibility_score ?? 0), 0) /
            rows.filter((r) => r.feasibility_score != null).length,
        );

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-3" data-testid="detailed-schedule">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold">{t('plan.detailedSchedule', 'Detailed Schedule')}</h1>
          <p className="text-xs text-ipe-text-muted">
            {t('plan.detailedSchedule.sub', 'Work Center Gantt · feasibility-colored bars')}
          </p>
        </div>
        <Link to={ROUTES.PLANNING_SCHEDULE} className="text-xs text-ipe-primary">
          {t('plan.openClassic', 'Classic Schedule')}
        </Link>
      </header>

      {/* KPI band — 6 tiles */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <KpiTile label="MOs" metric={moCount} status="neutral" />
        <KpiTile label="Operations" metric={opCount} status="neutral" />
        <KpiTile label="Work Centers" metric={workCenters.length} status="good" />
        <KpiTile
          label="Avg Feasibility"
          metric={avgFeas == null ? '—' : avgFeas}
          status={avgFeas != null && avgFeas < 70 ? 'warning' : 'good'}
        />
        <KpiTile
          label="Delayed"
          metric={delayed}
          status={delayed > 0 ? 'risk' : 'excellent'}
        />
        <KpiTile label="View" metric={viewMode} status="neutral" />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex rounded-md border border-ipe-border text-xs">
          {(['Day', 'Week'] as const).map((m) => (
            <button
              key={m}
              type="button"
              className={`px-3 py-1.5 ${viewMode === m ? 'bg-ipe-primary text-white' : 'bg-ipe-surface-card'}`}
              onClick={() => setViewMode(m)}
            >
              {m}
            </button>
          ))}
        </div>
        <select
          className="rounded-md border border-ipe-border bg-ipe-surface-card px-2 py-1.5 text-xs"
          value={wcFilter}
          onChange={(e) => setWcFilter(e.target.value)}
          aria-label="Filter work center"
        >
          <option value="">{t('plan.filter.allWc', 'All Work Centers')}</option>
          {workCenters.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-ipe-border bg-ipe-surface-card px-2 py-1.5 text-xs"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter status"
        >
          <option value="">{t('plan.filter.allStatus', 'All statuses')}</option>
          <option value="on_time">on_time</option>
          <option value="delayed">delayed</option>
          <option value="in_progress">in_progress</option>
          <option value="completed">completed</option>
        </select>
      </div>

      <div className="relative min-h-0 flex-1 overflow-hidden rounded-lg border border-ipe-border bg-ipe-surface-card">
        {loading ? (
          <p className="p-6 text-sm text-ipe-text-muted">{t('common.loading', 'Loading…')}</p>
        ) : (
          <FrappeGanttChart
            tasks={tasks}
            viewMode={viewMode}
            onTaskClick={setSelected}
            className="h-full p-2"
          />
        )}
      </div>

      {selected && selected.id !== 'placeholder' ? (
        <aside
          className="rounded-lg border border-ipe-border bg-ipe-surface-card p-4 shadow-sm"
          data-testid="gantt-task-detail"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold">{selected.name}</h2>
              <p className="text-xs text-ipe-text-muted">
                {selected.start} → {selected.end}
              </p>
            </div>
            <button
              type="button"
              className="text-xs text-ipe-text-muted"
              onClick={() => setSelected(null)}
            >
              Close
            </button>
          </div>
          {selected._meta ? (
            <dl className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
              <div>
                <dt className="text-ipe-text-muted">MO</dt>
                <dd className="font-mono">{selected._meta.mo_id}</dd>
              </div>
              <div>
                <dt className="text-ipe-text-muted">Work Center</dt>
                <dd>{selected._meta.work_center_name}</dd>
              </div>
              <div>
                <dt className="text-ipe-text-muted">Status</dt>
                <dd>{selected._meta.status}</dd>
              </div>
              <div>
                <dt className="text-ipe-text-muted">Feasibility</dt>
                <dd>
                  <FeasibilityBadge score={selected._meta.feasibility_score} size="sm" />
                </dd>
              </div>
            </dl>
          ) : null}
        </aside>
      ) : null}

      <style>{`
        .bar-feas-excellent .bar { fill: var(--color-score-excellent, #16a34a) !important; }
        .bar-feas-good .bar { fill: var(--color-score-good, #22c55e) !important; }
        .bar-feas-warning .bar { fill: var(--color-score-warning, #eab308) !important; }
        .bar-feas-risk .bar { fill: var(--color-score-risk, #f97316) !important; }
        .bar-feas-critical .bar { fill: var(--color-score-critical, #dc2626) !important; }
        .bar-feas-pending .bar { fill: #94a3b8 !important; }
      `}</style>
    </div>
  );
}
