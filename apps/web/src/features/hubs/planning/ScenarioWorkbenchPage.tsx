import { useCallback, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

interface ScenarioSummary {
  id: string;
  name: string;
  description?: string;
  status: string;
}

interface ScenarioDetail {
  id: string;
  name: string;
  parameters: Record<string, string>;
  results: { kpi_key: string; kpi_value: number }[];
}

const KPI_LABEL_KEYS: Record<string, string> = {
  otd_pct: 'scenarios.kpi.otd',
  avg_feasibility: 'scenarios.kpi.avgFeasibility',
  orders_at_risk: 'scenarios.kpi.ordersAtRisk',
  total_cost_usd: 'scenarios.kpi.totalCost',
  capacity_util_pct: 'scenarios.kpi.capacityUtil',
};

const BASELINE = {
  otd_pct: 87.5,
  avg_feasibility: 74.9,
  orders_at_risk: 1.0,
  total_cost_usd: 125000.0,
  capacity_util_pct: 82.0,
};

export function ScenarioWorkbenchPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selected, setSelected] = useState<ScenarioDetail[]>([]);
  const [name, setName] = useState('');
  const [demandDelta, setDemandDelta] = useState('10%');
  const [supplierDelay, setSupplierDelay] = useState('3');
  const [capacityReduction, setCapacityReduction] = useState('5%');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/scenario');
      setScenarios((res.data?.data?.scenarios ?? []) as ScenarioSummary[]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const loadDetail = async (id: string) => {
    const res = await api.get(`/api/v1/scenario/${id}`);
    const data = res.data?.data as ScenarioDetail;
    const kpis = Object.fromEntries((data.results ?? []).map((r) => [r.kpi_key, r.kpi_value]));
    const detail: ScenarioDetail = { ...data, parameters: data.parameters ?? {}, results: data.results ?? [] };
    setSelected((prev) => {
      const next = prev.filter((s) => s.id !== id);
      if (next.length >= 3) next.shift();
      return [...next, { ...detail, results: Object.entries(kpis).map(([k, v]) => ({ kpi_key: k, kpi_value: v })) }];
    });
  };

  const createAndSimulate = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const res = await api.post('/api/v1/scenario/simulate', {
        name: name.trim(),
        description: 'What-if sandbox',
        demand_change_pct: demandDelta,
        supplier_delay_days: supplierDelay,
        capacity_reduction_pct: capacityReduction,
        persist: true,
      });
      const sid = res.data?.data?.scenario_id as string;
      setName('');
      await load();
      if (sid) await loadDetail(sid);
    } finally {
      setBusy(false);
    }
  };

  const simulateExisting = async (id: string) => {
    setBusy(true);
    try {
      await api.post(`/api/v1/scenario/${id}/simulate`);
      await loadDetail(id);
    } finally {
      setBusy(false);
    }
  };

  const kpiValue = (detail: ScenarioDetail, key: string) =>
    detail.results.find((r) => r.kpi_key === key)?.kpi_value ?? null;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-ipe-text">{t('scenarios.title')}</h2>
        <p className="text-sm text-ipe-text-muted">{t('scenarios.subtitle')}</p>
      </div>

      <Card className="space-y-3">
        <h3 className="font-medium text-ipe-text">{t('scenarios.new')}</h3>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder={t('scenarios.name')} />
          <Input value={demandDelta} onChange={(e) => setDemandDelta(e.target.value)} placeholder={t('scenarios.demandDelta')} />
          <Input value={supplierDelay} onChange={(e) => setSupplierDelay(e.target.value)} placeholder={t('scenarios.supplierDelay')} />
          <Input value={capacityReduction} onChange={(e) => setCapacityReduction(e.target.value)} placeholder={t('scenarios.capacityReduction')} />
        </div>
        <Button onClick={() => void createAndSimulate()} disabled={busy || !name.trim()}>
          {t('scenarios.createSimulate')}
        </Button>
      </Card>

      <Card>
        <h3 className="mb-2 font-medium text-ipe-text">{t('scenarios.active')} ({scenarios.length}/3)</h3>
        {loading ? (
          <p className="text-sm text-ipe-text-muted">{t('scenarios.loading')}</p>
        ) : scenarios.length === 0 ? (
          <p className="text-sm text-ipe-text-muted">{t('scenarios.none')}</p>
        ) : (
          <ul className="space-y-2">
            {scenarios.map((s) => (
              <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 rounded border border-ipe-border px-3 py-2">
                <span className="text-sm font-medium">{s.name}</span>
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => void loadDetail(s.id)} disabled={busy}>
                    {t('scenarios.compare')}
                  </Button>
                  <Button size="sm" onClick={() => void simulateExisting(s.id)} disabled={busy}>
                    {t('scenarios.resimulate')}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {selected.length > 0 && (
        <Card>
          <h3 className="mb-3 font-medium text-ipe-text">{t('scenarios.baselineCompare')}</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-ipe-border text-start text-ipe-text-muted">
                  <th className="py-2 pe-4">{t('scenarios.kpi')}</th>
                  <th className="py-2 pe-4">{t('scenarios.baseline')}</th>
                  {selected.map((s) => (
                    <th key={s.id} className="py-2 pe-4">
                      {s.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.keys(KPI_LABEL_KEYS).map((key) => (
                  <tr key={key} className="border-b border-ipe-border/50">
                    <td className="py-2 pe-4">{t(KPI_LABEL_KEYS[key])}</td>
                    <td className="py-2 pe-4 font-semibold tabular-nums">{BASELINE[key as keyof typeof BASELINE]}</td>
                    {selected.map((s) => {
                      const val = kpiValue(s, key);
                      const base = BASELINE[key as keyof typeof BASELINE];
                      const delta = val != null ? val - base : null;
                      return (
                        <td key={s.id} className="py-2 pe-4 tabular-nums">
                          {val != null ? (
                            <>
                              <span className="font-semibold">{val}</span>
                              {delta != null && (
                                <span className={`ms-1 text-xs ${delta > 0 && key.includes('risk') ? 'text-red-600' : delta < 0 && key === 'otd_pct' ? 'text-red-600' : 'text-green-600'}`}>
                                  ({delta > 0 ? '+' : ''}
                                  {delta.toFixed(1)})
                                </span>
                              )}
                            </>
                          ) : (
                            '—'
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
