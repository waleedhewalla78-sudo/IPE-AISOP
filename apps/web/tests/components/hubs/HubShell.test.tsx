import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { HubShell } from '@/components/hubs/HubShell';

const tabs = [
  { to: '/planning/dashboard', label: 'Dashboard' },
  { to: '/planning/control-tower', label: 'Control Tower' },
];

function renderHub(initialPath = '/planning/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/planning" element={<HubShell title="Planning Hub" subtitle="Detect → decide → schedule" tabs={tabs} />}>
          <Route path="dashboard" element={<div>Dashboard content</div>} />
          <Route path="control-tower" element={<div>Control Tower content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('HubShell', () => {
  it('renders hub title, subtitle, and tab links', () => {
    renderHub();
    expect(screen.getByRole('heading', { name: 'Planning Hub' })).toBeInTheDocument();
    expect(screen.getByText('Detect → decide → schedule')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/planning/dashboard');
    expect(screen.getByRole('link', { name: 'Control Tower' })).toHaveAttribute('href', '/planning/control-tower');
  });

  it('renders nested route content via Outlet', () => {
    renderHub('/planning/control-tower');
    expect(screen.getByText('Control Tower content')).toBeInTheDocument();
  });
});
