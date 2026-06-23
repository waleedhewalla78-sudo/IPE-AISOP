import api from '@/lib/api';
import type { WorkCenterStatus, ShopFloorOrder, DelayAlert } from './types';

export async function fetchWorkCenters(): Promise<WorkCenterStatus[]> {
  try {
    const res = await api.get('/api/v1/capacity/analyze');
    const data = res.data?.data;
    if (!data?.work_centers) return [];
    return data.work_centers.map((wc: Record<string, unknown>) => ({
      id: wc.id as string,
      name: wc.name as string,
      status: (wc.status as WorkCenterStatus['status']) || 'operational',
      load_pct: (wc.utilization_pct as number) || 0,
      active_orders: (wc.active_orders as number) || 0,
      operator_count: (wc.operator_count as number) || 0,
      operator_absent: (wc.operator_absent as number) || 0,
    }));
  } catch {
    return [];
  }
}

export async function fetchShopFloorOrders(): Promise<ShopFloorOrder[]> {
  try {
    const res = await api.post('/api/v1/capacity/schedule', { operations: [] });
    const assignments = res.data?.data?.schedule?.assignments || [];
    return assignments.map((a: Record<string, unknown>, idx: number) => ({
      id: String(idx),
      mo_id: (a.mo_id as string) || '',
      product_name: (a.operation_name as string) || '',
      work_center: (a.work_center_id as string) || '',
      start_time: a.start_minute != null ? new Date(Date.now() + (a.start_minute as number) * 60000).toISOString() : null,
      end_time: a.end_minute != null ? new Date(Date.now() + (a.end_minute as number) * 60000).toISOString() : null,
      status: (a.on_time as boolean) ? 'in_progress' : 'delayed',
      progress_pct: 0,
    }));
  } catch {
    return [];
  }
}

export async function fetchDelayAlerts(): Promise<DelayAlert[]> {
  try {
    const res = await api.get('/api/v1/alerts');
    const alerts = res.data?.data?.alerts || [];
    return alerts.map((a: Record<string, unknown>) => ({
      id: (a.id as string) || '',
      mo_ref: (a.entity_id as string) || '',
      cause: (a.description as string) || '',
      severity: (a.severity as DelayAlert['severity']) || 'low',
      timestamp: (a.created_at as string) || new Date().toISOString(),
    }));
  } catch {
    return [];
  }
}
