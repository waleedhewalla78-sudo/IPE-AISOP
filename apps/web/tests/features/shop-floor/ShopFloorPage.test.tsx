import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ShopFloorPage } from '@/features/shop-floor/components/ShopFloorPage';

const TEST_TENANT = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

const mockItems = [
  {
    id: '1',
    mo_id: 'MO-2001',
    workcenter: 'Assembly Line 1',
    status: 'in_progress',
    progress: 45,
    operator: 'John Smith',
    start_time: '2026-06-21T08:00:00Z',
  },
  {
    id: '2',
    mo_id: 'MO-2002',
    workcenter: 'Machining Center',
    status: 'pending',
    progress: 0,
    operator: 'Jane Doe',
    start_time: '2026-06-21T09:00:00Z',
  },
];

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      json: async () => ({ items: mockItems }),
    }),
  );
});

describe('ShopFloorPage', () => {
  it('renders page title and work center cards', async () => {
    render(<ShopFloorPage tenantId={TEST_TENANT} />);

    expect(await screen.findByText('Shop Floor PWA')).toBeInTheDocument();
    expect(screen.getByText('MO-2001')).toBeInTheDocument();
    expect(screen.getByText('Assembly Line 1')).toBeInTheDocument();
    expect(screen.getByText('MO-2002')).toBeInTheDocument();
    expect(screen.getByText('Machining Center')).toBeInTheDocument();
  });

  it('shows in progress and pending sections', async () => {
    render(<ShopFloorPage tenantId={TEST_TENANT} />);

    expect(await screen.findByText(/In Progress \(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/Pending \(1\)/)).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('shows barcode scan input', async () => {
    render(<ShopFloorPage tenantId={TEST_TENANT} />);

    expect(await screen.findByPlaceholderText('Scan MO barcode or enter ID...')).toBeInTheDocument();
  });
});
