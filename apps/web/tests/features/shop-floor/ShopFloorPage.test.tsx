import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ShopFloorPage } from '@/features/shop-floor/components/ShopFloorPage';

describe('ShopFloorPage', () => {
  it('renders page title and work center cards', () => {
    render(<ShopFloorPage />);

    expect(screen.getByText('Shop Floor')).toBeInTheDocument();
    expect(screen.getByText('Assembly Line 1')).toBeInTheDocument();
    expect(screen.getByText('Machining Center')).toBeInTheDocument();
    expect(screen.getByText('Packaging Station')).toBeInTheDocument();
    expect(screen.getByText('Quality Lab')).toBeInTheDocument();
    expect(screen.getByText('Heat Treat')).toBeInTheDocument();
  });

  it('shows all active orders table', () => {
    render(<ShopFloorPage />);

    expect(screen.getByText((content) => content.startsWith('All Active Orders'))).toBeInTheDocument();
    const moRefs = screen.getAllByText(/^MO-/);
    expect(moRefs.length).toBeGreaterThanOrEqual(3);
    const progressBadges = screen.getAllByText(/in progress/i);
    expect(progressBadges.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('delayed')).toBeInTheDocument();
  });

  it('shows delay alerts panel', () => {
    render(<ShopFloorPage />);

    expect(screen.getByText((content) => content.startsWith('Delay Alerts'))).toBeInTheDocument();
  });
});
