import { useCallback, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface OrderRow {
  id: string;
  order_number: string;
  status: string;
  total_value: number;
}

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

export function OrderManagementPage() {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase()}/api/v1/orders`, { headers: authHeaders() });
      const body = await res.json() as { data?: { orders?: OrderRow[] } };
      setOrders(body.data?.orders ?? []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const promiseFirst = async () => {
    if (!orders[0]) return;
    await fetch(`${apiBase()}/api/v1/orders/${orders[0].id}/promise`, {
      method: 'POST',
      headers: authHeaders(),
    });
    await load();
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-bold text-ipe-text">Order Management</h2>
          <p className="text-sm text-ipe-text-muted">ATP/CTP promising and order exceptions</p>
        </div>
        {orders.length > 0 && (
          <Button variant="secondary" onClick={() => void promiseFirst()}>Promise latest order</Button>
        )}
      </div>
      {loading ? (
        <Card><p className="text-sm text-ipe-text-muted">Loading orders…</p></Card>
      ) : orders.length === 0 ? (
        <Card><p className="text-sm text-ipe-text-muted">No customer orders yet. Create via API POST /api/v1/orders.</p></Card>
      ) : (
        <Card>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-ipe-border text-left text-ipe-text-muted">
                <th className="py-2 pr-4">Order #</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Value</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-b border-ipe-border/50">
                  <td className="py-2 pr-4">{o.order_number}</td>
                  <td className="py-2 pr-4">{o.status}</td>
                  <td className="py-2 pr-4">${o.total_value.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
