import api from '@/lib/api';

export interface MdrDashboardData {
  composite_score: number;
  composite_threshold?: number;
  gate_threshold?: number;
  ai_scheduling_allowed?: boolean;
  gate_passed?: boolean;
  passed?: boolean;
  bom_completeness_pct?: number;
  lead_time_accuracy_pct?: number;
  routing_accuracy_pct?: number;
  inventory_accuracy_pct?: number;
  dimensions?: Record<string, { score: number; weight: number; detail?: string }>;
  remediation?: string[];
  recommendations?: string[];
}

export async function fetchMdrDashboard(): Promise<MdrDashboardData | null> {
  try {
    const res = await api.get('/api/v1/demand/mdr/dashboard');
    return res.data?.data ?? null;
  } catch (err) {
    console.error('Failed to fetch MDR dashboard:', err);
    return null;
  }
}
