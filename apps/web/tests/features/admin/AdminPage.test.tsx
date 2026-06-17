import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AdminPage } from '@/features/admin/components/AdminPage';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn().mockRejectedValue(new Error('Not connected')),
    put: vi.fn().mockRejectedValue(new Error('Not connected')),
  },
}));

describe('AdminPage', () => {
  it('renders admin page title and tabs', async () => {
    render(
      <BrowserRouter>
        <AdminPage />
      </BrowserRouter>,
    );

    expect(await screen.findByText('Admin Console')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByText('Data Quality')).toBeInTheDocument();
  });

  it('shows data quality metrics when tab is clicked', async () => {
    render(
      <BrowserRouter>
        <AdminPage />
      </BrowserRouter>,
    );

    expect(await screen.findByText('Admin Console')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Data Quality'));

    expect(await screen.findByText('BOM Completeness')).toBeInTheDocument();
    expect(screen.getByText('Lead Time Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Inventory Record Accuracy')).toBeInTheDocument();
  });
});
