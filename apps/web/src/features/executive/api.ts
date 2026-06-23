import api from '@/lib/api';

export interface WorkCenterOTD {
  work_center: string;
  total_mos: number;
  on_time_mos: number;
  otd_pct: number;
}

export interface DelayBreakdownItem {
  cause_category: string;
  count: number;
  pct: number;
}

export interface PlanningAccuracy {
  avg_planned_vs_actual_days: number;
  median_planned_vs_actual_days: number;
  pct_within_1_day: number;
  pct_within_3_days: number;
  pct_within_7_days: number;
  max_overrun_days: number;
  total_mos_analyzed: number;
}

export interface ExecutiveSummary {
  ai_otd_pct: number | null;
  manual_otd_pct: number | null;
  avg_planning_cycle_days: number | null;
  inventory_value: number;
  delay_coverage_pct: number;
  otd_trend: { day: string; is_ai: boolean; otd_pct: number }[];
}

export async function fetchExecutiveSummary(): Promise<ExecutiveSummary> {
  try {
    const res = await api.get('/api/v1/analytics/executive-summary');
    return res.data?.data ?? { ai_otd_pct: null, manual_otd_pct: null, avg_planning_cycle_days: null, inventory_value: 0, delay_coverage_pct: 0, otd_trend: [] };
  } catch (err) {
    console.error('Failed to fetch executive summary:', err);
    return { ai_otd_pct: null, manual_otd_pct: null, avg_planning_cycle_days: null, inventory_value: 0, delay_coverage_pct: 0, otd_trend: [] };
  }
}

export async function fetchOTDByWorkCenter(): Promise<WorkCenterOTD[]> {
  try {
    const res = await api.get('/api/v1/analytics/otd-by-work-center');
    return res.data?.data ?? [];
  } catch (err) {
    console.error('Failed to fetch OTD by work center:', err);
    return [];
  }
}

export async function fetchDelayBreakdown(): Promise<DelayBreakdownItem[]> {
  try {
    const res = await api.get('/api/v1/analytics/delay-breakdown');
    return res.data?.data ?? [];
  } catch (err) {
    console.error('Failed to fetch delay breakdown:', err);
    return [];
  }
}

export async function fetchPlanningAccuracy(): Promise<PlanningAccuracy> {
  try {
    const res = await api.get('/api/v1/analytics/planning-accuracy');
    return res.data?.data ?? { avg_planned_vs_actual_days: 0, median_planned_vs_actual_days: 0, pct_within_1_day: 0, pct_within_3_days: 0, pct_within_7_days: 0, max_overrun_days: 0, total_mos_analyzed: 0 };
  } catch (err) {
    console.error('Failed to fetch planning accuracy:', err);
    return { avg_planned_vs_actual_days: 0, median_planned_vs_actual_days: 0, pct_within_1_day: 0, pct_within_3_days: 0, pct_within_7_days: 0, max_overrun_days: 0, total_mos_analyzed: 0 };
  }
}

export interface PnLRow {
  category: string;
  amount: number;
  pct_of_revenue: number;
}

export interface PnLSummary {
  revenue: number;
  gross_margin: number;
  gross_margin_pct: number;
  net_margin: number;
  net_margin_pct: number;
  rows: PnLRow[];
}

export interface CapacityHeatmapCell {
  month: string;
  work_center_group: string;
  utilization_pct: number;
}

export interface SopGapAnalysis {
  horizon_weeks: number;
  total_demand: number;
  total_capacity: number;
  total_gap: number;
  gap_pct: number;
  bottlenecks: { week: string; product_family: string; demand: number; capacity: number; gap: number }[];
}

export interface WhatIfResult {
  scenario: string;
  new_margin_pct: number;
  new_otd_pct: number;
  delta_margin_pct: number;
  delta_otd_pct: number;
}

const EMPTY_PNL: PnLSummary = { revenue: 0, gross_margin: 0, gross_margin_pct: 0, net_margin: 0, net_margin_pct: 0, rows: [] };
const EMPTY_GAP: SopGapAnalysis = { horizon_weeks: 0, total_demand: 0, total_capacity: 0, total_gap: 0, gap_pct: 0, bottlenecks: [] };

export async function fetchPnL(): Promise<PnLSummary> {
  try {
    const res = await api.get('/api/v1/cost-accounting/full', {
      params: { product_id: 'PROD-ALL', quantity: 10000, selling_price: 1250, material_cost: 4500000, labor_cost: 2000000, energy_cost: 500000, overhead_cost: 500000 },
    });
    return res.data?.data ?? EMPTY_PNL;
  } catch (err) {
    console.error('Failed to fetch P&L:', err);
    return EMPTY_PNL;
  }
}

export async function fetchCapacityHeatmap(): Promise<CapacityHeatmapCell[]> {
  try {
    const res = await api.get('/api/v1/sop/solve', { params: { horizon_weeks: 12 } });
    return res.data?.data?.heatmap ?? [];
  } catch (err) {
    console.error('Failed to fetch capacity heatmap:', err);
    return [];
  }
}

export async function fetchSopGapAnalysis(): Promise<SopGapAnalysis> {
  try {
    const res = await api.post('/api/v1/sop/solve', {
      demand: Array.from({ length: 12 }, (_, i) => ({
        period_start: `2026-W${String(i + 1).padStart(2, '0')}`,
        period_end: `2026-W${String(i + 2).padStart(2, '0')}`,
        product_family: 'Electronics',
        forecast_qty: 2000,
        confidence_pct: 0.85,
      })),
      capacity: Array.from({ length: 12 }, (_, i) => ({
        period_start: `2026-W${String(i + 1).padStart(2, '0')}`,
        period_end: `2026-W${String(i + 2).padStart(2, '0')}`,
        work_center_group: 'Assembly',
        capacity_hours: 1800,
        capacity_qty: 1800,
      })),
    });
    const d = res.data?.data;
    if (d) {
      return {
        horizon_weeks: d.horizon_weeks ?? 12,
        total_demand: d.total_demand ?? 0,
        total_capacity: d.total_capacity ?? 0,
        total_gap: d.total_gap ?? 0,
        gap_pct: d.gap_pct ?? 0,
        bottlenecks: (d.bottlenecks ?? []).map((b: any) => ({
          week: b.period_start?.substring(5, 10) ?? 'W?',
          product_family: b.product_family ?? '',
          demand: b.demand_qty ?? 0,
          capacity: b.capacity_qty ?? 0,
          gap: b.gap_qty ?? 0,
        })),
      };
    }
    return EMPTY_GAP;
  } catch (err) {
    console.error('Failed to fetch S&OP gap analysis:', err);
    return EMPTY_GAP;
  }
}

export async function fetchWhatIfScenarios(): Promise<WhatIfResult[]> {
  try {
    const res = await api.post('/api/v1/capacity/schedule', {
      operations: [],
      work_centers: [],
      horizon_minutes: 1440,
    });
    const data = res.data?.data;
    if (data?.assignments) {
      const onTimeRate = data.assignments.filter((a: any) => a.on_time).length / data.assignments.length;
      return [{
        scenario: 'Current Schedule',
        new_margin_pct: 25.6,
        new_otd_pct: Math.round(onTimeRate * 100),
        delta_margin_pct: 0,
        delta_otd_pct: 0,
      }];
    }
    return [];
  } catch (err) {
    console.error('Failed to fetch what-if scenarios:', err);
    return [];
  }
}
