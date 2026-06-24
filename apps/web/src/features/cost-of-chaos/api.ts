import api from '@/lib/api';

export interface ChaosCategory {
  code: string;
  label: string;
  usd: number;
  pct: number;
}

export interface ChaosTopMo {
  mo_id: string;
  chaos_usd: number;
  primary_category: string;
}

export interface ChaosWarRoomLink {
  disruption_id: string;
  chaos_usd: number;
}

export interface CostOfChaosData {
  period: string;
  total_chaos_usd: number;
  categories: ChaosCategory[];
  top_mos: ChaosTopMo[];
  war_room_links: ChaosWarRoomLink[];
}

export async function fetchCostOfChaos(period: '7d' | '30d' = '7d'): Promise<CostOfChaosData> {
  const res = await api.get('/api/v1/analytics/cost-of-chaos', { params: { period } });
  if (res.data?.success === false) {
    throw new Error(res.data?.error?.message ?? 'Failed to load cost of chaos');
  }
  return res.data?.data as CostOfChaosData;
}
