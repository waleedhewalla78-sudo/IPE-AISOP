import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResolutionCenterPage } from '@/features/resolution-center/components/ResolutionCenterPage';

const mockScenarios = [
  {
    id: 'scn-1',
    mo_id: 'MO-1001',
    strategy: 'Expedite supplier',
    delivery_impact_days: 2,
    cost_impact: 500,
    business_score: 0.72,
    status: 'proposed',
  },
  {
    id: 'scn-2',
    mo_id: 'MO-1004',
    strategy: 'Substitute material',
    delivery_impact_days: 1,
    cost_impact: 200,
    business_score: 0.65,
    status: 'proposed',
  },
  {
    id: 'scn-3',
    mo_id: 'MO-1008',
    strategy: 'Split batch',
    delivery_impact_days: 3,
    cost_impact: 150,
    business_score: 0.58,
    status: 'proposed',
  },
];

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn((_url: string, config?: { params?: { mo_id?: string } }) => {
      const moId = config?.params?.mo_id;
      const scenarios = moId
        ? mockScenarios.filter((s) => s.mo_id === moId)
        : mockScenarios;
      return Promise.resolve({ data: { data: { scenarios } } });
    }),
  },
}));

describe('ResolutionCenterPage', () => {
  it('renders the page title and unresolved MOs list', async () => {
    render(<ResolutionCenterPage />);

    expect(await screen.findByText('Resolution Center')).toBeInTheDocument();
    expect(screen.getByText((content) => content.startsWith('Unresolved MOs'))).toBeInTheDocument();
    expect(screen.getByText('MO-1001')).toBeInTheDocument();
    expect(screen.getByText('MO-1004')).toBeInTheDocument();
    expect(screen.getByText('MO-1008')).toBeInTheDocument();
  });

  it('shows select hint when no MO is selected', async () => {
    render(<ResolutionCenterPage />);

    expect(await screen.findByText('Select an MO')).toBeInTheDocument();
  });

  it('shows constraint and scenario panels when an MO is clicked', async () => {
    render(<ResolutionCenterPage />);

    const moRow = await screen.findByText('MO-1001');
    moRow.click();

    expect(await screen.findByText((content) => content.includes('Constraints'))).toBeInTheDocument();
    expect(screen.getByText((content) => content.startsWith('Scenarios for'))).toBeInTheDocument();
    expect(screen.getByText('Expedite supplier')).toBeInTheDocument();
  });
});
