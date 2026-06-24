export interface GanttOperation {
  id: string;
  mo_id: string;
  mo_name: string;
  sequence: number;
  work_center_id: string;
  work_center_name: string;
  planned_start: number; // minutes from horizon start
  planned_end: number;
  duration: number;
  ai_start?: number;
  ai_end?: number;
  status: string;
  is_frozen?: boolean;
  is_disrupted?: boolean;
  priority_score?: number;
  is_critical?: boolean;
  slack_minutes?: number;
}

export interface CpmConflict {
  operation_id: string;
  reason: string;
}

export interface CpmFinancialDelta {
  overtime_usd: number;
  tardiness_penalty_usd: number;
  activity_cost_delta_usd: number;
}

export interface CpmCascadeOperation {
  operation_id: string;
  planned_start: string;
  planned_end: string;
  is_critical: boolean;
  slack_minutes: number;
}

export interface CpmCascadeResult {
  operations: CpmCascadeOperation[];
  critical_path_ids: string[];
  financial_delta: CpmFinancialDelta;
  conflicts: CpmConflict[];
  cascade_ms: number;
  cascade_token?: string;
}

export interface GanttRow {
  mo_id: string;
  mo_name: string;
  operations: GanttOperation[];
  feasibility_score?: number;
  primary_constraint?: string;
  disruption_status?: string;
  ai_suggested_start?: number;
  ai_suggested_end?: number;
  approved?: boolean;
}
