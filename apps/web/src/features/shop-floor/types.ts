export interface WorkCenterStatus {
  id: string;
  name: string;
  status: 'operational' | 'overloaded' | 'down' | 'maintenance';
  load_pct: number;
  active_orders: number;
  operator_count: number;
  operator_absent: number;
}

export interface ShopFloorOrder {
  id: string;
  mo_id: string;
  product_name: string;
  work_center: string;
  start_time: string | null;
  end_time: string | null;
  status: string;
  progress_pct: number;
}

export interface DelayAlert {
  id: string;
  mo_ref: string;
  cause: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
}
