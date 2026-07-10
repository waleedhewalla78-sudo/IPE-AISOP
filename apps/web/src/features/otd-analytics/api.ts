import api from '@/lib/api';

export interface OtdKpis {
  otd_pct: number | null;
  completed_mos: number;
  on_time_mos: number;
  orders_at_risk: number;
  avg_delay_days: number | null;
  chaos_cost_usd: number;
  lookback_days: number;
  filters: {
    supplier_id: string | null;
    line_id: string | null;
    region_id: string | null;
  };
}

export interface OtdTrendPoint {
  period_start: string | null;
  otd_pct: number | null;
  completed_mos: number;
  on_time_mos: number;
}

export interface OtdRootCause {
  cause_category: string;
  count: number;
  pct: number;
  cost_usd: number;
}

export interface OtdBaselineComparison {
  baseline: { otd_pct?: number; captured_at?: string } | null;
  current: OtdKpis;
  delta_vs_baseline: number | null;
  improvement_pct: number | null;
}

export interface OtdFilters {
  supplier_id?: string;
  line_id?: string;
  region_id?: string;
}

function filterParams(filters: OtdFilters): Record<string, string> {
  const params: Record<string, string> = {};
  if (filters.supplier_id) params.supplier_id = filters.supplier_id;
  if (filters.line_id) params.line_id = filters.line_id;
  if (filters.region_id) params.region_id = filters.region_id;
  return params;
}

export async function fetchOtdKpis(range = '30d', filters: OtdFilters = {}): Promise<OtdKpis> {
  const res = await api.get('/api/v1/analytics/otd/kpis', { params: { range, ...filterParams(filters) } });
  return res.data?.data;
}

export async function fetchOtdTrend(
  period: 'daily' | 'weekly' | 'monthly' = 'daily',
  range = '30d',
  filters: OtdFilters = {},
): Promise<{ period: string; range: string; points: OtdTrendPoint[] }> {
  const res = await api.get('/api/v1/analytics/otd/trend', {
    params: { period, range, ...filterParams(filters) },
  });
  return res.data?.data ?? { period, range, points: [] };
}

export async function fetchOtdRootCause(range = '30d', filters: OtdFilters = {}): Promise<OtdRootCause[]> {
  const res = await api.get('/api/v1/analytics/otd/root-cause', {
    params: { range, ...filterParams(filters) },
  });
  return res.data?.data ?? [];
}

export async function fetchOtdCostOfChaos(range = '30d'): Promise<{
  total_chaos_usd: number;
  categories: Array<{ code: string; label: string; usd: number; pct: number }>;
}> {
  const res = await api.get('/api/v1/analytics/otd/cost-of-chaos', { params: { range } });
  return res.data?.data ?? { total_chaos_usd: 0, categories: [] };
}

export async function fetchOtdBaseline(): Promise<OtdBaselineComparison> {
  const res = await api.get('/api/v1/analytics/otd/baseline');
  return res.data?.data;
}

export async function fetchFilterOptions(): Promise<{
  suppliers: Array<{ id: string; name: string }>;
  lines: Array<{ id: string; name: string }>;
  regions: Array<{ id: string; name: string }>;
}> {
  try {
    const [suppliersRes, linesRes] = await Promise.all([
      api.get('/api/v1/material/suppliers'),
      api.get('/api/v1/capacity/work-centers'),
    ]);
    const suppliers = (suppliersRes.data?.data?.suppliers ?? suppliersRes.data?.data ?? []).map(
      (s: { id: string; name: string }) => ({ id: s.id, name: s.name }),
    );
    const lines = (linesRes.data?.data ?? []).map((wc: { id: string; name: string; plant_id?: string }) => ({
      id: wc.id,
      name: wc.name,
      plant_id: wc.plant_id,
    }));
    const regionMap = new Map<string, string>();
    lines.forEach((wc: { plant_id?: string }) => {
      if (wc.plant_id) regionMap.set(wc.plant_id, wc.plant_id.slice(0, 8));
    });
    const regions = [...regionMap.entries()].map(([id, label]) => ({ id, name: `Plant ${label}` }));
    return { suppliers, lines, regions };
  } catch {
    return { suppliers: [], lines: [], regions: [] };
  }
}
