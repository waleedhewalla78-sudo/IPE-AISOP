export interface TenantConfig {
  id: string;
  name: string;
  tier: string;
  autonomy_mode: string;
  erp_type: string;
}

export interface OdooConfig {
  erp_type?: string;
  odoo_url: string;
  odoo_db: string;
  odoo_username: string;
  odoo_password?: string;
  enabled: boolean;
  password_set?: boolean;
  sync_interval_minutes?: number;
}

export interface DataQualityFlag {
  mo_id: string;
  erp_mo_id?: string | null;
  flag_code: string;
  message: string;
  created_at?: string | null;
}

export interface SyncRun {
  id: string;
  source?: string;
  trigger?: string;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds?: number | null;
  status: string;
  entity_counts?: Record<string, unknown>;
  error_summary?: string | null;
}

export interface ConfigData {
  priority_weights: Record<string, number>;
  strategic_product_ids: string[];
  feasibility_thresholds: Record<string, number>;
  autonomy_mode: string;
}

export interface DataQualityMetrics {
  bom_completeness_pct: number;
  lead_time_accuracy_pct: number;
  inventory_record_accuracy_pct: number;
}
