import api from '@/lib/api';

export interface BOMComponent {
  component_id: string;
  material_type: string;
  weight_kg: number;
  recyclable: boolean;
}

export interface CircularityScoreResponse {
  product_id: string;
  circularity_score: number;
  material_recovery_pct: number;
  disassembly_cost: number;
  take_back_eligible: boolean;
  breakdown: { material: string; recovery_pct: number }[];
}

export interface EolPlanResponse {
  product_id: string;
  region: string;
  predicted_eol_date: string;
  phase_out_schedule: { phase: string; date: string; description: string }[];
  regulatory_notices: { regulation: string; deadline: string; status: string }[];
}

export interface RecyclabilityScoreResponse {
  product_id: string;
  recyclability_score: number;
  grade: string;
  breakdown: { component: string; material: string; recyclability_pct: number }[];
  recommendations: string[];
}

export async function fetchCircularityScore(
  productId: string,
  bomComponents: BOMComponent[],
): Promise<CircularityScoreResponse> {
  try {
    const res = await api.post('/api/v1/sustainability/circularity-score', {
      product_id: productId,
      bom_components: bomComponents,
    });
    return res.data.data ?? res.data;
  } catch (err) {
    console.error('Failed to fetch circularity score:', err);
    throw err;
  }
}

export async function fetchEolPlan(
  productId: string,
  region: string,
): Promise<EolPlanResponse> {
  try {
    const res = await api.get('/api/v1/sustainability/eol-plan', {
      params: { product_id: productId, regulatory_region: region },
    });
    return res.data.data ?? res.data;
  } catch (err) {
    console.error('Failed to fetch EOL plan:', err);
    throw err;
  }
}

export async function fetchRecyclabilityScore(
  productId: string,
  bomComponents: BOMComponent[],
): Promise<RecyclabilityScoreResponse> {
  try {
    const res = await api.post('/api/v1/sustainability/recyclability-score', {
      product_id: productId,
      bom_components: bomComponents,
    });
    return res.data.data ?? res.data;
  } catch (err) {
    console.error('Failed to fetch recyclability score:', err);
    throw err;
  }
}
