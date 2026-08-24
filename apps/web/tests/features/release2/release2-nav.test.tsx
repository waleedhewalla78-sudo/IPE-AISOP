import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from '@/features/auth/store/authSlice';
import { Sidebar } from '@/components/layout/Sidebar';
import { PlanningHub } from '@/features/hubs/planning/PlanningHub';
import { RELEASE2_HUBS } from '@/lib/releaseProfile';
import { ROUTES } from '@/lib/constants';

vi.mock('@/lib/releaseProfile', () => ({
  IS_RELEASE1: false,
  IS_RELEASE2: true,
  IS_CONSTRAINED_RELEASE: true,
  IS_TRIMMED_RELEASE: true,
  SHOW_R2_PLANNING_TABS: true,
  RELEASE_PROFILE: 'release2',
  RELEASE1_HUBS: ['planning', 'command-center', 'platform', 'copilot'],
  RELEASE2_HUBS: ['planning', 'command-center', 'platform', 'copilot', 'demand', 'scenarios'],
  isHubEnabled: (hub: string) =>
    ['planning', 'command-center', 'platform', 'copilot', 'demand', 'scenarios'].includes(hub),
}));

function renderWithStore(ui: React.ReactElement, initialEntries: string[] = ['/']) {
  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: {
      auth: {
        user: {
          id: 'u1',
          email: 'ops@example.com',
          full_name: 'Ops Manager',
          role: 'manager',
          tenant_id: 't1',
        },
        token: 'x',
        refreshToken: 'y',
        isAuthenticated: true,
      },
    },
  });
  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </Provider>,
  );
}

describe('Release 2 profile — hubs (Spec 039 grouped nav)', () => {
  it('RELEASE2_HUBS includes demand and scenarios', () => {
    expect(RELEASE2_HUBS).toContain('demand');
    expect(RELEASE2_HUBS).toContain('scenarios');
    expect(RELEASE2_HUBS).toContain('copilot');
  });

  it('sidebar shows Copilot in release2 and hides legacy hub labels', () => {
    renderWithStore(<Sidebar />);
    expect(screen.getAllByText('Copilot').length).toBeGreaterThan(0);
    // Legacy hub chrome labels (not domain module rows on Home full-bleed)
    expect(screen.queryByText('Materials & Supply')).not.toBeInTheDocument();
    expect(screen.queryByText('Supply Chain')).not.toBeInTheDocument();
  });

  it('planning shell renders; Demand and Scenarios stay in Plan domain sidebar', () => {
    renderWithStore(
      <>
        <Sidebar />
        <PlanningHub />
      </>,
      [ROUTES.PLANNING_CONTROL_TOWER],
    );
    expect(screen.getByTestId('planning-hub')).toBeInTheDocument();
    expect(screen.getByTestId('domain-sidebar')).toHaveAttribute('data-domain', 'plan');
    expect(screen.getByRole('link', { name: /Demand Intelligence/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Scenario/i })).toBeInTheDocument();
  });
});
