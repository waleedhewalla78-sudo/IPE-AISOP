import { useEffect, useState } from 'react';
import api from '@/lib/api';

interface PortalOrder {
  order_number: string;
  status: string;
  delivery_date?: string | null;
  confidence: string;
  color: string;
  invoice_status: string;
}

export function CustomerPortalPage() {
  const [orders, setOrders] = useState<PortalOrder[]>([]);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/v1/orders/portal/summary');
        setOrders(res.data?.data?.orders ?? []);
      } catch {
        setNote('Portal API unavailable — demo empty state (read-only).');
        setOrders([]);
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-ipe-text">Customer Portal</h1>
        <p className="mt-1 text-sm text-ipe-text-muted">
          Read-only order tracking · delivery confidence · invoice status (A8)
        </p>
      </header>
      {note ? <p className="text-sm text-amber-700">{note}</p> : null}
      <div className="overflow-hidden rounded-lg border border-ipe-border bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-ipe-border bg-ipe-surface-alt text-ipe-text-muted">
            <tr>
              <th className="px-4 py-3">Order</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Delivery</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Invoice</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-ipe-text-muted" colSpan={5}>
                  No active orders to display.
                </td>
              </tr>
            ) : (
              orders.map((o) => (
                <tr key={o.order_number} className="border-b border-ipe-border/60">
                  <td className="px-4 py-3 font-medium">{o.order_number}</td>
                  <td className="px-4 py-3">{o.status}</td>
                  <td className="px-4 py-3">{o.delivery_date || '—'}</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        o.color === 'green'
                          ? 'text-emerald-700'
                          : o.color === 'red'
                            ? 'text-red-700'
                            : 'text-amber-700'
                      }
                    >
                      {o.confidence}
                    </span>
                  </td>
                  <td className="px-4 py-3">{o.invoice_status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
