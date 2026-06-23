import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ExecutiveDashboardPage } from '@/features/executive/components/ExecutiveDashboardPage';

vi.mock('@/features/executive/api', () => ({
  fetchExecutiveSummary: vi.fn().mockResolvedValue(null),
  fetchOTDByWorkCenter: vi.fn().mockResolvedValue([]),
  fetchDelayBreakdown: vi.fn().mockResolvedValue([]),
  fetchPlanningAccuracy: vi.fn().mockResolvedValue(null),
  fetchPnL: vi.fn().mockResolvedValue(null),
  fetchSopGapAnalysis: vi.fn().mockResolvedValue(null),
  fetchWhatIfScenarios: vi.fn().mockResolvedValue([]),
}));

describe('ExecutiveDashboardPage', () => {
  it('renders loading spinner initially', () => {
    render(
      <BrowserRouter>
        <ExecutiveDashboardPage />
      </BrowserRouter>,
    );
    // Page shows a spinner div while loading
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('renders executive dashboard after load', async () => {
    render(
      <BrowserRouter>
        <ExecutiveDashboardPage />
      </BrowserRouter>,
    );
    // Wait for async data loading to complete
    await vi.waitFor(() => {
      expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
