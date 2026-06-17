import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { MainLayout } from '@/components/layout';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { ControlTowerPage } from '@/features/control-tower/components/ControlTowerPage';
import { ResolutionCenterPage } from '@/features/resolution-center/components/ResolutionCenterPage';
import { CopilotPanel } from '@/features/copilot/components/CopilotPanel';
import { ShopFloorPage } from '@/features/shop-floor/components/ShopFloorPage';
import { AdminPage } from '@/features/admin/components/AdminPage';
import { ExecutiveDashboardPage } from '@/features/executive/components/ExecutiveDashboardPage';

function RequireAuth({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const token = localStorage.getItem('access_token');
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp as number | undefined;
    if (exp && Date.now() >= exp * 1000) {
      localStorage.removeItem('access_token');
      return <Navigate to="/login" state={{ from: location }} replace />;
    }
    if (roles) {
      const userRole = (payload.role as string) || '';
      if (!roles.includes(userRole)) {
        return <Navigate to="/" replace />;
      }
    }
  } catch {
    localStorage.removeItem('access_token');
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <MainLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/control-tower" replace />} />
        <Route path="control-tower" element={<ControlTowerPage />} />
        <Route path="resolution-center" element={<ResolutionCenterPage />} />
        <Route path="copilot" element={<CopilotPanel />} />
        <Route path="shop-floor" element={<ShopFloorPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="executive" element={<RequireAuth roles={['executive', 'admin']}><ExecutiveDashboardPage /></RequireAuth>} />
      </Route>
    </Routes>
  );
}
