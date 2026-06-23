import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import api from '@/lib/api';

interface TwinResult {
  disruption_type: string;
  source_id: string;
  delay_days: number;
  impacted_mos: { mo_id: string; delay_days: number; revenue_at_risk?: number }[];
  total_cost_impact: number;
  resolve_time_ms?: number;
}

export function DigitalTwinPanel() {
  const [supplierId, setSupplierId] = useState('SUP-T2-001');
  const [delayDays, setDelayDays] = useState(14);
  const [baseline] = useState({ otd_pct: 92, total_cost: 0 });
  const [result, setResult] = useState<TwinResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/api/v1/digital-twin/disrupt', {
        disruption_type: 'supplier_delay',
        source_id: supplierId,
        delay_days: delayDays,
      });
      setResult(res.data?.data ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const deltaCost = result ? result.total_cost_impact - baseline.total_cost : 0;
  const deltaOtd = result
    ? Math.max(0, baseline.otd_pct - result.impacted_mos.length * 1.5)
    : baseline.otd_pct;

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-medium text-ipe-text">Digital Twin Sandbox</h3>
          <p className="text-xs text-ipe-text-muted">Clone baseline schedule and simulate disruptions without touching live CDM</p>
        </div>
        <Badge variant="default">Sandbox</Badge>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <label className="text-sm">
          <span className="mb-1 block text-xs text-ipe-text-muted">Supplier ID</span>
          <input
            className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-ipe-text-muted">Delay (days)</span>
          <input
            type="number"
            min={1}
            className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
            value={delayDays}
            onChange={(e) => setDelayDays(Number(e.target.value) || 1)}
          />
        </label>
        <div className="flex items-end">
          <Button onClick={runSimulation} disabled={loading}>
            {loading ? 'Simulating...' : 'Run disruption'}
          </Button>
        </div>
      </div>

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

      {result && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-4 rounded-md bg-ipe-surface-alt p-3 text-sm">
          <div>
            <p className="text-xs text-ipe-text-muted">Impacted MOs</p>
            <p className="font-semibold text-ipe-text">{result.impacted_mos.length}</p>
          </div>
          <div>
            <p className="text-xs text-ipe-text-muted">Cost delta</p>
            <p className={`font-semibold ${deltaCost > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {deltaCost >= 0 ? '+' : ''}${deltaCost.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-ipe-text-muted">OTD delta (est.)</p>
            <p className={`font-semibold ${deltaOtd < baseline.otd_pct ? 'text-red-600' : 'text-green-600'}`}>
              {(deltaOtd - baseline.otd_pct).toFixed(1)} pts
            </p>
          </div>
          <div>
            <p className="text-xs text-ipe-text-muted">Resolve time</p>
            <p className="font-semibold text-ipe-text">{result.resolve_time_ms ?? 0} ms</p>
          </div>
        </div>
      )}
    </Card>
  );
}
