import api from '@/lib/api';

export interface ImpactedMO {
  mo_id: string;
  delay_days: number;
  affected_components: string[];
  revenue_at_risk: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface DisruptionEvent {
  id: string;
  disruption_type: string;
  source_id: string;
  source_name: string;
  delay_days: number;
  impacted_mos: ImpactedMO[];
  impacted_suppliers: { supplier_id: string; tier: number }[];
  total_cost_impact: number;
  created_at: string;
  status: 'active' | 'mitigating' | 'resolved';
}

export interface MitigationScenario {
  id: string;
  name: string;
  description: string;
  cost_impact: number;
  otd_impact_pct: number;
  delay_reduction_days: number;
  confidence: number;
}

export async function fetchDisruptions(): Promise<DisruptionEvent[]> {
  try {
    const res = await api.get('/api/v1/war-room/aggregate', {
      params: { supplier_id: 'SUP-T2-001', delay_days: 21 },
    });
    const d = res.data?.data;
    if (d?.impacted_mos) {
      return [{
        id: 'AGG-001',
        disruption_type: d.disruption_type,
        source_id: d.source_id,
        source_name: 'Silicon Foundry',
        delay_days: d.delay_days,
        impacted_mos: d.impacted_mos.map((m: ImpactedMO & Record<string, unknown>) => ({
          mo_id: String(m.mo_id),
          delay_days: Number(m.delay_days ?? 0),
          affected_components: (m.affected_components as string[]) ?? [],
          revenue_at_risk: Number(m.revenue_at_risk ?? 0),
          severity: Number(m.delay_days ?? 0) > 14 ? 'critical' as const : Number(m.delay_days ?? 0) > 7 ? 'high' as const : 'medium' as const,
        })),
        impacted_suppliers: d.impacted_suppliers ?? [],
        total_cost_impact: d.total_cost_impact ?? 0,
        created_at: new Date().toISOString(),
        status: 'active',
      }];
    }
    return [];
  } catch (err) {
    console.error('Failed to fetch disruptions:', err);
    return [];
  }
}

export async function fetchMitigationScenarios(): Promise<MitigationScenario[]> {
  try {
    const res = await api.get('/api/v1/resolution/scenarios');
    const scenarios = (res.data?.data?.scenarios ?? []) as Record<string, unknown>[];
    return scenarios.map((s: Record<string, unknown>) => ({
      id: String(s.id ?? ''),
      name: String(s.strategy ?? ''),
      description: String((s as any).description ?? ''),
      cost_impact: typeof s.cost_impact === 'number' ? s.cost_impact : 0,
      otd_impact_pct: typeof s.delivery_impact_days === 'number' ? Math.abs(s.delivery_impact_days) * 2 : 0,
      delay_reduction_days: typeof s.delivery_impact_days === 'number' ? Math.abs(s.delivery_impact_days) : 0,
      confidence: typeof s.business_score === 'number' ? s.business_score : 0.5,
    }));
  } catch (err) {
    console.error('Failed to fetch mitigation scenarios:', err);
    return [];
  }
}
