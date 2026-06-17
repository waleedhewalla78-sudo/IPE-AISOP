export const APP_NAME = 'IPE - Intelligent Planning Engine';
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ROUTES = {
  LOGIN: '/login',
  CONTROL_TOWER: '/control-tower',
  RESOLUTION_CENTER: '/resolution-center',
  COPILOT: '/copilot',
  SHOP_FLOOR: '/shop-floor',
  ADMIN: '/admin',
} as const;

export const DEMAND_TYPES = ['MTO', 'MTS', 'CTO', 'ETO'] as const;
export const MO_STATUSES = ['draft', 'planned', 'confirmed', 'in_progress', 'completed', 'cancelled'] as const;
