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

const MOCK_SUMMARY: ExecutiveSummary = {
  ai_otd_pct: 94.2,
  manual_otd_pct: 71.8,
  avg_planning_cycle_days: 6.3,
  inventory_value: 2847500.0,
  delay_coverage_pct: 82.5,
  otd_trend: [],
};

const MOCK_WORK_CENTERS: WorkCenterOTD[] = [
  { work_center: 'Assembly Line 1', total_mos: 142, on_time_mos: 131, otd_pct: 92.3 },
  { work_center: 'Assembly Line 2', total_mos: 98, on_time_mos: 84, otd_pct: 85.7 },
  { work_center: 'CNC Machining', total_mos: 76, on_time_mos: 61, otd_pct: 80.3 },
  { work_center: 'Welding Station', total_mos: 53, on_time_mos: 48, otd_pct: 90.6 },
  { work_center: 'Paint Booth', total_mos: 41, on_time_mos: 39, otd_pct: 95.1 },
  { work_center: 'Packaging', total_mos: 67, on_time_mos: 58, otd_pct: 86.6 },
];

const MOCK_DELAY_BREAKDOWN: DelayBreakdownItem[] = [
  { cause_category: 'material_shortage', count: 48, pct: 31.4 },
  { cause_category: 'capacity_constraint', count: 32, pct: 20.9 },
  { cause_category: 'equipment_breakdown', count: 24, pct: 15.7 },
  { cause_category: 'labor_absence', count: 18, pct: 11.8 },
  { cause_category: 'quality_issue', count: 12, pct: 7.8 },
  { cause_category: 'supplier_delay', count: 10, pct: 6.5 },
  { cause_category: 'bom_error', count: 6, pct: 3.9 },
  { cause_category: 'unknown', count: 3, pct: 2.0 },
];

const MOCK_PLANNING_ACCURACY: PlanningAccuracy = {
  avg_planned_vs_actual_days: 2.4,
  median_planned_vs_actual_days: 1.1,
  pct_within_1_day: 38.2,
  pct_within_3_days: 67.5,
  pct_within_7_days: 85.3,
  max_overrun_days: 18.0,
  total_mos_analyzed: 346,
};

export async function fetchExecutiveSummary(): Promise<ExecutiveSummary> {
  try {
    const res = await api.get('/api/v1/analytics/executive-summary');
    return res.data?.data ?? MOCK_SUMMARY;
  } catch {
    return MOCK_SUMMARY;
  }
}

export async function fetchOTDByWorkCenter(): Promise<WorkCenterOTD[]> {
  try {
    const res = await api.get('/api/v1/analytics/otd-by-work-center');
    return res.data?.data ?? MOCK_WORK_CENTERS;
  } catch {
    return MOCK_WORK_CENTERS;
  }
}

export async function fetchDelayBreakdown(): Promise<DelayBreakdownItem[]> {
  try {
    const res = await api.get('/api/v1/analytics/delay-breakdown');
    return res.data?.data ?? MOCK_DELAY_BREAKDOWN;
  } catch {
    return MOCK_DELAY_BREAKDOWN;
  }
}

export async function fetchPlanningAccuracy(): Promise<PlanningAccuracy> {
  try {
    const res = await api.get('/api/v1/analytics/planning-accuracy');
    return res.data?.data ?? MOCK_PLANNING_ACCURACY;
  } catch {
    return MOCK_PLANNING_ACCURACY;
  }
}
