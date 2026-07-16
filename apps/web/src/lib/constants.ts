export const APP_NAME = 'IPE - Intelligent Planning Engine';
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ROUTES = {
  LOGIN: '/login',

  // Hub roots
  PLANNING: '/planning',
  COMMAND_CENTER: '/command-center',
  INTELLIGENCE: '/intelligence',
  CUSTOMER_PORTAL: '/customer-portal',
  SUPPLY_CHAIN: '/supply-chain',
  AI_GOVERNANCE: '/ai-governance',
  PLATFORM: '/platform',
  SHOP_FLOOR: '/shop-floor',
  WORKSPACE: '/workspace',

  // Planning Hub tabs
  PLANNING_DASHBOARD: '/planning/dashboard',
  PLANNING_CONTROL_TOWER: '/planning/control-tower',
  PLANNING_RESOLUTION: '/planning/resolution',
  PLANNING_SCHEDULE: '/planning/schedule',
  PLANNING_DEMAND: '/planning/demand',
  PLANNING_SCENARIOS: '/planning/scenarios',
  PLANNING_PREDICTIONS: '/planning/predictions',
  PLANNING_ROOT_CAUSE: '/planning/root-cause',
  PLANNING_COCKPIT: '/planning/cockpit',

  // Command Center tabs
  COMMAND_DASHBOARD: '/command-center/dashboard',
  COMMAND_WAR_ROOM: '/command-center/war-room',
  COMMAND_OPS_LIVE: '/command-center/ops-live',
  COMMAND_EXECUTIVE: '/command-center/executive',
  COMMAND_OUTCOMES: '/command-center/outcomes',
  COMMAND_COST_OF_CHAOS: '/command-center/cost-of-chaos',
  COMMAND_EQUIPMENT: '/command-center/equipment',
  COMMAND_SOP_REPORT: '/command-center/sop-report',
  COMMAND_OTD_ANALYTICS: '/command-center/otd-analytics',

  // Phase 4 Manufacturing Intelligence modules
  INTELLIGENCE_PULSE: '/intelligence/pulse',
  INTELLIGENCE_DEMAND: '/intelligence/demand',
  INTELLIGENCE_PRODUCTION: '/intelligence/production',
  INTELLIGENCE_SUPPLY: '/intelligence/supply',
  INTELLIGENCE_QUALITY: '/intelligence/quality',
  INTELLIGENCE_FINANCE: '/intelligence/finance',
  INTELLIGENCE_CUSTOMER: '/intelligence/customer',
  // Phase 6 Enterprise Agentic modules
  INTELLIGENCE_ANALYTICS: '/intelligence/analytics',
  INTELLIGENCE_COMMERCIAL: '/intelligence/commercial',
  INTELLIGENCE_PROCUREMENT: '/intelligence/procurement',

  // Supply Chain tabs
  SUPPLY_TARIFF: '/supply-chain/tariff',
  SUPPLY_SCN: '/supply-chain/scn-portal',
  SUPPLY_INVENTORY: '/supply-chain/inventory',
  SUPPLY_PLANNING: '/supply-chain/supply-planning',
  SUPPLY_ORDERS: '/supply-chain/orders',
  SUPPLY_PROCUREMENT: '/supply-chain/procurement',
  SUPPLY_SUPPLIERS: '/supply-chain/suppliers',
  // Phase 3 also exposes /material/suppliers alias via hub tab

  // AI & Governance tabs
  AI_COPILOT: '/ai-governance/copilot',
  AI_MEETING_PREP: '/ai-governance/meeting-prep',
  AI_DESIGN: '/ai-governance/design-ai',
  AI_TRUST: '/ai-governance/ai-trust',
  AI_MDR: '/ai-governance/mdr',
  AI_COMPLIANCE: '/ai-governance/compliance',
  AI_QUALITY: '/ai-governance/quality',
  AI_SUSTAINABILITY: '/ai-governance/sustainability',

  // Platform tabs
  PLATFORM_ADMIN: '/platform/admin',
  PLATFORM_UPLOAD: '/platform/upload',
  PLATFORM_AGENTS: '/platform/agents',
  PLATFORM_EXCEPTIONS: '/platform/exceptions',
  PLATFORM_ODOO_CONFIG: '/platform/odoo-config',
  PLATFORM_ONBOARDING: '/platform/onboarding',
  PLATFORM_MLOPS: '/platform/ml-ops',
  PLATFORM_OPS: '/platform/ops',
  // Spec aliases
  ADMIN_UPLOAD: '/admin/upload',
  MATERIAL_SUPPLIERS: '/material/suppliers',

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
