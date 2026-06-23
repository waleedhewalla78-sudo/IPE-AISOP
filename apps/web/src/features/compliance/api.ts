import api from '@/lib/api';

export interface ScheduleAdherence {
  total_mos: number;
  completed: number;
  on_time: number;
  adherence_pct: number | null;
}

export interface AIDecisions {
  approvals: number;
  scenario_runs: number;
  cost_optimizations: number;
  copilot_interactions: number;
  total_ai_decisions: number;
}

export interface CostSavings {
  total_schedules_optimized: number;
  avg_total_cost: number;
}

export interface AuditLogEntry {
  timestamp: string;
  actor_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  rationale: string | null;
}

export interface ComplianceKPIs {
  schedule_adherence: ScheduleAdherence;
  ai_decisions: AIDecisions;
  cost_savings: CostSavings;
  recent_audit_log: AuditLogEntry[];
}

export async function fetchComplianceKPIs(): Promise<ComplianceKPIs> {
  try {
    const response = await api.get("/api/v1/feasibility/compliance-kpis");
    return response.data.data;
  } catch {
    return {
      schedule_adherence: {
        total_mos: 0,
        completed: 0,
        on_time: 0,
        adherence_pct: null,
      },
      ai_decisions: {
        approvals: 0,
        scenario_runs: 0,
        cost_optimizations: 0,
        copilot_interactions: 0,
        total_ai_decisions: 0,
      },
      cost_savings: {
        total_schedules_optimized: 0,
        avg_total_cost: 0,
      },
      recent_audit_log: [],
    };
  }
}
