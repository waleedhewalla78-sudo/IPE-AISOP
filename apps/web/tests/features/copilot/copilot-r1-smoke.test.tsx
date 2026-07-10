import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import { Sidebar } from '@/components/layout/Sidebar';
import { ROUTES } from '@/lib/constants';
import { RELEASE1_HUBS } from '@/lib/releaseProfile';
import { useAuth } from '@/features/auth/hooks/useAuth';

vi.mock('@/features/auth/hooks/useAuth');
vi.mock('@/lib/releaseProfile', () => ({
  IS_RELEASE1: true,
  IS_RELEASE2: false,
  RELEASE_PROFILE: 'release1',
  RELEASE1_HUBS: ['planning', 'command-center', 'platform', 'copilot'],
}));

describe('Copilot R1 smoke — release profile', () => {
  it('exposes copilot in RELEASE1_HUBS', () => {
    expect(RELEASE1_HUBS).toContain('copilot');
  });

  it('maps copilot route to ai-governance/copilot', () => {
    expect(ROUTES.AI_COPILOT).toBe('/ai-governance/copilot');
    expect(ROUTES.COPILOT).toBe('/copilot');
  });

  it('shows Copilot nav and hides POST-R1 hubs in release1 sidebar', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getByText('Copilot')).toBeInTheDocument();
    expect(screen.queryByText('Supply Chain')).not.toBeInTheDocument();
    expect(screen.queryByText('AI & Governance')).not.toBeInTheDocument();
  });
});

describe('Copilot R1 smoke — auth', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      user: null,
      token: null,
      login: vi.fn(),
      logout: vi.fn(),
      syncKeycloakSession: vi.fn(),
      authMode: 'local',
    });
  });

  it('redirects unauthenticated users from copilot route to login', () => {
    render(
      <MemoryRouter initialEntries={[ROUTES.AI_COPILOT]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path={ROUTES.AI_COPILOT} element={<div>Copilot page</div>} />
          </Route>
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText('Login page')).toBeInTheDocument();
    expect(screen.queryByText('Copilot page')).not.toBeInTheDocument();
  });

  it('allows authenticated users to reach copilot route', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { email: 'Ahmed@nour', role: 'planner' },
      token: 'test-token',
      login: vi.fn(),
      logout: vi.fn(),
      syncKeycloakSession: vi.fn(),
      authMode: 'local',
    });

    render(
      <MemoryRouter initialEntries={[ROUTES.AI_COPILOT]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path={ROUTES.AI_COPILOT} element={<div>Copilot page</div>} />
          </Route>
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText('Copilot page')).toBeInTheDocument();
  });
});
