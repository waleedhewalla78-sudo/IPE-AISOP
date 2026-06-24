import api from '@/lib/api';

export interface TariffShockRequest {
  region: string;
  tariff_delta_pct: number;
  margin_threshold_pct?: number;
}

export interface MoMarginImpact {
  mo_id: string;
  net_margin_before: number;
  net_margin_after: number;
  erosion_usd: number;
}

export interface SubstituteDraft {
  mo_id: string;
  from_material_id: string;
  to_material_id: string;
  status: string;
}

export interface TariffShockResult {
  affected_mo_count: number;
  mos_below_threshold: MoMarginImpact[];
  substitute_drafts: SubstituteDraft[];
}

export async function runTariffShock(params: TariffShockRequest): Promise<TariffShockResult> {
  const res = await api.post('/api/v1/demand/tariff/shock', {
    region: params.region,
    tariff_delta_pct: params.tariff_delta_pct,
    margin_threshold_pct: params.margin_threshold_pct ?? 15,
  });
  if (res.data?.success === false) {
    throw new Error(res.data?.error?.message ?? 'Tariff shock simulation failed');
  }
  return res.data?.data as TariffShockResult;
}
