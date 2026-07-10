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
import api from '@/lib/api';

interface ForecastPoint {
  forecast_date: string;
  value: number;
  lower_bound: number | null;
  upper_bound: number | null;
}

interface OverlayRow {
  date: string;
  demand: number;
  capacity: number;
  gap: number;
}

const CAPACITY_BASELINE = 100;

export function ForecastOverlayWidget() {
  const [points, setPoints] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/demand/forecast', { params: { days: 14 } });
      const forecasts = (res.data?.data?.forecasts ?? []) as ForecastPoint[];
      setPoints(forecasts.slice(0, 14));
    } catch {
      setError('Forecast overlay unavailable');
      setPoints([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const chartData = useMemo<OverlayRow[]>(() => {
    const byDate = new Map<string, number>();
    for (const p of points) {
      const key = new Date(p.forecast_date).toLocaleDateString();
      byDate.set(key, (byDate.get(key) ?? 0) + p.value);
    }
    return Array.from(byDate.entries()).map(([date, demand]) => ({
      date,
      demand: Math.round(demand * 10) / 10,
      capacity: CAPACITY_BASELINE,
      gap: Math.round((demand - CAPACITY_BASELINE) * 10) / 10,
    }));
  }, [points]);

  const gapDays = chartData.filter((r) => r.gap > 0).length;

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="font-medium text-ipe-text">Demand vs Capacity (14d)</h3>
          <p className="text-xs text-ipe-text-muted">SES forecast overlay — gap days: {gapDays}</p>
        </div>
      </div>
      {loading ? (
        <p className="text-sm text-ipe-text-muted">Loading forecast overlay…</p>
      ) : error ? (
        <p className="text-sm text-ipe-text-muted">{error}</p>
      ) : chartData.length === 0 ? (
        <p className="text-sm text-ipe-text-muted">No forecast data. Run demand sense cycle.</p>
      ) : (
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-ipe-border" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="demand" fill="#3b82f6" fillOpacity={0.15} stroke="#3b82f6" name="Demand" />
              <Line type="monotone" dataKey="capacity" stroke="#22c55e" strokeWidth={2} name="Capacity ref" dot={false} />
              <Line type="monotone" dataKey="gap" stroke="#ef4444" strokeDasharray="4 4" name="Gap" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
