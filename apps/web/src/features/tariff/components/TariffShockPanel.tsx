import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  runTariffShock,
  type MoMarginImpact,
  type SubstituteDraft,
  type TariffShockResult,
} from '../api';

function formatUsd(value: number): string {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function TariffShockPanel() {
  const [region, setRegion] = useState('Region_X');
  const [tariffDeltaPct, setTariffDeltaPct] = useState(25);
  const [marginThresholdPct, setMarginThresholdPct] = useState(15);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TariffShockResult | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runTariffShock({
        region,
        tariff_delta_pct: tariffDeltaPct,
        margin_threshold_pct: marginThresholdPct,
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-4">
        <h3 className="mb-1 font-semibold text-ipe-text">Tariff Shock Simulator</h3>
        <p className="mb-4 text-sm text-ipe-text-muted">
          Model a regional tariff increase and identify MOs below margin threshold with substitute drafts
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-ipe-text-muted">Region</label>
            <Input value={region} onChange={(e) => setRegion(e.target.value)} placeholder="Region_X" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-ipe-text-muted">Tariff delta (%)</label>
            <Input
              type="number"
              value={tariffDeltaPct}
              onChange={(e) => setTariffDeltaPct(Number(e.target.value))}
              min={0}
              max={100}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-ipe-text-muted">Margin threshold (%)</label>
            <Input
              type="number"
              value={marginThresholdPct}
              onChange={(e) => setMarginThresholdPct(Number(e.target.value))}
              min={0}
              max={100}
            />
          </div>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <Button onClick={handleRun} disabled={loading} variant="primary" size="sm">
            {loading ? 'Running...' : 'Run Shock Simulation'}
          </Button>
          {result && (
            <Badge variant={result.affected_mo_count > 0 ? 'danger' : 'success'}>
              {result.affected_mo_count} MO{result.affected_mo_count === 1 ? '' : 's'} affected
            </Badge>
          )}
        </div>
        {error && (
          <p className="mt-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}
      </Card>

      {result && (
        <>
          <Card className="p-4">
            <h3 className="mb-3 font-medium text-ipe-text">MOs Below Margin Threshold</h3>
            {result.mos_below_threshold.length === 0 ? (
              <p className="text-sm text-ipe-text-muted">No MOs fall below the margin threshold for this scenario.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                      <th className="pb-2 pr-4">MO</th>
                      <th className="pb-2 pr-4 text-right">Margin Before</th>
                      <th className="pb-2 pr-4 text-right">Margin After</th>
                      <th className="pb-2 text-right">Erosion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.mos_below_threshold.map((mo: MoMarginImpact) => (
                      <tr key={mo.mo_id} className="border-b border-ipe-border/50">
                        <td className="py-2 pr-4 font-medium">{mo.mo_id.slice(0, 8)}…</td>
                        <td className="py-2 pr-4 text-right">{formatUsd(mo.net_margin_before)}</td>
                        <td className="py-2 pr-4 text-right text-red-600">{formatUsd(mo.net_margin_after)}</td>
                        <td className="py-2 text-right font-semibold text-red-600">-{formatUsd(mo.erosion_usd)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card className="p-4">
            <h3 className="mb-3 font-medium text-ipe-text">Substitute Drafts</h3>
            {result.substitute_drafts.length === 0 ? (
              <p className="text-sm text-ipe-text-muted">No substitute drafts generated for this shock.</p>
            ) : (
              <div className="space-y-2">
                {result.substitute_drafts.map((draft: SubstituteDraft, idx) => (
                  <div
                    key={`${draft.mo_id}-${draft.from_material_id}-${idx}`}
                    className="flex flex-wrap items-center justify-between gap-2 rounded border border-ipe-border p-3 text-sm"
                  >
                    <div>
                      <span className="font-medium">MO {draft.mo_id.slice(0, 8)}…</span>
                      <span className="mx-2 text-ipe-text-muted">→</span>
                      <span className="text-ipe-text-muted">
                        {draft.from_material_id.slice(0, 8)} → {draft.to_material_id.slice(0, 8)}
                      </span>
                    </div>
                    <Badge variant={draft.status === 'pending_approval' ? 'warning' : 'default'}>
                      {draft.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
