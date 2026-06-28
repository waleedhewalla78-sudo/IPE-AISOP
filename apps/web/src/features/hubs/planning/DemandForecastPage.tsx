import { useCallback, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface ForecastRow {
  product_id: string;
  forecast_date: string;
  value: number;
  lower_bound: number | null;
  upper_bound: number | null;
  horizon_type: string;
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('access_token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
    try {
      const payload = JSON.parse(atob(token.split('.')[1] ?? '')) as { tenant_id?: string };
      if (payload.tenant_id) headers['X-Tenant-ID'] = payload.tenant_id;
    } catch {
      /* ignore */
    }
  }
  return headers;
}

function apiBase(): string {
  return import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
}

export function DemandForecastPage() {
  const [forecasts, setForecasts] = useState<ForecastRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [sensing, setSensing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/demand/forecast?horizon=short`, { headers: authHeaders() });
      const body = await res.json() as { success?: boolean; data?: { forecasts?: ForecastRow[] } };
      setForecasts(body.data?.forecasts ?? []);
    } catch {
      setError('Could not load forecasts. Ensure demand-svc is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const runSense = async () => {
    setSensing(true);
    try {
      await fetch(`${apiBase()}/api/v1/demand/sense`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ horizon: 'short', periods: 14 }),
      });
      await load();
    } finally {
      setSensing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-bold text-ipe-text">Demand Sensing</h2>
          <p className="text-sm text-ipe-text-muted">Short-term statistical forecasts from demand history + signals</p>
        </div>
        <Button onClick={() => void runSense()} disabled={sensing}>
          {sensing ? 'Running…' : 'Run sense cycle'}
        </Button>
      </div>
      {error && <Card><p className="text-sm text-red-600">{error}</p></Card>}
      {loading ? (
        <Card><p className="text-sm text-ipe-text-muted">Loading forecasts…</p></Card>
      ) : forecasts.length === 0 ? (
        <Card>
          <p className="text-sm text-ipe-text-muted">No forecasts yet. Click &quot;Run sense cycle&quot; to generate from demand lines.</p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-ipe-border text-left text-ipe-text-muted">
                  <th className="py-2 pr-4">Product</th>
                  <th className="py-2 pr-4">Date</th>
                  <th className="py-2 pr-4">Forecast</th>
                  <th className="py-2 pr-4">Band</th>
                </tr>
              </thead>
              <tbody>
                {forecasts.slice(0, 50).map((f, i) => (
                  <tr key={`${f.product_id}-${f.forecast_date}-${i}`} className="border-b border-ipe-border/50">
                    <td className="py-2 pr-4 font-mono text-xs">{f.product_id.slice(0, 8)}…</td>
                    <td className="py-2 pr-4">{new Date(f.forecast_date).toLocaleDateString()}</td>
                    <td className="py-2 pr-4">{f.value.toFixed(1)}</td>
                    <td className="py-2 pr-4 text-ipe-text-muted">
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
