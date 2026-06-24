export const APP_NAME = 'IPE - Intelligent Planning Engine';
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ROUTES = {
  LOGIN: '/login',
  CONTROL_TOWER: '/control-tower',
  SCHEDULE: '/schedule',
  RESOLUTION_CENTER: '/resolution-center',
  COPILOT: '/copilot',
  EXECUTIVE: '/executive',
  WAR_ROOM: '/war-room',
  AI_TRUST: '/ai-trust',
  SHOP_FLOOR: '/shop-floor',
  SCN_PORTAL: '/scn-portal',
  ML_OPS: '/ml-ops',
  ONBOARDING: '/onboarding',
  ADMIN: '/admin',
  TARIFF: '/tariff',
  COST_OF_CHAOS: '/cost-of-chaos',
} as const;

export const DEMAND_TYPES = ['MTO', 'MTS', 'CTO', 'ETO'] as const;
export const MO_STATUSES = ['draft', 'planned', 'confirmed', 'in_progress', 'completed', 'cancelled'] as const;
