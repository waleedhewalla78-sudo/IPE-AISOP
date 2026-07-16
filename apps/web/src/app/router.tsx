import { Navigate, Route, Routes } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import { LoginForm } from '@/features/auth/components/LoginForm';
import {
  PlanningHub,
  CommandCenterHub,
  IntelligenceHub,
  SupplyChainHub,
  AIGovernanceHub,
  PlatformHub,
  PlanningDashboardPage,
  ControlTowerPage,
  ResolutionCenterPage,
  SchedulePage,
  DemandForecastPage,
  ScenarioWorkbenchPage,
  CommandCenterDashboardPage,
  WarRoomPage,
  ExecutiveDashboardPage,
  OutcomesPage,
  CostOfChaosPage,
  OTDDashboardPage,
  TariffPage,
  SCNDashboard,
  InventoryPage,
  SupplyPlanningPage,
  OrderManagementPage,
  ProcurementDashboardPage,
  EquipmentHealthPage,
  CopilotPanel,
  DesignAIPage,
  AITrustPage,
  MdrDashboardPage,
  ComplianceDashboardPage,
  QualityPage,
  SustainabilityPage,
  AdminPage,
  OdooConfigPage,
  OdooConnectionsPage,
  OnboardingWizard,
  MLOpsDashboard,
  OpsDashboard,
  SOPReport,
  ShopFloorPage,
  UnifiedWorkspacePage,
  PredictiveViewPage,
  RootCauseExplorerPage,
  DataUploadCenterPage,
  AgentDashboardPage,
  ExceptionManagerPage,
  SupplierScorecardPage,
  MeetingPrepPage,
  IntelligencePulsePage,
  DemandCommandPage,
  ProductionCommandPage,
  SupplyCommandPage,
  QualityCommandPage,
  FinanceCommandPage,
  CustomerCommandPage,
  AnalyticsCommandPage,
  CommercialCommandPage,
  ProcurementCommandPage,
  CustomerPortalPage,
  PlanningCockpitPage,
  OpsLivePage,
} from '@/app/lazyRoutes';
import { ROUTES } from '@/lib/constants';

const tenantId = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

function LegacyRedirect({ to }: { to: string }) {
  return <Navigate to={to} replace />;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Navigate to={ROUTES.WORKSPACE} replace />} />

          <Route path={ROUTES.WORKSPACE} element={<UnifiedWorkspacePage />} />

          {/* Planning Hub */}
          <Route path={ROUTES.PLANNING} element={<PlanningHub />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<PlanningDashboardPage />} />
            <Route path="cockpit" element={<PlanningCockpitPage />} />
            <Route path="demand" element={<DemandForecastPage />} />
            <Route path="scenarios" element={<ScenarioWorkbenchPage />} />
            <Route path="control-tower" element={<ControlTowerPage />} />
            <Route path="resolution" element={<ResolutionCenterPage />} />
            <Route path="schedule" element={<SchedulePage />} />
            <Route path="predictions" element={<PredictiveViewPage />} />
            <Route path="root-cause" element={<RootCauseExplorerPage />} />
            <Route path="root-cause/:moId" element={<RootCauseExplorerPage />} />
          </Route>

          {/* Command Center */}
          <Route path={ROUTES.COMMAND_CENTER} element={<CommandCenterHub />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<CommandCenterDashboardPage />} />
            <Route path="ops-live" element={<OpsLivePage />} />
            <Route path="war-room" element={<WarRoomPage />} />
            <Route path="executive" element={<ExecutiveDashboardPage />} />
            <Route path="outcomes" element={<OutcomesPage />} />
            <Route path="equipment" element={<EquipmentHealthPage />} />
            <Route path="cost-of-chaos" element={<CostOfChaosPage />} />
            <Route path="otd-analytics" element={<OTDDashboardPage />} />
            <Route path="sop-report" element={<SOPReport />} />
          </Route>

          {/* Phase 4 Manufacturing Intelligence */}
          <Route path={ROUTES.INTELLIGENCE} element={<IntelligenceHub />}>
            <Route index element={<Navigate to="pulse" replace />} />
            <Route path="pulse" element={<IntelligencePulsePage />} />
            <Route path="demand" element={<DemandCommandPage />} />
            <Route path="production" element={<ProductionCommandPage />} />
            <Route path="supply" element={<SupplyCommandPage />} />
            <Route path="quality" element={<QualityCommandPage />} />
            <Route path="finance" element={<FinanceCommandPage />} />
            <Route path="customer" element={<CustomerCommandPage />} />
            <Route path="analytics" element={<AnalyticsCommandPage />} />
            <Route path="commercial" element={<CommercialCommandPage />} />
            <Route path="procurement" element={<ProcurementCommandPage />} />
          </Route>

          <Route path={ROUTES.CUSTOMER_PORTAL} element={<CustomerPortalPage />} />

          {/* Supply Chain Hub */}
          <Route path={ROUTES.SUPPLY_CHAIN} element={<SupplyChainHub />}>
            <Route index element={<Navigate to="supply-planning" replace />} />
            <Route path="supply-planning" element={<SupplyPlanningPage />} />
            <Route path="orders" element={<OrderManagementPage />} />
            <Route path="procurement" element={<ProcurementDashboardPage />} />
            <Route path="tariff" element={<TariffPage />} />
            <Route path="scn-portal" element={<SCNDashboard tenantId={tenantId} />} />
            <Route path="inventory" element={<InventoryPage />} />
            <Route path="suppliers" element={<SupplierScorecardPage />} />
          </Route>

          {/* AI & Governance */}
          <Route path={ROUTES.AI_GOVERNANCE} element={<AIGovernanceHub />}>
            <Route index element={<Navigate to="copilot" replace />} />
            <Route path="copilot" element={<CopilotPanel />} />
            <Route path="meeting-prep" element={<MeetingPrepPage />} />
            <Route path="meeting-prep/:type" element={<MeetingPrepPage />} />
            <Route path="design-ai" element={<DesignAIPage />} />
            <Route path="ai-trust" element={<AITrustPage />} />
            <Route path="mdr" element={<MdrDashboardPage />} />
            <Route path="compliance" element={<ComplianceDashboardPage />} />
            <Route path="quality" element={<QualityPage />} />
            <Route path="sustainability" element={<SustainabilityPage />} />
          </Route>

          {/* Platform */}
          <Route path={ROUTES.PLATFORM} element={<PlatformHub />}>
            <Route index element={<Navigate to="admin" replace />} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="upload" element={<DataUploadCenterPage />} />
            <Route path="agents" element={<AgentDashboardPage />} />
            <Route path="exceptions" element={<ExceptionManagerPage />} />
            <Route path="odoo-config" element={<OdooConnectionsPage />} />
            <Route path="odoo-config/versions" element={<OdooConfigPage />} />
            <Route path="onboarding" element={<OnboardingWizard />} />
            <Route path="ml-ops" element={<MLOpsDashboard tenantId={tenantId} />} />
            <Route path="ops" element={<OpsDashboard />} />
          </Route>

          <Route path={ROUTES.SHOP_FLOOR} element={<ShopFloorPage tenantId={tenantId} />} />

          {/* Legacy routes → hub tabs (demo scripts & bookmarks) */}
          <Route path="/control-tower" element={<LegacyRedirect to={ROUTES.PLANNING_CONTROL_TOWER} />} />
          <Route path="/schedule" element={<LegacyRedirect to={ROUTES.PLANNING_SCHEDULE} />} />
          <Route path="/resolution" element={<LegacyRedirect to={ROUTES.PLANNING_RESOLUTION} />} />
          <Route path="/resolution-center" element={<LegacyRedirect to={ROUTES.PLANNING_RESOLUTION} />} />
          <Route path="/copilot" element={<LegacyRedirect to={ROUTES.AI_COPILOT} />} />
          <Route path="/executive" element={<LegacyRedirect to={ROUTES.COMMAND_EXECUTIVE} />} />
          <Route path="/war-room" element={<LegacyRedirect to={ROUTES.COMMAND_WAR_ROOM} />} />
          <Route path="/cost-of-chaos" element={<LegacyRedirect to={ROUTES.COMMAND_COST_OF_CHAOS} />} />
          <Route path="/tariff" element={<LegacyRedirect to={ROUTES.SUPPLY_TARIFF} />} />
          <Route path="/scn-portal" element={<LegacyRedirect to={ROUTES.SUPPLY_SCN} />} />
          <Route path="/ai-trust" element={<LegacyRedirect to={ROUTES.AI_TRUST} />} />
          <Route path="/mdr" element={<LegacyRedirect to={ROUTES.AI_MDR} />} />
          <Route path="/compliance" element={<LegacyRedirect to={ROUTES.AI_COMPLIANCE} />} />
          <Route path="/quality" element={<LegacyRedirect to={ROUTES.AI_QUALITY} />} />
          <Route path="/sustainability" element={<LegacyRedirect to={ROUTES.AI_SUSTAINABILITY} />} />
          <Route path="/admin" element={<LegacyRedirect to={ROUTES.PLATFORM_ADMIN} />} />
          <Route path="/admin/upload" element={<LegacyRedirect to={ROUTES.PLATFORM_UPLOAD} />} />
          <Route path="/material/suppliers" element={<LegacyRedirect to={ROUTES.SUPPLY_SUPPLIERS} />} />
          <Route path="/copilot/meeting/:type" element={<LegacyRedirect to={ROUTES.AI_MEETING_PREP} />} />
          <Route path="/onboarding" element={<LegacyRedirect to={ROUTES.PLATFORM_ONBOARDING} />} />
          <Route path="/ml-ops" element={<LegacyRedirect to={ROUTES.PLATFORM_MLOPS} />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to={ROUTES.PLANNING_DASHBOARD} replace />} />
    </Routes>
  );
}
