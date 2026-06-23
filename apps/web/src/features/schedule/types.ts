export interface GanttOperation {
  id: string;
  mo_id: string;
  mo_name: string;
  sequence: number;
  work_center_id: string;
  work_center_name: string;
  planned_start: number; // epoch minutes
  planned_end: number;
  duration: number;
  ai_start?: number;
  ai_end?: number;
  status: string;
  is_frozen?: boolean;
  is_disrupted?: boolean;
  priority_score?: number;
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
