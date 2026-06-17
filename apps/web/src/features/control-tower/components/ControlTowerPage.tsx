import { useEffect, useState } from 'react';
import { KPICard } from './KPICard';
import { Card } from '@/components/ui/Card';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fetchRiskQueue, getMockBottlenecks } from '../api';
import type { MORiskItem, BottleneckItem } from '../types';

function scoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  return 'text-red-600';
}

function scoreBadge(score: number): 'success' | 'warning' | 'danger' {
  if (score >= 90) return 'success';
  if (score >= 70) return 'warning';
  return 'danger';
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

export function ControlTowerPage() {
  const [riskQueue, setRiskQueue] = useState<MORiskItem[]>([]);
  const [bottlenecks] = useState<BottleneckItem[]>(() => getMockBottlenecks());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRiskQueue().then(queue => {
      setRiskQueue(queue);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  const onTimeDelivery = 85;
  const feasibilityScore = 78;
  const activeBottlenecks = 2;
  const ordersAtRisk = riskQueue.filter(r => r.feasibility_score < 70).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Control Tower</h1>
        <p className="text-sm text-ipe-text-muted">Production overview, risk queue, and bottleneck map</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title="On-Time Delivery" value={`${onTimeDelivery}%`} trend={onTimeDelivery >= 80 ? 'up' : 'down'} subtitle="Last 30 days" />
        <KPICard title="Feasibility Score" value={`${feasibilityScore}%`} trend={feasibilityScore >= 70 ? 'up' : 'down'} subtitle="Overall avg" />
        <KPICard title="Active Bottlenecks" value={activeBottlenecks} trend={activeBottlenecks > 0 ? 'down' : 'neutral'} subtitle="WC >85% util" />
        <KPICard title="Orders at Risk" value={ordersAtRisk} trend={ordersAtRisk > 0 ? 'down' : 'up'} subtitle="Score &lt;70" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <h3 className="mb-3 font-medium">MO Risk Queue ({riskQueue.length})</h3>
            <div className="overflow-x-auto">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>MO ID</TableHeader>
                  <TableHeader>Product</TableHeader>
                  <TableHeader>Customer</TableHeader>
                  <TableHeader>Required</TableHeader>
                  <TableHeader>Feasibility</TableHeader>
                  <TableHeader>Constraint</TableHeader>
                  <TableHeader />
                </TableRow>
              </TableHead>
              <tbody>
                {riskQueue.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.mo_id}</TableCell>
                    <TableCell>{item.product_name}</TableCell>
                    <TableCell>{item.customer_name}</TableCell>
                    <TableCell>{new Date(item.required_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <span className={`font-semibold ${scoreColor(item.feasibility_score)}`}>
                        {item.feasibility_score}
                      </span>
                      <Badge variant={scoreBadge(item.feasibility_score)} className="ml-2">
                        {item.feasibility_score >= 90 ? 'On Track' : item.feasibility_score >= 70 ? 'At Risk' : 'Critical'}
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
                      <Button size="sm" variant="secondary">Resolve</Button>
                    </TableCell>
                  </TableRow>
                ))}
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
