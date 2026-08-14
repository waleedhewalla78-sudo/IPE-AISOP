import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Breadcrumbs } from './Breadcrumbs';
import { RouteFallback } from './RouteFallback';
import { AiDegradedBanner } from './AiDegradedBanner';
import { CriticalAlertBanner } from './CriticalAlertBanner';
import { SessionIdleGuard } from './SessionIdleGuard';
import { ToastHost } from '@/components/ui/ToastHost';
import { CopilotCommandPalette } from '@/features/copilot/components/CopilotCommandPalette';
import { FeatureErrorBoundary } from '@/components/ui/FeatureErrorBoundary';

export function MainLayout() {
  return (
    <CopilotCommandPalette>
      <div className="flex h-screen bg-ipe-surface font-sans text-ipe-text">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header />
          <Breadcrumbs variant="bar" />
          <CriticalAlertBanner />
          <AiDegradedBanner />
          <main className="flex-1 overflow-auto p-4 lg:p-6">
            <div className="mx-auto max-w-content">
              <FeatureErrorBoundary>
                <Suspense fallback={<RouteFallback />}>
                  <Outlet />
                </Suspense>
              </FeatureErrorBoundary>
            </div>
          </main>
        </div>
        <ToastHost />
        <SessionIdleGuard />
      </div>
    </CopilotCommandPalette>
  );
}
