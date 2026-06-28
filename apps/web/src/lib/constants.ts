export const APP_NAME = 'IPE - Intelligent Planning Engine';
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ROUTES = {
  LOGIN: '/login',

  // Hub roots
  PLANNING: '/planning',
  COMMAND_CENTER: '/command-center',
  SUPPLY_CHAIN: '/supply-chain',
  AI_GOVERNANCE: '/ai-governance',
  PLATFORM: '/platform',
  SHOP_FLOOR: '/shop-floor',

  // Planning Hub tabs
  PLANNING_DASHBOARD: '/planning/dashboard',
  PLANNING_CONTROL_TOWER: '/planning/control-tower',
  PLANNING_RESOLUTION: '/planning/resolution',
  PLANNING_SCHEDULE: '/planning/schedule',
  PLANNING_DEMAND: '/planning/demand',
  PLANNING_SCENARIOS: '/planning/scenarios',

  // Command Center tabs
  COMMAND_DASHBOARD: '/command-center/dashboard',
  COMMAND_WAR_ROOM: '/command-center/war-room',
  COMMAND_EXECUTIVE: '/command-center/executive',
  COMMAND_COST_OF_CHAOS: '/command-center/cost-of-chaos',
  COMMAND_EQUIPMENT: '/command-center/equipment',

  // Supply Chain tabs
  SUPPLY_TARIFF: '/supply-chain/tariff',
  SUPPLY_SCN: '/supply-chain/scn-portal',
  SUPPLY_INVENTORY: '/supply-chain/inventory',
  SUPPLY_PLANNING: '/supply-chain/supply-planning',
  SUPPLY_ORDERS: '/supply-chain/orders',
  SUPPLY_PROCUREMENT: '/supply-chain/procurement',

  // AI & Governance tabs
  AI_COPILOT: '/ai-governance/copilot',
  AI_DESIGN: '/ai-governance/design-ai',
  AI_TRUST: '/ai-governance/ai-trust',
  AI_MDR: '/ai-governance/mdr',
  AI_COMPLIANCE: '/ai-governance/compliance',
  AI_QUALITY: '/ai-governance/quality',
  AI_SUSTAINABILITY: '/ai-governance/sustainability',

  // Platform tabs
  PLATFORM_ADMIN: '/platform/admin',
  PLATFORM_ONBOARDING: '/platform/onboarding',
  PLATFORM_MLOPS: '/platform/ml-ops',

  // Legacy aliases (redirects in router)
  CONTROL_TOWER: '/control-tower',
  SCHEDULE: '/schedule',
  RESOLUTION_CENTER: '/resolution-center',
  COPILOT: '/copilot',
  EXECUTIVE: '/executive',
  COST_OF_CHAOS: '/cost-of-chaos',
  TARIFF: '/tariff',
  WAR_ROOM: '/war-room',
  SCN_PORTAL: '/scn-portal',
  ML_OPS: '/ml-ops',
  ONBOARDING: '/onboarding',
  ADMIN: '/admin',
} as const;

export const DEMAND_TYPES = ['MTO', 'MTS', 'CTO', 'ETO'] as const;
export const MO_STATUSES = ['draft', 'planned', 'confirmed', 'in_progress', 'completed', 'cancelled'] as const;
