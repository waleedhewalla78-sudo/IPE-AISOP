import { lazy, type ComponentType } from 'react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function lazyNamed<M extends Record<string, ComponentType<any>>, K extends keyof M>(
  factory: () => Promise<M>,
  exportName: K,
) {
  return lazy(() => factory().then((mod) => ({ default: mod[exportName] })));
}

// Hub shells
export const PlanningHub = lazyNamed(() => import('@/features/hubs/planning/PlanningHub'), 'PlanningHub');
export const CommandCenterHub = lazyNamed(
  () => import('@/features/hubs/command-center/CommandCenterHub'),
  'CommandCenterHub',
);
export const SupplyChainHub = lazyNamed(() => import('@/features/hubs/supply-chain/SupplyChainHub'), 'SupplyChainHub');
export const AIGovernanceHub = lazyNamed(
  () => import('@/features/hubs/ai-governance/AIGovernanceHub'),
  'AIGovernanceHub',
);
export const PlatformHub = lazyNamed(() => import('@/features/hubs/platform/PlatformHub'), 'PlatformHub');

// Planning Hub tabs
export const PlanningDashboardPage = lazyNamed(
  () => import('@/features/hubs/planning/PlanningDashboardPage'),
  'PlanningDashboardPage',
);
export const ControlTowerPage = lazyNamed(
  () => import('@/features/control-tower/components/ControlTowerPage'),
  'ControlTowerPage',
);
export const ResolutionCenterPage = lazyNamed(
  () => import('@/features/resolution-center/components/ResolutionCenterPage'),
  'ResolutionCenterPage',
);
export const SchedulePage = lazyNamed(() => import('@/features/schedule/SchedulePage'), 'SchedulePage');
export const DemandForecastPage = lazyNamed(
  () => import('@/features/hubs/planning/DemandForecastPage'),
  'DemandForecastPage',
);
export const ScenarioWorkbenchPage = lazyNamed(
  () => import('@/features/hubs/planning/ScenarioWorkbenchPage'),
  'ScenarioWorkbenchPage',
);

// Command Center tabs
export const CommandCenterDashboardPage = lazyNamed(
  () => import('@/features/hubs/command-center/CommandCenterDashboardPage'),
  'CommandCenterDashboardPage',
);
export const WarRoomPage = lazyNamed(() => import('@/features/war-room/components/WarRoomPage'), 'WarRoomPage');
export const ExecutiveDashboardPage = lazyNamed(
  () => import('@/features/executive/components/ExecutiveDashboardPage'),
  'ExecutiveDashboardPage',
);
export const OutcomesPage = lazyNamed(
  () => import('@/features/executive/components/OutcomesPage'),
  'OutcomesPage',
);
export const CostOfChaosPage = lazyNamed(() => import('@/features/cost-of-chaos/CostOfChaosPage'), 'CostOfChaosPage');

// Supply Chain tabs
export const TariffPage = lazyNamed(() => import('@/features/tariff/TariffPage'), 'TariffPage');
export const SCNDashboard = lazyNamed(() => import('@/features/scn-portal/components/SCNDashboard'), 'SCNDashboard');
export const InventoryPage = lazyNamed(
  () => import('@/features/hubs/supply-chain/InventoryPage'),
  'InventoryPage',
);
export const SupplyPlanningPage = lazyNamed(
  () => import('@/features/hubs/supply-chain/SupplyPlanningPage'),
  'SupplyPlanningPage',
);
export const OrderManagementPage = lazyNamed(
  () => import('@/features/hubs/supply-chain/OrderManagementPage'),
  'OrderManagementPage',
);
export const ProcurementDashboardPage = lazyNamed(
  () => import('@/features/hubs/supply-chain/ProcurementDashboardPage'),
  'ProcurementDashboardPage',
);
export const EquipmentHealthPage = lazyNamed(
  () => import('@/features/hubs/command-center/EquipmentHealthPage'),
  'EquipmentHealthPage',
);

// AI & Governance tabs
export const CopilotPanel = lazyNamed(() => import('@/features/copilot/components/CopilotPanel'), 'CopilotPanel');
export const DesignAIPage = lazyNamed(
  () => import('@/features/hubs/ai-governance/DesignAIPage'),
  'DesignAIPage',
);
export const AITrustPage = lazyNamed(() => import('@/features/ai-trust/components/AITrustPage'), 'AITrustPage');
export const MdrDashboardPage = lazyNamed(
  () => import('@/features/mdr/components/MdrDashboardPage'),
  'MdrDashboardPage',
);
export const ComplianceDashboardPage = lazyNamed(
  () => import('@/features/compliance/components/ComplianceDashboardPage'),
  'ComplianceDashboardPage',
);
export const QualityPage = lazyNamed(() => import('@/features/quality/components/QualityPage'), 'QualityPage');
export const SustainabilityPage = lazyNamed(
  () => import('@/features/sustainability/components/SustainabilityPage'),
  'SustainabilityPage',
);

// Platform tabs
export const AdminPage = lazyNamed(() => import('@/features/admin/components/AdminPage'), 'AdminPage');
export const OnboardingWizard = lazyNamed(
  () => import('@/features/onboarding/components/OnboardingWizard'),
  'OnboardingWizard',
);
export const MLOpsDashboard = lazyNamed(
  () => import('@/features/ml-ops/components/MLOpsDashboard'),
  'MLOpsDashboard',
);

// Standalone
export const ShopFloorPage = lazyNamed(
  () => import('@/features/shop-floor/components/ShopFloorPage'),
  'ShopFloorPage',
);
