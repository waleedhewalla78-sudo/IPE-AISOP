import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/lib/constants';
import { fetchExecutiveSummary } from '@/features/executive/api';
import { fetchCostOfChaos } from '@/features/cost-of-chaos/api';
import api from '@/lib/api';

interface CommandStats {
  activeAlerts: number;
  aiOtd: number | null;
  chaosUsd: number;
  recoveryOptions: number;
  delayCategories: number;
}

export function CommandCenterDashboardPage() {
  const [stats, setStats] = useState<CommandStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [summary, chaos, alertsRes, recoveryRes, delayRes] = await Promise.all([
          fetchExecutiveSummary(),
          fetchCostOfChaos('7d'),
          api.get('/api/v1/dashboard/alerts').catch(() => ({ data: { data: { alerts: [] } } })),
          api.get('/api/v1/war-room/recovery-plan').catch(() => ({ data: { data: { recovery_options: [] } } })),
          api.get('/api/v1/analytics/delay-breakdown').catch(() => ({ data: { data: [] } })),
        ]);
        const alerts = (alertsRes.data?.data?.alerts ?? alertsRes.data?.data ?? []) as unknown[];
        const recovery = (recoveryRes.data?.data?.recovery_options ?? []) as unknown[];
        const delays = (delayRes.data?.data ?? []) as unknown[];
        setStats({
          activeAlerts: Array.isArray(alerts) ? alerts.length : 0,
          aiOtd: summary.ai_otd_pct,
          chaosUsd: chaos.total_chaos_usd,
          recoveryOptions: recovery.length,
          delayCategories: delays.length,
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
    { label: 'Active alerts', value: stats.activeAlerts, link: ROUTES.COMMAND_WAR_ROOM, action: 'War Room' },
    { label: 'AI OTD', value: stats.aiOtd != null ? `${stats.aiOtd.toFixed(1)}%` : 'N/A', link: ROUTES.COMMAND_EXECUTIVE, action: 'Executive' },
    { label: 'Cost of chaos (7d)', value: `$${stats.chaosUsd.toLocaleString()}`, link: ROUTES.COMMAND_COST_OF_CHAOS, action: 'Pareto' },
    { label: 'Recovery options', value: stats.recoveryOptions, link: ROUTES.COMMAND_WAR_ROOM, action: 'Mitigate' },
    { label: 'Delay categories', value: stats.delayCategories, link: ROUTES.COMMAND_EXECUTIVE, action: 'Analytics' },
  ];

  return (
    <div className="space-y-6">
      <p className="text-sm text-ipe-text-muted">
        Executive command view — disruptions, financial impact, and recovery in one place.
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
