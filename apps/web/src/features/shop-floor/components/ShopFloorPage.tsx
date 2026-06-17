import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import type { WorkCenterStatus, ShopFloorOrder, DelayAlert } from '../types';

const MOCK_WORK_CENTERS: WorkCenterStatus[] = [
  { id: 'WC001', name: 'Assembly Line 1', status: 'overloaded', load_pct: 97, active_orders: 4, operator_count: 6, operator_absent: 2 },
  { id: 'WC002', name: 'Machining Center', status: 'overloaded', load_pct: 89, active_orders: 3, operator_count: 4, operator_absent: 0 },
  { id: 'WC003', name: 'Packaging Station', status: 'operational', load_pct: 72, active_orders: 2, operator_count: 3, operator_absent: 0 },
  { id: 'WC004', name: 'Quality Lab', status: 'operational', load_pct: 45, active_orders: 1, operator_count: 2, operator_absent: 1 },
  { id: 'WC005', name: 'Heat Treat', status: 'maintenance', load_pct: 0, active_orders: 0, operator_count: 2, operator_absent: 0 },
];

const MOCK_ORDERS: ShopFloorOrder[] = [
  { id: '1', mo_id: 'MO-1001', product_name: 'Widget A', work_center: 'Assembly Line 1', start_time: '2026-07-01T08:00', end_time: '2026-07-05T17:00', status: 'in_progress', progress_pct: 60 },
  { id: '2', mo_id: 'MO-1002', product_name: 'Gadget B', work_center: 'Assembly Line 1', start_time: '2026-07-06T08:00', end_time: '2026-07-10T17:00', status: 'queued', progress_pct: 0 },
  { id: '3', mo_id: 'MO-1004', product_name: 'Component C', work_center: 'Machining Center', start_time: '2026-06-28T08:00', end_time: '2026-07-02T17:00', status: 'delayed', progress_pct: 30 },
  { id: '4', mo_id: 'MO-1005', product_name: 'Widget A', work_center: 'Packaging Station', start_time: '2026-07-05T08:00', end_time: '2026-07-06T17:00', status: 'queued', progress_pct: 0 },
  { id: '5', mo_id: 'MO-1006', product_name: 'Gadget B', work_center: 'Machining Center', start_time: '2026-07-03T08:00', end_time: '2026-07-07T17:00', status: 'in_progress', progress_pct: 25 },
];

const MOCK_ALERTS: DelayAlert[] = [
  { id: 'A1', mo_ref: 'MO-1001', cause: 'Material shortage - delay on Assembly Line 1', severity: 'high', timestamp: '2026-07-01T14:30' },
  { id: 'A2', mo_ref: 'MO-1004', cause: 'Supplier delay - component ETA +3d', severity: 'high', timestamp: '2026-06-29T09:15' },
  { id: 'A3', mo_ref: 'MO-1006', cause: 'Operator absent - Machining Center short-staffed', severity: 'medium', timestamp: '2026-07-02T07:45' },
];

function statusColor(status: string): string {
  switch (status) {
    case 'operational': return 'text-green-600 bg-green-50';
    case 'overloaded': return 'text-orange-600 bg-orange-50';
    case 'down': return 'text-red-600 bg-red-50';
    case 'maintenance': return 'text-blue-600 bg-blue-50';
    default: return 'text-ipe-text-muted bg-ipe-surface-alt';
  }
}

function loadBarColor(pct: number): string {
  if (pct > 95) return 'bg-red-600';
  if (pct > 85) return 'bg-orange-500';
  if (pct > 70) return 'bg-yellow-400';
  return 'bg-green-500';
}

function severityBadge(severity: string): 'danger' | 'warning' | 'default' {
  switch (severity) {
    case 'high': return 'danger';
    case 'medium': return 'warning';
    default: return 'default';
  }
}

export function ShopFloorPage() {
  const [selectedWc, setSelectedWc] = useState<string | null>(null);
  const [workCenters] = useState(MOCK_WORK_CENTERS);
  const [orders] = useState(MOCK_ORDERS);
  const [alerts] = useState(MOCK_ALERTS);

  const filteredOrders = selectedWc
    ? orders.filter(o => o.work_center === workCenters.find(w => w.id === selectedWc)?.name)
    : orders;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Shop Floor</h1>
        <p className="text-sm text-ipe-text-muted">Work center monitoring, active orders, and delay alerts</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {workCenters.map(wc => (
          <Card
            key={wc.id}
            className={`cursor-pointer transition-colors ${selectedWc === wc.id ? 'ring-2 ring-ipe-primary' : ''}`}
            onClick={() => setSelectedWc(selectedWc === wc.id ? null : wc.id)}
          >
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-medium truncate">{wc.name}</h3>
              <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${statusColor(wc.status)}`}>{wc.status}</span>
            </div>
            <div className="mb-2 h-3 w-full overflow-hidden rounded-full bg-gray-100">
              <div className={`h-full rounded-full transition-all ${loadBarColor(wc.load_pct)}`} style={{ width: `${Math.min(wc.load_pct, 100)}%` }} />
            </div>
            <div className="flex justify-between text-xs text-ipe-text-muted">
              <span>{wc.load_pct}% load</span>
              <span>{wc.active_orders} orders</span>
            </div>
            <div className="mt-1 text-xs text-ipe-text-muted">
              Operators: {wc.operator_count - wc.operator_absent}/{wc.operator_count}
              {wc.operator_absent > 0 && <span className="ml-1 text-red-500">({wc.operator_absent} absent)</span>}
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <h3 className="mb-3 font-medium">{selectedWc ? `Orders at ${workCenters.find(w => w.id === selectedWc)?.name}` : 'All Active Orders'}</h3>
            <div className="overflow-x-auto">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>MO</TableHeader>
                  <TableHeader>Product</TableHeader>
                  <TableHeader>Status</TableHeader>
                  <TableHeader>Progress</TableHeader>
                </TableRow>
              </TableHead>
              <tbody>
                {filteredOrders.map(o => (
                  <TableRow key={o.id}>
                    <TableCell className="font-medium">{o.mo_id}</TableCell>
                    <TableCell>{o.product_name}</TableCell>
                    <TableCell>
                      <Badge variant={o.status === 'delayed' ? 'danger' : o.status === 'in_progress' ? 'success' : 'warning'}>
                        {o.status.replace(/_/g, ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-full max-w-24 overflow-hidden rounded-full bg-gray-100">
                          <div className={`h-full rounded-full ${o.progress_pct > 80 ? 'bg-green-500' : o.progress_pct > 30 ? 'bg-blue-500' : 'bg-gray-400'}`} style={{ width: `${o.progress_pct}%` }} />
                        </div>
                        <span className="text-xs tabular-nums text-ipe-text-muted">{o.progress_pct}%</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {filteredOrders.length === 0 && (
                  <TableRow><TableCell colSpan={4} className="text-center text-ipe-text-muted">No orders for this work center.</TableCell></TableRow>
                )}
              </tbody>
            </Table>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <h3 className="mb-3 font-medium">Delay Alerts ({alerts.length})</h3>
            <div className="space-y-3">
              {alerts.map(a => (
                <div key={a.id} className="border-b border-ipe-border pb-3 last:border-b-0 last:pb-0">
                  <div className="mb-1 flex items-center gap-2">
                    <Badge variant={severityBadge(a.severity)}>{a.severity}</Badge>
                    <span className="text-xs font-medium text-ipe-text-muted">{a.mo_ref}</span>
                  </div>
                  <p className="text-sm text-ipe-text">{a.cause}</p>
                  <p className="mt-1 text-xs text-ipe-text-muted">{new Date(a.timestamp).toLocaleString()}</p>
                </div>
              ))}
              {alerts.length === 0 && <p className="text-sm text-ipe-text-muted">No active alerts.</p>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
