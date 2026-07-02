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



type Supplier = {

  id: string;

  name: string;

  category?: string;

  esg_score: number;

  risk_tier: string;

  risk?: { composite_score: number };

};



export function ProcurementDashboardPage() {

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);

  const [spendSummary, setSpendSummary] = useState<{ total: number; by_category: Record<string, number> } | null>(null);

  const [compliance, setCompliance] = useState<{ compliant: boolean; suppliers: unknown[] } | null>(null);

  const [loading, setLoading] = useState(true);

  const [checking, setChecking] = useState(false);



  const load = useCallback(async () => {

    setLoading(true);

    try {

      const [supRes, spendRes] = await Promise.all([

        fetch(`${apiBase()}/api/v1/suppliers`, { headers: authHeaders() }),

        fetch(`${apiBase()}/api/v1/procurement/spend`, { headers: authHeaders() }),

      ]);

      const supBody = await supRes.json() as { data?: { suppliers: Supplier[] } };

      const spendBody = await spendRes.json() as { data?: { summary: { total: number; by_category: Record<string, number> } } };

      setSuppliers(supBody.data?.suppliers ?? []);

      setSpendSummary(spendBody.data?.summary ?? null);

    } finally {

      setLoading(false);

    }

  }, []);



  useEffect(() => { void load(); }, [load]);



  const runCompliance = async () => {

    setChecking(true);

    try {

      const res = await fetch(`${apiBase()}/api/v1/procurement/compliance/check`, {

        method: 'POST',

        headers: authHeaders(),

        body: JSON.stringify({}),

      });

      const body = await res.json() as { data?: { compliant: boolean; suppliers: unknown[] } };

      setCompliance(body.data ?? null);

    } finally {

      setChecking(false);

    }

  };



  return (

    <div className="space-y-4">

      <div className="flex flex-wrap items-center justify-between gap-2">

        <div>

          <h2 className="text-xl font-bold text-ipe-text">Responsible Procurement</h2>

          <p className="text-sm text-ipe-text-muted">Supplier ESG, spend visibility, and compliance checks</p>

        </div>

        <Button onClick={() => void runCompliance()} disabled={checking}>{checking ? 'Checking…' : 'Run compliance check'}</Button>

      </div>



      {spendSummary && (

        <Card>

          <h3 className="mb-2 font-medium">Spend summary</h3>

          <p className="text-sm text-ipe-text">Total: ${spendSummary.total.toLocaleString()}</p>

          <ul className="mt-1 text-sm text-ipe-text-muted">

            {Object.entries(spendSummary.by_category).map(([cat, amt]) => (

              <li key={cat}>{cat}: ${amt.toLocaleString()}</li>

            ))}

          </ul>

        </Card>

      )}



      {compliance && (

        <Card>

          <p className="text-sm font-medium">{compliance.compliant ? 'All suppliers compliant' : 'Compliance gaps detected'}</p>

          <p className="text-sm text-ipe-text-muted">{compliance.suppliers.length} supplier(s) checked</p>

        </Card>

      )}



      {loading ? (

        <Card><p className="text-sm text-ipe-text-muted">Loading suppliers…</p></Card>

      ) : (

        <Card>

          <h3 className="mb-2 font-medium">Suppliers ({suppliers.length})</h3>

          <div className="overflow-x-auto">

            <table className="w-full text-sm">

              <thead>

                <tr className="text-left text-ipe-text-muted">

                  <th className="py-1 pr-4">Name</th>

                  <th className="py-1 pr-4">Category</th>

                  <th className="py-1 pr-4">ESG</th>

                  <th className="py-1 pr-4">Risk tier</th>

                  <th className="py-1">Composite</th>

                </tr>

              </thead>

              <tbody>

                {suppliers.map((s) => (

                  <tr key={s.id} className="border-t border-ipe-border">

                    <td className="py-1 pr-4">{s.name}</td>

                    <td className="py-1 pr-4">{s.category ?? '—'}</td>

                    <td className="py-1 pr-4">{s.esg_score}</td>

                    <td className="py-1 pr-4">{s.risk_tier}</td>

                    <td className="py-1">{s.risk?.composite_score?.toFixed(3) ?? '—'}</td>

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

