import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CopilotPanel } from '@/features/copilot/components/CopilotPanel';
import { ROUTES } from '@/lib/constants';

function renderCopilot() {
  return render(
    <MemoryRouter initialEntries={[ROUTES.AI_COPILOT]}>
      <CopilotPanel />
    </MemoryRouter>,
  );
}

describe('CopilotPanel', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: async () => ({ success: true, data: {} }),
        }),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders copilot title and input', () => {
    renderCopilot();
    expect(screen.getByTestId('copilot-panel')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Copilot' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask about your production/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument();
  });

  it('renders empty state message when no messages', () => {
    renderCopilot();
    expect(screen.getByText(/switch agents from the left navigator/i)).toBeInTheDocument();
    expect(screen.getByText(/not configured/i)).toBeInTheDocument();
  });
});
