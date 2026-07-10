export interface FieldMappingItem {
  ipe_field: string;
  odoo_model: string;
  odoo_field: string;
  transform?: string | null;
}

export interface OdooConfigEntity {
  entity_key: string;
  version: number;
  is_current: boolean;
  name: string;
  odoo_url: string;
  odoo_db: string;
  odoo_username: string;
  enabled: boolean;
  sync_interval_minutes: number;
  password_set: boolean;
  field_mappings: Record<string, FieldMappingItem[]>;
  change_summary?: string | null;
  created_at?: string | null;
}

export interface OdooConfigListData {
  entities: OdooConfigEntity[];
  schema_version: number;
}

export interface OdooConnectionTestResult {
  connected: boolean;
  uid?: number;
  server_version?: string;
  latency_ms?: number;
  entity_key?: string;
}
