import { useCallback, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('access_token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
    try {
      const payload = JSON.parse(atob(token.split('.')[1] ?? '')) as { tenant_id?: string };
      if (payload.tenant_id) headers['X-Tenant-ID'] = payload.tenant_id;
    } catch { /* ignore */ }
  }
  return headers;
}

function apiBase(): string {
  return import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
}

export function SupplyPlanningPage() {
  const [network, setNetwork] = useState<{ facilities: unknown[]; lanes: unknown[] } | null>(null);
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase()}/api/v1/supply/network`, { headers: authHeaders() });
      const body = await res.json() as { data?: { facilities: unknown[]; lanes: unknown[] } };
      setNetwork(body.data ?? { facilities: [], lanes: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const generate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${apiBase()}/api/v1/supply/plan/generate`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ name: 'Multi-echelon plan', horizon_days: 30 }),
      });
      const body = await res.json() as { data?: Record<string, unknown> };
      setPlan(body.data ?? null);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-bold text-ipe-text">Supply Planning</h2>
          <p className="text-sm text-ipe-text-muted">Multi-echelon network visibility and replenishment</p>
        </div>
        <Button onClick={() => void generate()} disabled={generating}>{generating ? 'Generating…' : 'Generate plan'}</Button>
      </div>
      {loading ? (
        <Card><p className="text-sm text-ipe-text-muted">Loading network…</p></Card>
      ) : (
        <Card>
          <p className="text-sm text-ipe-text">Facilities: {(network?.facilities?.length ?? 0)} · Lanes: {(network?.lanes?.length ?? 0)}</p>
        </Card>
      )}
      {plan && (
        <Card>
          <h3 className="mb-2 font-medium">Latest plan</h3>
          <p className="text-sm text-ipe-text-muted">Network inventory: {String(plan.network_inventory_total ?? '—')}</p>
          <p className="text-sm text-ipe-text-muted">Recommended transfers: {Array.isArray(plan.recommended_transfers) ? plan.recommended_transfers.length : 0}</p>
        </Card>
      )}
    </div>
  );
}
