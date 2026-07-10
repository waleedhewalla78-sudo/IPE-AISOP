import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { PlanningHub } from '@/features/hubs/planning/PlanningHub';
import { RELEASE2_HUBS } from '@/lib/releaseProfile';

vi.mock('@/lib/releaseProfile', () => ({
  IS_RELEASE1: false,
  IS_RELEASE2: true,
  IS_TRIMMED_RELEASE: true,
  RELEASE_PROFILE: 'release2',
  RELEASE1_HUBS: ['planning', 'command-center', 'platform', 'copilot'],
  RELEASE2_HUBS: ['planning', 'command-center', 'platform', 'copilot', 'demand', 'scenarios'],
  isHubEnabled: (hub: string) =>
    ['planning', 'command-center', 'platform', 'copilot', 'demand', 'scenarios'].includes(hub),
}));

describe('Release 2 profile — hubs', () => {
  it('RELEASE2_HUBS includes demand and scenarios', () => {
    expect(RELEASE2_HUBS).toContain('demand');
    expect(RELEASE2_HUBS).toContain('scenarios');
    expect(RELEASE2_HUBS).toContain('copilot');
  });

  it('sidebar shows Copilot and hides supply chain in release2', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getByText('Copilot')).toBeInTheDocument();
    expect(screen.queryByText('Supply Chain')).not.toBeInTheDocument();
    expect(screen.queryByText('Shop Floor')).not.toBeInTheDocument();
  });

  it('planning hub shows Demand and Scenarios tabs in release2', () => {
    render(
      <MemoryRouter initialEntries={['/planning']}>
        <PlanningHub />
      </MemoryRouter>,
    );
    expect(screen.getByText('Demand')).toBeInTheDocument();
    expect(screen.getByText('Scenarios')).toBeInTheDocument();
  });
});
