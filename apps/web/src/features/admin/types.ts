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
