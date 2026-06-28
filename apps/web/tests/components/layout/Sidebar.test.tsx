import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { ROUTES } from '@/lib/constants';

const HUB_LABELS = [
  'Planning Hub',
  'Command Center',
  'Supply Chain',
  'AI & Governance',
  'Shop Floor',
  'Platform',
];

function renderSidebar(path = ROUTES.PLANNING_DASHBOARD) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Sidebar />
    </MemoryRouter>,
  );
}

describe('Sidebar', () => {
  it('renders six hub navigation items', () => {
    renderSidebar();
    HUB_LABELS.forEach((label) => {
      expect(screen.getByRole('link', { name: new RegExp(label) })).toBeInTheDocument();
    });
  });

  it('links to hub root routes', () => {
    renderSidebar();
    expect(screen.getByRole('link', { name: /Planning Hub/i })).toHaveAttribute('href', ROUTES.PLANNING);
    expect(screen.getByRole('link', { name: /Command Center/i })).toHaveAttribute('href', ROUTES.COMMAND_CENTER);
    expect(screen.getByRole('link', { name: /Shop Floor/i })).toHaveAttribute('href', ROUTES.SHOP_FLOOR);
  });
});
