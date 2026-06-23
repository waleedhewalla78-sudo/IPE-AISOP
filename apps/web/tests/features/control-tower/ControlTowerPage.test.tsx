import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ControlTowerPage } from '@/features/control-tower/components/ControlTowerPage';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn().mockRejectedValue(new Error('Not connected')),
  },
}));

describe('ControlTowerPage', () => {
  it('renders KPI cards and risk queue table', async () => {
    render(
      <BrowserRouter>
        <ControlTowerPage />
      </BrowserRouter>,
    );

    expect(await screen.findByText('Control Tower')).toBeInTheDocument();
    expect(screen.getByText('On-Time Delivery')).toBeInTheDocument();
    expect(screen.getByText('Avg Feasibility Score')).toBeInTheDocument();
    expect(screen.getByText('Active Bottlenecks')).toBeInTheDocument();
    expect(screen.getByText('Orders at Risk')).toBeInTheDocument();

    expect(screen.getByText((content) => content.startsWith('MO Risk Queue'))).toBeInTheDocument();
    expect(screen.getByText('Bottleneck Map')).toBeInTheDocument();
  });
});
