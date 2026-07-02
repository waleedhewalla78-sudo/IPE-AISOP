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



type Material = {

  id: string;

  name: string;

  grade: string;

  category: string;

  cost_per_kg: number;

  sustainability_score: number;

  properties: Record<string, number>;

};



export function DesignAIPage() {

  const [materials, setMaterials] = useState<Material[]>([]);

  const [recommendations, setRecommendations] = useState<Array<{ name: string; score: number; rationale?: string }>>([]);

  const [compliance, setCompliance] = useState<{ compliant: boolean; checks: Array<{ rule: string; result: string }> } | null>(null);

  const [loading, setLoading] = useState(true);

  const [tensile, setTensile] = useState(300);

  const [maxCost, setMaxCost] = useState(5);

  const [busy, setBusy] = useState(false);



  const load = useCallback(async () => {

    setLoading(true);

    try {

      const res = await fetch(`${apiBase()}/api/v1/materials`, { headers: authHeaders() });

      const body = await res.json() as { data?: { materials: Material[] } };

      setMaterials(body.data?.materials ?? []);

    } finally {

      setLoading(false);

    }

  }, []);



  useEffect(() => { void load(); }, [load]);



  const recommend = async () => {

    setBusy(true);

    try {

      const res = await fetch(`${apiBase()}/api/v1/design/recommend`, {

        method: 'POST',

        headers: authHeaders(),

        body: JSON.stringify({ required_tensile_mpa: tensile, max_cost_per_kg: maxCost }),

      });

      const body = await res.json() as { data?: { recommendations: Array<{ name: string; score: number; rationale?: string }> } };

      setRecommendations(body.data?.recommendations ?? []);

    } finally {

      setBusy(false);

    }

  };



  const checkCompliance = async () => {

    setBusy(true);

    try {

      const res = await fetch(`${apiBase()}/api/v1/design/check-compliance`, {

        method: 'POST',

        headers: authHeaders(),

        body: JSON.stringify({ process_type: 'machining', parameters: { max_hardness_hrc: 42 } }),

      });

      const body = await res.json() as { data?: { compliant: boolean; checks: Array<{ rule: string; result: string }> } };

      setCompliance(body.data ?? null);

    } finally {

      setBusy(false);

    }

  };



  return (

    <div className="space-y-4">

      <div>

        <h2 className="text-xl font-bold text-ipe-text">Product Design AI</h2>

        <p className="text-sm text-ipe-text-muted">Material catalog, recommendations, and process compliance</p>

      </div>



      <Card>

        <h3 className="mb-2 font-medium">Recommend materials</h3>

        <div className="mb-3 flex flex-wrap gap-3 text-sm">

          <label className="flex items-center gap-2">

            Min tensile (MPa)

            <input type="number" value={tensile} onChange={(e) => setTensile(Number(e.target.value))} className="w-24 rounded border px-2 py-1" />

          </label>

          <label className="flex items-center gap-2">

            Max cost/kg

            <input type="number" value={maxCost} onChange={(e) => setMaxCost(Number(e.target.value))} className="w-24 rounded border px-2 py-1" />

          </label>

          <Button onClick={() => void recommend()} disabled={busy}>Recommend</Button>

          <Button variant="secondary" onClick={() => void checkCompliance()} disabled={busy}>Check machining compliance</Button>

        </div>

        {recommendations.length > 0 && (

          <ul className="space-y-1 text-sm">

            {recommendations.map((r) => (

              <li key={r.name}>{r.name} — score {r.score.toFixed(3)} {r.rationale && <span className="text-ipe-text-muted">({r.rationale})</span>}</li>

            ))}

          </ul>

        )}

        {compliance && (

          <p className="mt-2 text-sm">{compliance.compliant ? '✓ Process compliant' : '✗ Compliance issues'} · {compliance.checks.length} checks</p>

        )}

      </Card>



      {loading ? (

        <Card><p className="text-sm text-ipe-text-muted">Loading catalog…</p></Card>

      ) : (

        <Card>

          <h3 className="mb-2 font-medium">Engineering material catalog ({materials.length})</h3>

          <div className="overflow-x-auto">

            <table className="w-full text-sm">

              <thead>

                <tr className="text-left text-ipe-text-muted">

                  <th className="py-1 pr-4">Name</th>

                  <th className="py-1 pr-4">Category</th>

                  <th className="py-1 pr-4">Tensile MPa</th>

                  <th className="py-1 pr-4">Cost/kg</th>

                  <th className="py-1">ESG</th>

                </tr>

              </thead>

              <tbody>

                {materials.map((m) => (

                  <tr key={m.id} className="border-t border-ipe-border">

                    <td className="py-1 pr-4">{m.name}</td>

                    <td className="py-1 pr-4">{m.category}</td>

                    <td className="py-1 pr-4">{m.properties?.tensile_mpa ?? '—'}</td>

                    <td className="py-1 pr-4">{m.cost_per_kg}</td>

                    <td className="py-1">{m.sustainability_score}</td>

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

