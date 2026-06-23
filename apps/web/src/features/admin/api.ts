import api from '@/lib/api';
import type { ConfigData, DataQualityMetrics } from './types';

export async function fetchConfig(): Promise<ConfigData> {
  try {
    const res = await api.get('/api/v1/admin/config');
    const data = res.data?.data;
    return {
      priority_weights: data?.config?.priority_weights ?? {},
      strategic_product_ids: data?.config?.strategic_product_ids ?? [],
      feasibility_thresholds: data?.config?.feasibility_thresholds ?? {},
      autonomy_mode: data?.autonomy_mode ?? 'shadow',
    };
  } catch (err) {
    console.error('Failed to fetch config:', err);
    return { priority_weights: {}, strategic_product_ids: [], feasibility_thresholds: {}, autonomy_mode: 'shadow' };
  }
}

export async function updateConfig(config: Partial<ConfigData>): Promise<ConfigData> {
  try {
    const res = await api.put('/api/v1/admin/config', config);
    const data = res.data?.data;
    return {
      priority_weights: data?.config?.priority_weights ?? config.priority_weights ?? {},
      strategic_product_ids: data?.config?.strategic_product_ids ?? config.strategic_product_ids ?? [],
      feasibility_thresholds: data?.config?.feasibility_thresholds ?? config.feasibility_thresholds ?? {},
      autonomy_mode: data?.autonomy_mode ?? config.autonomy_mode ?? 'shadow',
    };
  } catch (err) {
    console.error('Failed to update config:', err);
    return { priority_weights: config.priority_weights ?? {}, strategic_product_ids: config.strategic_product_ids ?? [], feasibility_thresholds: config.feasibility_thresholds ?? {}, autonomy_mode: config.autonomy_mode ?? 'shadow' };
  }
}

export async function fetchDataQuality(): Promise<DataQualityMetrics> {
  try {
    const res = await api.get('/api/v1/admin/data-quality');
    return res.data?.data as DataQualityMetrics;
  } catch (err) {
    console.error('Failed to fetch data quality:', err);
    return { bom_completeness_pct: 0, lead_time_accuracy_pct: 0, inventory_record_accuracy_pct: 0 };
  }
}

export interface LlmTierStatus {
  tier?: number;
  tenant_tier?: string;
  active_provider: string | null;
  routing_enabled: boolean;
  providers: Record<string, { available: boolean; detail: string; provider?: string }>;
}

export async function fetchLlmStatus(): Promise<LlmTierStatus | null> {
  try {
    const res = await api.get('/api/v1/copilot/llm-status');
    return res.data?.data ?? null;
  } catch (err) {
    console.error('Failed to fetch LLM status:', err);
    return null;
  }
}
