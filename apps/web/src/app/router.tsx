import { Navigate, Route, Routes } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { AdminPage } from '@/features/admin/components/AdminPage';
import { SCNDashboard } from '@/features/scn-portal/components/SCNDashboard';
import { ShopFloorPage } from '@/features/shop-floor/components/ShopFloorPage';
import { MLOpsDashboard } from '@/features/ml-ops/components/MLOpsDashboard';
import { ControlTowerPage } from '@/features/control-tower/components/ControlTowerPage';
import { ResolutionCenterPage } from '@/features/resolution-center/components/ResolutionCenterPage';
import { ExecutiveDashboardPage } from '@/features/executive/components/ExecutiveDashboardPage';
import { WarRoomPage } from '@/features/war-room/components/WarRoomPage';
import { AITrustPage } from '@/features/ai-trust/components/AITrustPage';
import { SchedulePage } from '@/features/schedule/SchedulePage';
import { OnboardingWizard } from '@/features/onboarding/components/OnboardingWizard';
import { QualityPage } from '@/features/quality/components/QualityPage';
import { SustainabilityPage } from '@/features/sustainability/components/SustainabilityPage';
import { ComplianceDashboardPage } from '@/features/compliance/components/ComplianceDashboardPage';
import { CopilotPanel } from '@/features/copilot/components/CopilotPanel';
import { MdrDashboardPage } from '@/features/mdr/components/MdrDashboardPage';

const tenantId = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Navigate to="/control-tower" replace />} />
          <Route path="/control-tower" element={<ControlTowerPage />} />
          <Route path="/schedule" element={<SchedulePage />} />
          <Route path="/resolution" element={<ResolutionCenterPage />} />
          <Route path="/resolution-center" element={<ResolutionCenterPage />} />
          <Route path="/copilot" element={<CopilotPanel />} />
          <Route path="/executive" element={<ExecutiveDashboardPage />} />
          <Route path="/scn-portal" element={<SCNDashboard tenantId={tenantId} />} />
          <Route path="/shop-floor" element={<ShopFloorPage tenantId={tenantId} />} />
          <Route path="/war-room" element={<WarRoomPage />} />
          <Route path="/ai-trust" element={<AITrustPage />} />
          <Route path="/ml-ops" element={<MLOpsDashboard tenantId={tenantId} />} />
          <Route path="/onboarding" element={<OnboardingWizard />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/quality" element={<QualityPage />} />
          <Route path="/sustainability" element={<SustainabilityPage />} />
          <Route path="/compliance" element={<ComplianceDashboardPage />} />
          <Route path="/mdr" element={<MdrDashboardPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/control-tower" replace />} />
    </Routes>
  );
}
