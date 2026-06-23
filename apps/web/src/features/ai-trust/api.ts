import api from '@/lib/api';

export interface TrustScore {
  category: string;
  score: number;
  trend: 'up' | 'down' | 'stable';
  delta: number;
}

export interface ModelAccuracy {
  model_name: string;
  prediction_count: number;
  accuracy_pct: number;
  avg_confidence: number;
  mape: number;
}

export interface AdoptionMetric {
  month: string;
  total_decisions: number;
  ai_accepted: number;
  ai_overridden: number;
  manual_only: number;
  adoption_pct: number;
}

export interface ImpactMetric {
  metric: string;
  ai_value: number;
  manual_value: number;
  delta: number;
  delta_pct: number;
}

export interface OverrideEvent {
  id: string;
  timestamp: string;
  model: string;
  recommendation: string;
  override_reason: string;
  planner: string;
  impact: string;
}

export async function fetchTrustScores(): Promise<TrustScore[]> {
  try {
    const res = await api.get('/api/v1/ai-trust/scores');
    return res.data?.data ?? [];
  } catch (err) {
    console.error('Failed to fetch trust scores:', err);
    return [];
  }
}

export async function fetchModelAccuracy(): Promise<ModelAccuracy[]> {
  try {
    const res = await api.get('/api/v1/ai-trust/model-accuracy');
    return res.data?.data ?? [];
  } catch (err) {
    console.error('Failed to fetch model accuracy:', err);
    return [];
  }
}

export async function fetchAdoptionMetrics(): Promise<AdoptionMetric[]> {
  try {
    const res = await api.get('/api/v1/ai-trust/adoption');
    return res.data?.data ?? [];
  } catch (err) {
    console.error('Failed to fetch adoption metrics:', err);
    return [];
  }
}

export async function fetchImpactMetrics(): Promise<ImpactMetric[]> {
  try {
    const res = await api.get('/api/v1/ai-trust/impact');
    return res.data?.data ?? [];
  } catch (err) {
    console.error('Failed to fetch impact metrics:', err);
    return [];
  }
}
