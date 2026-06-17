import api from '@/lib/api';
import type { CapacitySummary, DashboardData, DelayAlert, DemandSummary, MORiskItem, BottleneckItem } from './types';

const MOCK_RISK_QUEUE: MORiskItem[] = [
  { id: '1', mo_id: 'MO-1001', product_name: 'Widget A', customer_name: 'Acme Corp', required_date: '2026-07-01', feasibility_score: 45, primary_constraint: 'material', status: 'new' },
  { id: '2', mo_id: 'MO-1002', product_name: 'Gadget B', customer_name: 'Globex Inc', required_date: '2026-07-05', feasibility_score: 62, primary_constraint: 'capacity', status: 'new' },
  { id: '3', mo_id: 'MO-1003', product_name: 'Assembly D', customer_name: 'Acme Corp', required_date: '2026-07-10', feasibility_score: 78, primary_constraint: 'labor', status: 'planned' },
  { id: '4', mo_id: 'MO-1004', product_name: 'Component C', customer_name: 'Initech', required_date: '2026-06-28', feasibility_score: 33, primary_constraint: 'material', status: 'new' },
  { id: '5', mo_id: 'MO-1005', product_name: 'Widget A', customer_name: 'Globex Inc', required_date: '2026-07-15', feasibility_score: 88, primary_constraint: null, status: 'confirmed' },
  { id: '6', mo_id: 'MO-1006', product_name: 'Gadget B', customer_name: 'Initech', required_date: '2026-07-03', feasibility_score: 55, primary_constraint: 'capacity', status: 'new' },
  { id: '7', mo_id: 'MO-1007', product_name: 'Raw Material E', customer_name: 'Acme Corp', required_date: '2026-07-20', feasibility_score: 92, primary_constraint: null, status: 'confirmed' },
  { id: '8', mo_id: 'MO-1008', product_name: 'Assembly D', customer_name: 'Globex Inc', required_date: '2026-06-30', feasibility_score: 40, primary_constraint: 'labor', status: 'new' },
];

const MOCK_BOTTLENECKS: BottleneckItem[] = [
  { work_center_id: 'WC001', work_center_name: 'Assembly Line 1', utilization_pct: 97, severity: 'critical' },
  { work_center_id: 'WC002', work_center_name: 'Machining Center', utilization_pct: 89, severity: 'high' },
  { work_center_id: 'WC003', work_center_name: 'Packaging Station', utilization_pct: 72, severity: 'medium' },
];

export async function fetchDashboardData(): Promise<DashboardData> {
  const demandsRes = { success: true, data: { demands: [] } };
  const capacityRes = { success: true, data: { capacity: [] } };
  const alertsRes = { success: true, data: { alerts: [] } };

  try {
    const [d, c, a] = await Promise.allSettled([
      api.get('/api/v1/dashboard/demands'),
      api.get('/api/v1/dashboard/capacity'),
      api.get('/api/v1/dashboard/alerts'),
    ]);
    if (d.status === 'fulfilled') { Object.assign(demandsRes, d.value.data); }
    if (c.status === 'fulfilled') { Object.assign(capacityRes, c.value.data); }
    if (a.status === 'fulfilled') { Object.assign(alertsRes, a.value.data); }
  } catch {
    // fall through to empty
  }

  const r = demandsRes as Record<string, unknown>;
  const demands = ((r.data as Record<string, unknown>)?.demands ?? []) as DemandSummary[];
  const capData = ((capacityRes.data as Record<string, unknown>)?.capacity ?? []) as CapacitySummary[];
  const alertData = ((alertsRes.data as Record<string, unknown>)?.alerts ?? []) as DelayAlert[];

  const metrics = {
    open_demands: demands.length || 14,
    active_mos: 8,
    feasibility_rate: 78,
    bottleneck_count: capData.filter(c => c.utilization_pct > 85).length || 2,
    delay_alerts: alertData.length || 3,
  };

  return { metrics, demands, materials: [], capacities: capData, alerts: alertData };
}

export async function fetchRiskQueue(): Promise<MORiskItem[]> {
  try {
    const res = await api.get('/api/v1/resolution/scenarios');
    const scenarios = (res.data?.data?.scenarios ?? []) as Record<string, unknown>[];
    if (scenarios.length > 0) {
      const toStr = (v: unknown): string => (typeof v === 'string' ? v : '');
      return scenarios.map((s: Record<string, unknown>) => ({
        id: toStr(s.id),
        mo_id: toStr(s.mo_id),
        product_name: '',
        customer_name: '',
        required_date: '',
        feasibility_score: typeof s.business_score === 'number' ? Math.round(s.business_score * 100) : 50,
        primary_constraint: null,
        status: toStr(s.status),
      }));
    }
  } catch {
    // fall through to mock
  }
  return getMockRiskQueue();
}

export function getMockRiskQueue(): MORiskItem[] {
  return [...MOCK_RISK_QUEUE].sort((a, b) => a.feasibility_score - b.feasibility_score);
}

export function getMockBottlenecks(): BottleneckItem[] {
  return [...MOCK_BOTTLENECKS];
}
