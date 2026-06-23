export interface ControlTowerMetrics {
  open_demands: number;
  active_mos: number;
  feasibility_rate: number;
  bottleneck_count: number;
  delay_alerts: number;
}

export interface DemandSummary {
  id: string;
  product_name: string;
  quantity: number;
  required_date: string;
  demand_type: string;
  priority_score: number | null;
  status: string;
}

export interface MaterialStatus {
  product_name: string;
  internal_ref: string | null;
  qty_on_hand: number;
  qty_reserved: number;
  net_available: number;
  incoming_supply: number;
  shortage: number;
}

export interface CapacitySummary {
  work_center: string;
  total_hours: number;
  utilized_hours: number;
  utilization_pct: number;
  status: string;
}

export interface DelayAlert {
  id: string;
  mo_ref: string;
  cause: string;
  delay_minutes: number;
  created_at: string;
  severity: 'low' | 'medium' | 'high';
}

export interface DashboardData {
  metrics: ControlTowerMetrics;
  demands: DemandSummary[];
  materials: MaterialStatus[];
  capacities: CapacitySummary[];
  alerts: DelayAlert[];
}

export interface MORiskItem {
  id: string;
  mo_id: string;
  product_name: string;
  customer_name: string;
  required_date: string;
  feasibility_score: number;
  primary_constraint: string | null;
  status: string;
}

export interface BottleneckItem {
  work_center_id: string;
  work_center_name: string;
  utilization_pct: number;
  severity: string;
}

export interface MOQueueItem {
  mo_id: string;
  product_name: string;
  customer_name: string;
  required_date: string;
  feasibility_score: number | null;
  primary_constraint: string | null;
}

export interface KPI {
  avg_feasibility_score: number | null;
  active_bottlenecks: number | null;
  orders_at_risk: number | null;
  otd_pct: number | null;
}
