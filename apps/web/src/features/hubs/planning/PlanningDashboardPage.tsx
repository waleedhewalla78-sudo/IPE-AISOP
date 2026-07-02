import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/lib/constants';
import { fetchKPIs, fetchQueue } from '@/features/control-tower/api';
import api from '@/lib/api';

interface PlanningStats {
  queueCount: number;
  avgFeasibility: number | null;
  atRisk: number;
  scenarioCount: number;
  scheduledOps: number;
}

export function PlanningDashboardPage() {
  const [stats, setStats] = useState<PlanningStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [kpis, queue, scenariosRes, scheduleRes] = await Promise.all([
          fetchKPIs(),
          fetchQueue(),
          api.get('/api/v1/resolution/scenarios').catch(() => ({ data: { data: [] } })),
          api.get('/api/v1/capacity/schedule/active').catch(() => ({ data: { data: { schedule: { assignments: [] } } } })),
        ]);
        const scenarios = (scenariosRes.data?.data ?? []) as unknown[];
        const assignments =
          (scheduleRes.data?.data?.schedule?.assignments as unknown[]) ??
          (scheduleRes.data?.data?.assignments as unknown[]) ??
          [];
        setStats({
          queueCount: queue.length,
          avgFeasibility: kpis?.avg_feasibility_score ?? null,
          atRisk: kpis?.orders_at_risk ?? 0,
          scenarioCount: scenarios.length,
          scheduledOps: assignments.length,
        });
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  const cards = [
    { label: 'MOs in queue', value: stats.queueCount, link: ROUTES.PLANNING_CONTROL_TOWER, action: 'View queue' },
    { label: 'Avg feasibility', value: stats.avgFeasibility != null ? `${stats.avgFeasibility.toFixed(1)}%` : '—', link: ROUTES.PLANNING_CONTROL_TOWER, action: 'KPIs' },
    { label: 'Orders at risk', value: stats.atRisk, link: ROUTES.PLANNING_RESOLUTION, action: 'Resolve' },
    { label: 'Resolution scenarios', value: stats.scenarioCount, link: ROUTES.PLANNING_RESOLUTION, action: 'Scenarios' },
    { label: 'Scheduled operations', value: stats.scheduledOps, link: ROUTES.PLANNING_SCHEDULE, action: 'Open Gantt' },
  ];

  return (
    <div className="space-y-6">
      <p className="text-sm text-ipe-text-muted">
        Planning team overview — detect constraints, compare scenarios, and build the schedule in one hub.
      </p>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {cards.map((c) => (
          <Card key={c.label} className="p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-ipe-text-muted">{c.label}</p>
            <p className="mt-2 text-3xl font-bold text-ipe-text">{c.value}</p>
            <Link to={c.link} className="mt-3 inline-block">
              <Button size="sm" variant="ghost">{c.action} →</Button>
            </Link>
          </Card>
        ))}
      </div>
    </div>
  );
}
