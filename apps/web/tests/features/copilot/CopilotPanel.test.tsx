import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CopilotPanel } from '@/features/copilot/components/CopilotPanel';

describe('CopilotPanel', () => {
  it('renders copilot title and input', () => {
    render(<CopilotPanel />);
    expect(screen.getByText('Copilot')).toBeInTheDocument();
    expect(screen.getByText(/Ask questions about your production plan/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask about your production/)).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('renders empty state message when no messages', () => {
    render(<CopilotPanel />);
    expect(screen.getByText(/Ask about demand, material status/)).toBeInTheDocument();
  });
});
