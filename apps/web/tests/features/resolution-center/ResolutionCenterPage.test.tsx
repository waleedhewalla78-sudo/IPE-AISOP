import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ResolutionCenterPage } from '@/features/resolution-center/components/ResolutionCenterPage';

function withRouter(node: ReactNode) {
  return <MemoryRouter initialEntries={['/planning/resolution']}>{node}</MemoryRouter>;
}

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
    get: vi.fn((url: string, config?: { params?: { mo_id?: string } }) => {
      if (url.includes('/feasibility/queue')) {
        // Serve a matching feasibility queue so the page can construct its
        // unresolved MO list; mo_ids intentionally match the mocked scenarios.
        return Promise.resolve({
          data: {
            data: mockScenarios.map((s) => ({
              mo_id: s.mo_id,
              erp_mo_id: s.mo_id,
              product_name: 'Widget',
              feasibility_score: 65,
              primary_constraint: 'material',
            })),
          },
        });
      }
      const moId = config?.params?.mo_id;
      const scenarios = moId
        ? mockScenarios.filter((s) => s.mo_id === moId)
        : mockScenarios;
      return Promise.resolve({ data: { data: { scenarios } } });
    }),
    post: vi.fn(() => Promise.resolve({ data: { data: {} } })),
  },
}));

describe('ResolutionCenterPage', () => {
  it('renders the page title and unresolved MOs list', async () => {
    render(withRouter(<ResolutionCenterPage />));

    expect(await screen.findByText(/Resolution [Cc]enter/)).toBeInTheDocument();
    expect(screen.getByText((content) => content.startsWith('Unresolved MOs'))).toBeInTheDocument();
    expect(screen.getAllByText(/MO-1001/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MO-1004/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MO-1008/).length).toBeGreaterThan(0);
  });

  it('shows select hint when no MO is selected', async () => {
    render(withRouter(<ResolutionCenterPage />));

    expect(await screen.findByText(/Select an MO/)).toBeInTheDocument();
  });

  it('shows constraint and scenario panels when an MO is clicked', async () => {
    render(withRouter(<ResolutionCenterPage />));

    const moRow = (await screen.findAllByText(/MO-1001/))[0];
    moRow.click();

    // Spec 035: per-scenario option cards (no separate Constraints heading).
    expect(await screen.findByText('Expedite supplier')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Approve this path/i })).toBeInTheDocument();
  });
});
