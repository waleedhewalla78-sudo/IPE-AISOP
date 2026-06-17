import api from '@/lib/api';
import type { ConfigData, DataQualityMetrics } from './types';

const MOCK_CONFIG: ConfigData = {
  priority_weights: { urgency: 0.30, customer_tier: 0.20, penalty: 0.20, margin: 0.15, strategic_product: 0.10, quantity: 0.05 },
  strategic_product_ids: [],
  feasibility_thresholds: { auto_confirm: 90, planner: 70 },
  autonomy_mode: 'shadow',
};

const MOCK_DATA_QUALITY: DataQualityMetrics = {
  bom_completeness_pct: 87.5,
  lead_time_accuracy_pct: 72.3,
  inventory_record_accuracy_pct: 94.1,
};

export async function fetchConfig(): Promise<ConfigData> {
  try {
    const res = await api.get('/api/v1/admin/config');
    return res.data?.data as ConfigData;
  } catch {
    return MOCK_CONFIG;
  }
}

export async function updateConfig(config: Partial<ConfigData>): Promise<ConfigData> {
  try {
    const res = await api.put('/api/v1/admin/config', config);
    return res.data?.data as ConfigData;
  } catch {
    return { ...MOCK_CONFIG, ...config };
  }
}

export async function fetchDataQuality(): Promise<DataQualityMetrics> {
  try {
    const res = await api.get('/api/v1/admin/data-quality');
    return res.data?.data as DataQualityMetrics;
  } catch {
    return MOCK_DATA_QUALITY;
  }
}
