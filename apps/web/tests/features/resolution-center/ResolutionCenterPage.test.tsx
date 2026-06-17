import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResolutionCenterPage } from '@/features/resolution-center/components/ResolutionCenterPage';

describe('ResolutionCenterPage', () => {
  it('renders the page title and unresolved MOs list', () => {
    render(<ResolutionCenterPage />);

    expect(screen.getByText('Resolution Center')).toBeInTheDocument();
    expect(screen.getByText((content) => content.startsWith('Unresolved MOs'))).toBeInTheDocument();
    expect(screen.getByText('MO-1001')).toBeInTheDocument();
    expect(screen.getByText('MO-1004')).toBeInTheDocument();
    expect(screen.getByText('MO-1008')).toBeInTheDocument();
  });

  it('shows select hint when no MO is selected', () => {
    render(<ResolutionCenterPage />);

    expect(screen.getByText('Select an MO')).toBeInTheDocument();
  });

  it('shows constraint and scenario panels when an MO is clicked', async () => {
    render(<ResolutionCenterPage />);

    const moRow = screen.getByText('MO-1001');
    moRow.click();

    expect(await screen.findByText((content) => content.includes('Constraints'))).toBeInTheDocument();
    expect(screen.getByText((content) => content.startsWith('Scenarios for'))).toBeInTheDocument();
    expect(screen.getByText('Expedite supplier')).toBeInTheDocument();
    expect(screen.getByText('Substitute material')).toBeInTheDocument();
  });
});
