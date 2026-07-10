import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/lib/constants';
import api from '@/lib/api';

interface UnifiedKpi {
  label: string;
  value: string;
  source_tool: string;
  link_path: string | null;
}

interface ActivityItem {
  id: string;
  summary: string;
  source_tool: string;
  severity: string;
  occurred_at: string;
}

interface UnifiedDashboard {
  role: string;
  kpis: UnifiedKpi[];
  recent_activity: ActivityItem[];
  pending_actions: string[];
}

export function UnifiedWorkspacePage() {
  const [data, setData] = useState<UnifiedDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get('/api/v1/dashboard/unified');
        setData(res.data?.data ?? null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load unified dashboard');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-ipe-border bg-ipe-surface p-6 text-sm text-ipe-text-muted">
        {error ?? 'Unified dashboard unavailable'}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-ipe-text">Unified Workspace</h1>
        <p className="mt-1 text-sm text-ipe-text-muted">
          Sprint 7 cohesion view — cross-tool KPIs, activity, and pending actions ({data.role})
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {data.kpis.map((kpi) => (
          <Card key={kpi.label} className="p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-ipe-text-muted">{kpi.label}</p>
            <p className="mt-2 text-3xl font-bold text-ipe-text">{kpi.value}</p>
            <p className="mt-1 text-xs text-ipe-text-muted">{kpi.source_tool}</p>
            {kpi.link_path && (
              <Link to={kpi.link_path} className="mt-3 inline-block">
                <Button size="sm" variant="ghost">Open →</Button>
              </Link>
            )}
          </Card>
        ))}
      </div>

      {data.pending_actions.length > 0 && (
        <Card className="p-4">
          <h2 className="text-sm font-semibold text-ipe-text">Pending actions</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ipe-text-muted">
            {data.pending_actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ipe-text">Cross-tool activity</h2>
          <Link to={ROUTES.PLANNING_CONTROL_TOWER}>
            <Button size="sm" variant="ghost">Planning hub</Button>
          </Link>
        </div>
        {data.recent_activity.length === 0 ? (
          <p className="mt-4 text-sm text-ipe-text-muted">No activity events yet — sync or ingest via EIB.</p>
        ) : (
          <ul className="mt-4 divide-y divide-ipe-border">
            {data.recent_activity.map((ev) => (
              <li key={ev.id} className="flex gap-3 py-3 text-sm">
                <span className="shrink-0 rounded bg-ipe-surface-muted px-2 py-0.5 text-xs uppercase text-ipe-text-muted">
                  {ev.source_tool}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-ipe-text">{ev.summary}</p>
                  <p className="text-xs text-ipe-text-muted">{new Date(ev.occurred_at).toLocaleString()}</p>
                </div>
                <span className="text-xs text-ipe-text-muted">{ev.severity}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
