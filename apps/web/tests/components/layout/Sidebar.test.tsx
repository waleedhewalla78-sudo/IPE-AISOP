import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from '@/features/auth/store/authSlice';
import { Sidebar } from '@/components/layout/Sidebar';
import { ROUTES } from '@/lib/constants';

/**
 * Spec 040 / product redesign — Home · Plan · Execute · Supply · Analyze · Copilot · Admin.
 */

const DOMAIN_IDS = ['home', 'plan', 'execute', 'supply', 'analyze', 'copilot', 'admin'];

function renderSidebar(path = ROUTES.PLANNING_CONTROL_TOWER, role: 'admin' | 'manager' = 'admin') {
  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: {
      auth: {
        user: { id: 'u1', email: 'admin@example.com', full_name: 'Admin', role, tenant_id: 't1' },
        token: 'x',
        refreshToken: 'y',
        isAuthenticated: true,
      },
    },
  });
  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={[path]}>
        <Sidebar />
      </MemoryRouter>
    </Provider>,
  );
}

describe('Sidebar', () => {
  it('renders the domain icon rail', () => {
    renderSidebar();
    expect(screen.getByTestId('icon-rail')).toBeInTheDocument();
    DOMAIN_IDS.forEach((id) => {
      expect(screen.getByTestId(`domain-${id}`)).toBeInTheDocument();
    });
  });

  it('shows Plan modules when on a planning route', () => {
    renderSidebar(ROUTES.PLANNING_CONTROL_TOWER);
    expect(screen.getByTestId('domain-sidebar')).toHaveAttribute('data-domain', 'plan');
    expect(screen.getByRole('link', { name: /Control Tower/i })).toHaveAttribute(
      'href',
      ROUTES.PLANNING_CONTROL_TOWER,
    );
    expect(screen.getByRole('link', { name: /Demand Intelligence/i })).toHaveAttribute(
      'href',
      ROUTES.PLANNING_DEMAND,
    );
    expect(screen.getByRole('link', { name: /Resolution Center/i })).toBeInTheDocument();
  });

  it('hides domain sidebar on Home (full-bleed)', () => {
    renderSidebar(ROUTES.WORKSPACE);
    expect(screen.queryByTestId('domain-sidebar')).not.toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toHaveAttribute('data-domain', 'home');
  });

  it('shows Execute modules under Execute domain', () => {
    renderSidebar(ROUTES.WORK_PROJECTS);
    expect(screen.getByTestId('domain-sidebar')).toHaveAttribute('data-domain', 'execute');
    expect(screen.getByRole('link', { name: /Projects/i })).toHaveAttribute('href', ROUTES.WORK_PROJECTS);
    expect(screen.getByRole('link', { name: /Tasks/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Objectives/i })).toBeInTheDocument();
  });

  it('shows agent navigator in Copilot domain', () => {
    renderSidebar(ROUTES.AI_COPILOT);
    expect(screen.getByTestId('domain-sidebar')).toHaveAttribute('data-domain', 'copilot');
    expect(screen.getByTestId('agent-navigator')).toBeInTheDocument();
    expect(screen.getByTestId('agent-nav-A1')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Meeting Prep/i })).toHaveAttribute(
      'href',
      ROUTES.AI_MEETING_PREP,
    );
  });
});
