import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { RouteFallback } from './RouteFallback';
import { AiDegradedBanner } from './AiDegradedBanner';
import { CopilotCommandPalette } from '@/features/copilot/components/CopilotCommandPalette';
import { FeatureErrorBoundary } from '@/components/ui/FeatureErrorBoundary';

export function MainLayout() {
  return (
    <CopilotCommandPalette>
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <Header />
          <AiDegradedBanner />
          <main className="flex-1 overflow-auto bg-ipe-surface p-6">
            <FeatureErrorBoundary>
              <Suspense fallback={<RouteFallback />}>
                <Outlet />
              </Suspense>
            </FeatureErrorBoundary>
          </main>
        </div>
      </div>
    </CopilotCommandPalette>
  );
}

