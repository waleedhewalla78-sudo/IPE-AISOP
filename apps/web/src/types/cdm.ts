export interface Tenant {
  id: string;
  name: string;
  tier: 'starter' | 'professional' | 'enterprise';
  erp_type: string;
  autonomy_mode: 'shadow' | 'suggest' | 'autonomous';
  is_active: boolean;
}

export interface Product {
  id: string;
  tenant_id: string;
  erp_source_id: string;
  name: string;
  internal_ref: string | null;
  source_type: 'manufactured' | 'purchased' | 'subcontracted';
  uom: string;
  standard_cost: number | null;
  lead_time_days: number | null;
  safety_stock: number;
  created_at: string;
}

export interface DemandLine {
  id: string;
  tenant_id: string;
  product_id: string;
  quantity: number;
  required_date: string;
  demand_type: 'MTO' | 'MTS' | 'CTO' | 'ETO';
  priority_score: number | null;
  status: string;
  created_at: string;
}

export interface ManufacturingOrder {
  id: string;
  product_id: string;
  quantity: number;
  planned_start: string | null;
  planned_end: string | null;
  feasibility_score: number | null;
  status: string;
  created_at: string;
}

export interface MOConstraint {
  type: 'material' | 'capacity' | 'labor' | 'bom' | 'demand';
  severity: 'critical' | 'high' | 'medium' | 'low';
  detail: string;
  value: number | null;
}

export interface MOWithConstraints extends ManufacturingOrder {
  constraints: MOConstraint[];
  delay_cause: string | null;
  delay_confidence: number | null;
}

export interface ResolutionScenario {
  id: string;
  mo_id: string;
  strategy: string;
  delivery_impact_days: number | null;
  cost_impact: number | null;
  business_score: number | null;
  status: 'proposed' | 'approved' | 'rejected' | 'expired';
  details: string;
}
