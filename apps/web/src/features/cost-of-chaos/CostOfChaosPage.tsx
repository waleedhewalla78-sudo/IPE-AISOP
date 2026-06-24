import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fetchCostOfChaos, type CostOfChaosData } from './api';

const PARETO_COLORS = ['#ef4444', '#f97316', '#eab308', '#3b82f6', '#8b5cf6', '#22c55e'];

function formatUsd(value: number): string {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function CostOfChaosPage() {
  const [period, setPeriod] = useState<'7d' | '30d'>('7d');
  const [data, setData] = useState<CostOfChaosData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchCostOfChaos(period);
        setData(result);
      } catch (err) {
        setData(null);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    })();
  }, [period]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4 p-6">
        <h1 className="text-2xl font-bold text-ipe-text">Cost of Chaos</h1>
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error ?? 'No data available'}
        </p>
        <Button variant="secondary" size="sm" onClick={() => setPeriod(period)}>
          Retry
        </Button>
      </div>
    );
  }

  const chartData = data.categories.map((c) => ({
    name: c.label,
    usd: c.usd,
    pct: c.pct,
    code: c.code,
  }));

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ipe-text">Cost of Chaos</h1>
          <p className="text-sm text-ipe-text-muted">
            Pareto breakdown of planning chaos costs — idle time, rework, expedite freight
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={period === '7d' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setPeriod('7d')}
          >
            7 days
          </Button>
          <Button
            variant={period === '30d' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setPeriod('30d')}
          >
            30 days
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Total Chaos Cost</h3>
          <p className="text-2xl font-bold text-red-600">{formatUsd(data.total_chaos_usd)}</p>
          <Badge variant="warning" className="mt-1">
            Period: {data.period}
          </Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Categories</h3>
          <p className="text-2xl font-bold text-ipe-text">{data.categories.length}</p>
          <Badge variant="default" className="mt-1">
            Non-zero categories
          </Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">War Room Links</h3>
          <p className="text-2xl font-bold text-ipe-text">{data.war_room_links.length}</p>
          <Link to="/war-room" className="mt-1 inline-block text-sm text-ipe-primary hover:underline">
            Open War Room →
          </Link>
        </Card>
      </div>

      <Card className="p-4">
        <h3 className="mb-4 font-medium">Pareto by Category</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
            <YAxis type="category" dataKey="name" width={120} />
            <Tooltip formatter={(value) => formatUsd(Number(value ?? 0))} />
            <Bar dataKey="usd" radius={[0, 4, 4, 0]}>
              {chartData.map((_, idx) => (
                <Cell key={idx} fill={PARETO_COLORS[idx % PARETO_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card className="p-4">
        <h3 className="mb-4 font-medium">Category Breakdown</h3>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
              <th className="pb-2 pr-4">Category</th>
              <th className="pb-2 pr-4 text-right">Cost (USD)</th>
              <th className="pb-2 text-right">Share</th>
            </tr>
          </thead>
          <tbody>
            {data.categories.map((cat) => (
              <tr key={cat.code} className="border-b border-ipe-border/50">
                <td className="py-2 pr-4 font-medium">{cat.label}</td>
                <td className="py-2 pr-4 text-right">{formatUsd(cat.usd)}</td>
                <td className="py-2 text-right">{cat.pct.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {data.top_mos.length > 0 && (
        <Card className="p-4">
          <h3 className="mb-4 font-medium">Top MOs by Chaos Cost</h3>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                <th className="pb-2 pr-4">MO</th>
                <th className="pb-2 pr-4">Primary Category</th>
                <th className="pb-2 text-right">Chaos USD</th>
              </tr>
            </thead>
            <tbody>
              {data.top_mos.map((mo) => (
                <tr key={mo.mo_id} className="border-b border-ipe-border/50">
                  <td className="py-2 pr-4 font-medium">{mo.mo_id.slice(0, 8)}…</td>
                  <td className="py-2 pr-4 capitalize">{mo.primary_category.replace(/_/g, ' ')}</td>
                  <td className="py-2 text-right font-semibold text-red-600">{formatUsd(mo.chaos_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
