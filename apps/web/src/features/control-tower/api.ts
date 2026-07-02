import api from '@/lib/api';
import type { CapacitySummary, DashboardData, DelayAlert, DemandSummary, MORiskItem, BottleneckItem, MOQueueItem, KPI } from './types';

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
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err);
  }

  const r = demandsRes as Record<string, unknown>;
  const demands = ((r.data as Record<string, unknown>)?.demands ?? []) as DemandSummary[];
  const capData = ((capacityRes.data as Record<string, unknown>)?.capacity ?? []) as CapacitySummary[];
  const alertData = ((alertsRes.data as Record<string, unknown>)?.alerts ?? []) as DelayAlert[];

  const metrics = {
    open_demands: demands.length,
    active_mos: 0,
    feasibility_rate: 0,
    bottleneck_count: capData.filter(c => c.utilization_pct > 85).length,
    delay_alerts: alertData.length,
  };

  return { metrics, demands, materials: [], capacities: capData, alerts: alertData };
}

export async function fetchRiskQueue(): Promise<MORiskItem[]> {
  try {
    const res = await api.get('/api/v1/feasibility/queue');
    const queue = (res.data?.data ?? []) as Record<string, unknown>[];
    if (queue.length > 0) {
      const toStr = (v: unknown): string => (typeof v === 'string' ? v : '');
      return queue.map((item: Record<string, unknown>, i: number) => ({
        id: toStr(item.mo_id) || String(i),
        mo_id: toStr(item.mo_id),
        product_name: toStr(item.product_name),
        customer_name: toStr(item.customer_name),
        required_date: toStr(item.required_date),
        feasibility_score: typeof item.feasibility_score === 'number' ? item.feasibility_score : 0,
        primary_constraint: (item.primary_constraint as string) ?? null,
        status: 'new',
      }));
    }
  } catch (err) {
    console.error('Failed to fetch risk queue:', err);
  }
  return [];
}

export async function getMockBottlenecks(): Promise<BottleneckItem[]> {
  try {
    const res = await api.post('/api/v1/capacity/analyze');
    const data = res.data?.data;
    if (data?.work_centers) {
      return data.work_centers
        .filter((wc: any) => (wc.oee ?? 0.85) > 0.85)
        .map((wc: any) => ({
          work_center_id: String(wc.id),
          work_center_name: String(wc.name),
          utilization_pct: Math.round((wc.oee ?? 0.85) * 100),
          severity: (wc.oee ?? 0.85) > 0.95 ? 'critical' : (wc.oee ?? 0.85) > 0.90 ? 'high' : 'medium',
        }));
    }
  } catch (err) {
    console.error('Failed to fetch bottlenecks:', err);
  }
  return [];
}

export async function fetchQueue(): Promise<MOQueueItem[]> {
  try {
    const res = await api.get('/api/v1/feasibility/queue');
    return res.data?.data ?? [];
  } catch (err) {
    console.error('Failed to fetch feasibility queue:', err);
    return [];
  }
}

export async function fetchKPIs(): Promise<KPI | null> {
  try {
    const res = await api.get('/api/v1/feasibility/kpis');
    return res.data?.data ?? null;
  } catch (err) {
    console.error('Failed to fetch KPIs:', err);
    return null;
  }
}

export async function queryPlannerAssist(query: string): Promise<{
  intent: string;
  answer_markdown: string;
  citations: Record<string, unknown>[];
  source?: string;
}> {
  const res = await api.post('/api/v1/planner-assist/query', { query });
  if (!res.data?.success) {
    throw new Error(res.data?.error?.message ?? 'Planner assist failed');
  }
  return res.data.data;
}
