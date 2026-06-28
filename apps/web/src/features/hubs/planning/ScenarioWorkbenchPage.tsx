import { useCallback, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface ScenarioSummary {
  id: string;
  name: string;
  description?: string;
  status: string;
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

export function ScenarioWorkbenchPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [demandDelta, setDemandDelta] = useState('10%');
  const [results, setResults] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase()}/api/v1/scenario`, { headers: authHeaders() });
      const body = await res.json() as { data?: { scenarios?: ScenarioSummary[] } };
      setScenarios(body.data?.scenarios ?? []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const createScenario = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const res = await fetch(`${apiBase()}/api/v1/scenario`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ name: name.trim(), description: 'What-if sandbox' }),
      });
      const body = await res.json() as { data?: { scenario_id?: string } };
      const id = body.data?.scenario_id;
      if (id) {
        await fetch(`${apiBase()}/api/v1/scenario/${id}/parameters`, {
          method: 'PUT',
          headers: authHeaders(),
          body: JSON.stringify({
            parameters: [{ parameter_key: 'demand_change_pct', parameter_value: demandDelta }],
          }),
        });
        setSelectedId(id);
        setName('');
        await load();
      }
    } finally {
      setBusy(false);
    }
  };

  const simulate = async (id: string) => {
    setBusy(true);
    try {
      const res = await fetch(`${apiBase()}/api/v1/scenario/${id}/simulate`, {
        method: 'POST',
        headers: authHeaders(),
      });
      const body = await res.json() as { data?: { kpis?: Record<string, number> } };
      setResults(body.data?.kpis ?? null);
      setSelectedId(id);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-ipe-text">Scenario Workbench</h2>
        <p className="text-sm text-ipe-text-muted">Clone baseline, adjust demand/capacity/lead time, simulate KPIs</p>
      </div>

      <Card className="space-y-3">
        <h3 className="font-medium text-ipe-text">New scenario</h3>
        <div className="flex flex-wrap gap-2">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Scenario name" className="max-w-xs" />
          <Input value={demandDelta} onChange={(e) => setDemandDelta(e.target.value)} placeholder="Demand Δ e.g. 10%" className="max-w-[8rem]" />
          <Button onClick={() => void createScenario()} disabled={busy || !name.trim()}>Create</Button>
        </div>
      </Card>

      <Card>
        <h3 className="mb-2 font-medium text-ipe-text">Active scenarios</h3>
        {loading ? (
          <p className="text-sm text-ipe-text-muted">Loading…</p>
        ) : scenarios.length === 0 ? (
          <p className="text-sm text-ipe-text-muted">No scenarios yet.</p>
        ) : (
          <ul className="space-y-2">
            {scenarios.map((s) => (
              <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 rounded border border-ipe-border px-3 py-2">
                <span className="text-sm font-medium">{s.name}</span>
                <Button onClick={() => void simulate(s.id)} disabled={busy}>
                  Simulate
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {results && selectedId && (
        <Card>
          <h3 className="mb-2 font-medium text-ipe-text">Simulation results</h3>
          <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
            {Object.entries(results).map(([k, v]) => (
              <div key={k}>
                <dt className="text-ipe-text-muted">{k.replace(/_/g, ' ')}</dt>
                <dd className="font-semibold text-ipe-text">{v}</dd>
              </div>
            ))}
          </dl>
        </Card>
      )}
    </div>
  );
}
