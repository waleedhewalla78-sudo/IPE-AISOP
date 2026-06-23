import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { KPICard } from './KPICard';
import { Card } from '@/components/ui/Card';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fetchQueue, fetchKPIs, getMockBottlenecks } from '../api';
import { FeasibilityWebSocket } from '@/lib/ws';
import type { MOQueueItem, KPI, BottleneckItem } from '../types';

const wsClient = new FeasibilityWebSocket();

function scoreColor(score: number | null): string {
  if (score === null) return 'text-ipe-text-muted';
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  return 'text-red-600';
}

function scoreBadge(score: number | null): 'success' | 'warning' | 'danger' | 'default' {
  if (score === null) return 'default';
  if (score >= 90) return 'success';
  if (score >= 70) return 'warning';
  return 'danger';
}

function scoreLabel(score: number | null): string {
  if (score === null) return 'Pending';
  if (score >= 90) return 'On Track';
  if (score >= 70) return 'At Risk';
  return 'Critical';
}

function rowBg(score: number | null): string {
  if (score === null) return '';
  if (score >= 90) return 'bg-green-50';
  if (score >= 70) return 'bg-yellow-50';
  return 'bg-red-50';
}

function constraintIcon(constraint: string | null): string {
  if (!constraint) return '\u2713';
  const icons: Record<string, string> = { material: 'M', capacity: 'C', labor: 'L', demand: 'D', bom: 'B' };
  return icons[constraint] ?? '?';
}

function bottleneckColor(pct: number): string {
  if (pct > 95) return 'bg-red-600';
  if (pct > 85) return 'bg-orange-500';
  if (pct > 70) return 'bg-yellow-400';
  return 'bg-green-500';
}

function kpiScoreColor(score: number | null): 'up' | 'down' | 'neutral' {
  if (score === null) return 'neutral';
  if (score >= 70) return 'up';
  return 'down';
}

function kpiBgColor(score: number | null): string {
  if (score === null) return 'bg-white';
  if (score >= 90) return 'bg-green-50 border-green-200';
  if (score >= 70) return 'bg-yellow-50 border-yellow-200';
  return 'bg-red-50 border-red-200';
}

export function ControlTowerPage() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState<MOQueueItem[]>([]);
  const [kpis, setKPIs] = useState<KPI | null>(null);
  const [bottlenecks, setBottlenecks] = useState<BottleneckItem[]>([]);
  const [loading, setLoading] = useState(true);

  const handleWsMessage = useCallback((data: unknown) => {
    const item = data as Partial<MOQueueItem>;
    if (!item.mo_id) return;
    setQueue((prev) => {
      const idx = prev.findIndex((q) => q.mo_id === item.mo_id);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { ...next[idx], ...item } as MOQueueItem;
        return next;
      }
      return [item as MOQueueItem, ...prev];
    });
  }, []);

  useEffect(() => {
    Promise.all([fetchQueue(), fetchKPIs(), getMockBottlenecks()]).then(([q, k, b]) => {
      setQueue(q);
      setKPIs(k);
      setBottlenecks(b);
      setLoading(false);
    });

    wsClient.onMessage(handleWsMessage);
    wsClient.connect();

    return () => {
      wsClient.disconnect();
    };
  }, [handleWsMessage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  const avgScore = kpis?.avg_feasibility_score ?? null;
  const activeBottlenecks = kpis?.active_bottlenecks ?? null;
  const ordersAtRisk = kpis?.orders_at_risk ?? null;
  const otdPct = kpis?.otd_pct ?? null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Control Tower</h1>
        <p className="text-sm text-ipe-text-muted">Production overview, risk queue, and bottleneck map</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Avg Feasibility Score"
          value={avgScore !== null ? `${avgScore}%` : '-'}
          trend={kpiScoreColor(avgScore)}
          subtitle="Overall avg"
          className={kpiBgColor(avgScore)}
        />
        <KPICard
          title="Active Bottlenecks"
          value={activeBottlenecks !== null ? activeBottlenecks : '-'}
          trend={activeBottlenecks !== null && activeBottlenecks > 0 ? 'down' : 'neutral'}
          subtitle="WC >85% util"
        />
        <KPICard
          title="Orders at Risk"
          value={ordersAtRisk !== null ? ordersAtRisk : '-'}
          trend={ordersAtRisk !== null && ordersAtRisk > 0 ? 'down' : 'neutral'}
          subtitle="Score &lt;70"
        />
        {otdPct !== null ? (
          <KPICard
            title="On-Time Delivery"
            value={`${otdPct}%`}
            trend={otdPct >= 80 ? 'up' : 'down'}
            subtitle="Last 30 days"
          />
        ) : (
          <div className="rounded-lg border border-ipe-border bg-gray-50 p-5 shadow-sm opacity-60">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-ipe-text-muted">On-Time Delivery</p>
                <p className="mt-1 text-xl font-semibold text-ipe-text-muted">Not available in Shadow Mode</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <h3 className="mb-3 font-medium">MO Risk Queue ({queue.length})</h3>
            <div className="overflow-x-auto">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>MO ID</TableHeader>
                  <TableHeader>Product</TableHeader>
                  <TableHeader>Customer</TableHeader>
                  <TableHeader>Required</TableHeader>
                  <TableHeader>Feasibility <span className="text-xs font-normal text-ipe-text-muted" title="Capacity & Labor scoring pending (Sprint 3)">*</span></TableHeader>
                  <TableHeader>Constraint</TableHeader>
                  <TableHeader />
                </TableRow>
              </TableHead>
              <tfoot>
                <TableRow>
                  <TableCell colSpan={7} className="text-xs text-ipe-text-muted italic pt-2">
                    * Capacity &amp; Labor scoring pending (Sprint 3) &mdash; scores are material-driven only.
                  </TableCell>
                </TableRow>
              </tfoot>
              <tbody>
                {queue.map((item) => (
                  <TableRow key={item.mo_id} className={rowBg(item.feasibility_score)}>
                    <TableCell className="font-medium">{item.mo_id}</TableCell>
                    <TableCell>{item.product_name}</TableCell>
                    <TableCell>{item.customer_name}</TableCell>
                    <TableCell>{new Date(item.required_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <span className={`font-semibold ${scoreColor(item.feasibility_score)}`}>
                        {item.feasibility_score !== null ? item.feasibility_score : '-'}
                      </span>
                      <Badge variant={scoreBadge(item.feasibility_score)} className="ml-2">
                        {scoreLabel(item.feasibility_score)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {item.primary_constraint ? (
                        <span className="inline-flex items-center gap-1 rounded bg-ipe-surface-alt px-2 py-0.5 text-xs font-medium">
                          <span className="font-bold">{constraintIcon(item.primary_constraint)}</span>
                          {item.primary_constraint}
                        </span>
                      ) : (
                        <span className="text-xs text-ipe-text-muted">None</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="secondary" onClick={() => navigate(`/resolution-center?mo_id=${item.mo_id}`)}>Resolve</Button>
                    </TableCell>
                  </TableRow>
                ))}
                {queue.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8 text-center text-sm text-ipe-text-muted">
                      No MOs in the queue.
                    </TableCell>
                  </TableRow>
                )}
              </tbody>
            </Table>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <h3 className="mb-3 font-medium">Bottleneck Map</h3>
            <p className="mb-4 text-xs text-ipe-text-muted">Work centers exceeding 85% utilization</p>
            <div className="space-y-4">
              {bottlenecks.map((b) => {
                const barPct = Math.min(b.utilization_pct, 100);
                return (
                  <div key={b.work_center_id}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium truncate">{b.work_center_name}</span>
                      <span className="text-ipe-text-muted tabular-nums">{b.utilization_pct}%</span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-gray-100">
                      <div
                        className={`h-full rounded-full transition-all ${bottleneckColor(b.utilization_pct)}`}
                        style={{ width: `${barPct}%` }}
                      />
                    </div>
                    <div className="mt-0.5 text-xs text-ipe-text-muted">
                      {b.utilization_pct > 95 ? 'Critical overload' : b.utilization_pct > 85 ? 'Bottleneck risk' : 'Moderate load'}
                    </div>
                  </div>
                );
              })}
              {bottlenecks.length === 0 && (
                <p className="text-sm text-ipe-text-muted">No bottlenecks detected.</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
