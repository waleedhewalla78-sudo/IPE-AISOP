import api from '@/lib/api';

export interface SpcXbarRequest {
  measurements: number[][];
  sigma_multiplier: number;
  usl: number;
  lsl: number;
}

export interface SpcXbarResponse {
  x_bar_values: number[];
  ucl: number;
  lcl: number;
  cl: number;
  out_of_control_points: number[];
  sigma: number;
}

export interface PChartRequest {
  defect_counts: number[];
  sample_sizes: number[];
  sigma_multiplier: number;
}

export interface PChartResponse {
  defect_rates: number[];
  ucl: number;
  lcl: number;
  cl: number;
  out_of_control_points: number[];
}

export interface DefectPredictionRequest {
  mo_id: string;
  operation_type: string;
  work_center_id: string;
  shift: string;
  operator_id: string;
  days_since_maintenance: number;
}

export interface DefectPredictionResponse {
  mo_id: string;
  defect_probability: number;
  risk_level: string;
  contributing_factors: { factor: string; weight: number; description: string }[];
  recommended_actions: string[];
}

export async function fetchSpcXbar(
  measurements: number[][],
  sigmaMultiplier: number,
  usl: number,
  lsl: number,
): Promise<SpcXbarResponse> {
  try {
    const res = await api.post('/api/v1/quality/spc/xbar', {
      measurements,
      sigma_multiplier: sigmaMultiplier,
      usl,
      lsl,
    });
    return res.data.data ?? res.data;
  } catch (err) {
    console.error('Failed to fetch SPC X-bar chart:', err);
    throw err;
  }
}

export async function fetchPChart(
  defectCounts: number[],
  sampleSizes: number[],
  sigmaMultiplier: number,
): Promise<PChartResponse> {
  try {
    const res = await api.post('/api/v1/quality/spc/pchart', {
      defect_counts: defectCounts,
      sample_sizes: sampleSizes,
      sigma_multiplier: sigmaMultiplier,
    });
    return res.data.data ?? res.data;
  } catch (err) {
    console.error('Failed to fetch P-chart:', err);
    throw err;
  }
}

export async function fetchDefectPrediction(
  moId: string,
  operationType: string,
  workCenterId: string,
  shift: string,
  operatorId: string,
  daysSinceMaintenance: number,
): Promise<DefectPredictionResponse> {
  try {
    const res = await api.post('/api/v1/quality/predict', {
      mo_id: moId,
      operation_type: operationType,
      work_center_id: workCenterId,
      shift,
      operator_id: operatorId,
      days_since_maintenance: daysSinceMaintenance,
    });
    return res.data.data ?? res.data;
  } catch (err) {
    console.error('Failed to fetch defect prediction:', err);
    throw err;
  }
}
