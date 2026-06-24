import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  fetchDisruptions,
  fetchMitigationScenarios,
  fetchRecoveryPlan,
  type DisruptionEvent,
  type MitigationScenario,
  type RecoveryPlan,
} from '../api';

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-300',
  high: 'bg-amber-100 text-amber-800 border-amber-300',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  low: 'bg-green-100 text-green-800 border-green-300',
};

export function WarRoomPage() {
  const [disruptions, setDisruptions] = useState<DisruptionEvent[]>([]);
  const [mitigations, setMitigations] = useState<MitigationScenario[]>([]);
  const [recoveryPlan, setRecoveryPlan] = useState<RecoveryPlan | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [d, m] = await Promise.all([fetchDisruptions(), fetchMitigationScenarios()]);
      setDisruptions(d);
      setMitigations(m);
      const disruptionId = d[0]?.id;
      const plan = await fetchRecoveryPlan(disruptionId);
      setRecoveryPlan(plan);
      setLoading(false);
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  const totalImpacted = disruptions.reduce((s, d) => s + d.impacted_mos.length, 0);
  const totalCost = disruptions.reduce((s, d) => s + d.total_cost_impact, 0);
  const activeCount = disruptions.filter(d => d.status === 'active').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">War Room</h1>
        <p className="text-sm text-ipe-text-muted">Automated disruption aggregation, impact analysis, and mitigation task assignment</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Active Disruptions</h3>
          <p className="text-2xl font-bold text-red-600">{activeCount}</p>
          <Badge variant="danger" className="mt-1">Requires action</Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Impacted MOs</h3>
          <p className="text-2xl font-bold text-ipe-text">{totalImpacted}</p>
          <Badge variant="warning" className="mt-1">Across all disruptions</Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Revenue at Risk</h3>
          <p className="text-2xl font-bold text-ipe-text">${(totalCost / 1e3).toFixed(0)}K</p>
          <Badge variant={totalCost > 500000 ? 'danger' : 'warning'} className="mt-1">
            {totalCost > 500000 ? 'High impact' : 'Moderate impact'}
          </Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Mitigation Options</h3>
          <p className="text-2xl font-bold text-green-600">{mitigations.length}</p>
          <Badge variant="success" className="mt-1">Available</Badge>
        </Card>
      </div>

      {/* Top 3 Recovery Options */}
      {recoveryPlan && recoveryPlan.recovery_options.length > 0 && (
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-medium">Top Recovery Options</h3>
            <Badge variant="default">
              {recoveryPlan.impacted_mo_count} MOs impacted
            </Badge>
          </div>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            {recoveryPlan.recovery_options.slice(0, 3).map((opt) => (
              <div
                key={opt.scenario_id}
                className="rounded border border-ipe-border p-4 ring-1 ring-transparent hover:ring-ipe-primary/20"
              >
                <div className="mb-2 flex items-center justify-between">
                  <Badge variant={opt.rank === 1 ? 'success' : 'default'}>
                    Rank #{opt.rank}
                  </Badge>
                  <span className="text-xs text-ipe-text-muted">
                    {opt.scenario_id.slice(0, 8)}…
                  </span>
                </div>
                <p className="mb-3 text-sm font-medium text-ipe-text">{opt.summary}</p>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-ipe-text-muted">Business score</span>
                    <span className="font-semibold text-green-600">
                      ${opt.business_score_usd.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ipe-text-muted">Activity cost</span>
                    <span className="font-semibold">
                      ${opt.activity_cost_usd.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ipe-text-muted">Delivery impact</span>
                    <span className="font-semibold">{opt.delivery_impact_days} days</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Disruption Events */}
      <Card>
        <h3 className="mb-4 font-medium">Active Disruption Events</h3>
        <div className="space-y-4">
          {disruptions.map(d => (
            <div key={d.id} className="rounded border border-ipe-border p-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-medium">{d.disruption_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                  <Badge variant={d.status === 'active' ? 'danger' : d.status === 'mitigating' ? 'warning' : 'success'}>
                    {d.status}
                  </Badge>
                </div>
                <span className="text-xs text-ipe-text-muted">{d.created_at}</span>
              </div>
              <div className="mb-3 grid grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-ipe-text-muted">Source: </span>
                  <span className="font-medium">{d.source_name} ({d.source_id})</span>
                </div>
                <div>
                  <span className="text-ipe-text-muted">Delay: </span>
                  <span className="font-semibold text-red-600">{d.delay_days} days</span>
                </div>
                <div>
                  <span className="text-ipe-text-muted">MOs impacted: </span>
                  <span className="font-semibold">{d.impacted_mos.length}</span>
                </div>
              </div>
              {d.impacted_mos.length > 0 && (
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                      <th className="pb-1 pr-4">MO</th>
                      <th className="pb-1 pr-4 text-right">Delay (days)</th>
                      <th className="pb-1 pr-4">Components</th>
                      <th className="pb-1 pr-4 text-right">Revenue at Risk</th>
                      <th className="pb-1">Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.impacted_mos.map(mo => (
                      <tr key={mo.mo_id} className="border-b border-ipe-border/50">
                        <td className="py-1 pr-4 font-medium">{mo.mo_id}</td>
                        <td className="py-1 pr-4 text-right font-semibold text-red-600">{mo.delay_days.toFixed(1)}</td>
                        <td className="py-1 pr-4 text-xs">{mo.affected_components.join(', ')}</td>
                        <td className="py-1 pr-4 text-right">${(mo.revenue_at_risk / 1e3).toFixed(0)}K</td>
                        <td className="py-1">
                          <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${SEVERITY_COLOR[mo.severity]}`}>
                            {mo.severity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Mitigation Scenarios */}
      <Card>
        <h3 className="mb-4 font-medium">Mitigation Scenarios</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {mitigations.map(m => (
            <div key={m.id} className="rounded border border-ipe-border p-4">
              <h4 className="mb-2 font-medium">{m.name}</h4>
              <p className="mb-3 text-xs text-ipe-text-muted">{m.description}</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Cost</span>
                  <span className="font-semibold">${(m.cost_impact / 1e3).toFixed(0)}K</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">OTD Impact</span>
                  <span className="font-semibold text-green-600">+{m.otd_impact_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Delay Reduction</span>
                  <span className="font-semibold">{m.delay_reduction_days} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Confidence</span>
                  <span className="font-semibold">{(m.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <button className="mt-3 w-full rounded bg-ipe-primary px-3 py-1.5 text-sm font-medium text-white hover:bg-ipe-primary-dark">
                Assign Task
              </button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}