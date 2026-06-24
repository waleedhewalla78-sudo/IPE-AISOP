import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SchedulePage } from '@/features/schedule/SchedulePage';

vi.mock('@/features/schedule/api', () => ({
  fetchSchedule: vi.fn().mockResolvedValue({ rows: [], moVersions: {}, xaiExplanation: null, solverStatus: 'UNKNOWN' }),
  fetchActiveSchedule: vi.fn().mockResolvedValue({ rows: [], moVersions: {} }),
  approveSchedule: vi.fn().mockResolvedValue({ activated: [], failed: [] }),
  downloadMsProjectExport: vi.fn().mockResolvedValue(undefined),
}));

describe('SchedulePage', () => {
  it('renders schedule page with title and refresh button', async () => {
    render(
      <BrowserRouter>
        <SchedulePage />
      </BrowserRouter>,
    );
    expect(await screen.findByText('Schedule')).toBeInTheDocument();
    expect(screen.getByText('Refresh')).toBeInTheDocument();
    expect(screen.getByText(/Compare planned vs AI-suggested/)).toBeInTheDocument();
  });
});
