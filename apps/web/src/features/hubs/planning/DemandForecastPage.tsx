import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

interface ForecastRow {
  product_id: string;
  forecast_date: string;
  value: number;
  lower_bound: number | null;
  upper_bound: number | null;
  horizon_days?: number;
}

const HORIZONS = [7, 14, 30] as const;

export function DemandForecastPage() {
  const [forecasts, setForecasts] = useState<ForecastRow[]>([]);
  const [horizonDays, setHorizonDays] = useState<number>(14);
  const [mapePct, setMapePct] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [sensing, setSensing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [forecastRes, accuracyRes] = await Promise.all([
        api.get('/api/v1/demand/forecast', { params: { days: horizonDays } }),
        api.get('/api/v1/demand/accuracy'),
      ]);
      setForecasts((forecastRes.data?.data?.forecasts ?? []) as ForecastRow[]);
      setMapePct(accuracyRes.data?.data?.mape_pct ?? null);
    } catch {
      setError(t('errors.forecastLoad'));
    } finally {
      setLoading(false);
    }
  }, [horizonDays]);

  useEffect(() => {
    void load();
  }, [load]);

  const chartData = useMemo(() => {
    const byDate = new Map<string, { demand: number; lower: number; upper: number }>();
    for (const f of forecasts) {
      const key = new Date(f.forecast_date).toLocaleDateString();
      const prev = byDate.get(key) ?? { demand: 0, lower: 0, upper: 0 };
      byDate.set(key, {
        demand: prev.demand + f.value,
        lower: prev.lower + (f.lower_bound ?? f.value),
        upper: prev.upper + (f.upper_bound ?? f.value),
      });
    }
    return Array.from(byDate.entries()).map(([date, v]) => ({
      date,
      demand: Math.round(v.demand * 10) / 10,
      lower: Math.round(v.lower * 10) / 10,
      upper: Math.round(v.upper * 10) / 10,
    }));
  }, [forecasts]);

  const runSense = async () => {
    setSensing(true);
    try {
      await api.post('/api/v1/demand/sense', { horizon: 'short', days: horizonDays });
      await load();
    } finally {
      setSensing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-bold text-ipe-text">{t('demand.title')}</h2>
          <p className="text-sm text-ipe-text-muted">
            {t('demand.subtitle')}
            {mapePct != null ? ` · ${t('demand.mape', undefined, { value: mapePct })}` : ` · ${t('demand.mapeHoldout')}`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {HORIZONS.map((d) => (
            <Button
              key={d}
              size="sm"
              variant={horizonDays === d ? 'primary' : 'secondary'}
              onClick={() => setHorizonDays(d)}
            >
              {d}d
            </Button>
          ))}
          <Button onClick={() => void runSense()} disabled={sensing}>
            {sensing ? t('demand.running') : t('demand.runSense')}
          </Button>
        </div>
      </div>

      {error && (
        <Card>
          <p className="text-sm text-red-600">{error}</p>
        </Card>
      )}

      {loading ? (
        <Card>
          <p className="text-sm text-ipe-text-muted">{t('demand.loading')}</p>
        </Card>
      ) : chartData.length > 0 ? (
        <Card>
          <h3 className="mb-2 font-medium text-ipe-text">{t('demand.forecastChart', undefined, { days: horizonDays })}</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="upper" stackId="band" stroke="none" fill="#93c5fd" name={t('demand.upper')} />
                <Area type="monotone" dataKey="lower" stackId="band" stroke="none" fill="#ffffff" name={t('demand.lower')} />
                <Line type="monotone" dataKey="demand" stroke="#2563eb" strokeWidth={2} name={t('demand.forecast')} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>
      ) : (
        <Card>
          <p className="text-sm text-ipe-text-muted">{t('demand.noForecasts')}</p>
        </Card>
      )}

      {forecasts.length > 0 && (
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-ipe-border text-start text-ipe-text-muted">
                  <th className="py-2 pe-4">{t('demand.product')}</th>
                  <th className="py-2 pe-4">{t('demand.date')}</th>
                  <th className="py-2 pe-4">{t('demand.forecast')}</th>
                  <th className="py-2 pe-4">{t('demand.band')}</th>
                </tr>
              </thead>
              <tbody>
                {forecasts.slice(0, 30).map((f, i) => (
                  <tr key={`${f.product_id}-${f.forecast_date}-${i}`} className="border-b border-ipe-border/50">
                    <td className="py-2 pe-4 font-mono text-xs tabular-nums">{f.product_id.slice(0, 8)}…</td>
                    <td className="py-2 pe-4 tabular-nums">{new Date(f.forecast_date).toLocaleDateString()}</td>
                    <td className="py-2 pe-4 tabular-nums">{f.value.toFixed(1)}</td>
                    <td className="py-2 pe-4 text-ipe-text-muted tabular-nums">
                      {f.lower_bound != null && f.upper_bound != null
                        ? `${f.lower_bound.toFixed(1)} – ${f.upper_bound.toFixed(1)}`
                        : '—'}
                    </td>
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
