import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { OdooConfigPanel } from '@/features/admin/components/OdooConfigPanel';

vi.mock('@/lib/i18n', () => ({
  t: (key: string) => key,
}));

vi.mock('@/features/admin/api', () => ({
  fetchOdooConfig: vi.fn().mockResolvedValue({
    odoo_url: 'http://odoo.local',
    odoo_db: 'ipe',
    odoo_username: 'admin',
    enabled: true,
    password_set: true,
    sync_interval_minutes: 900,
  }),
  fetchSyncDqFlags: vi.fn().mockResolvedValue([
    {
      mo_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      erp_mo_id: 'MO/001',
      flag_code: 'MISSING_BOM',
      message: 'No BOM',
    },
  ]),
  fetchSyncHistory: vi.fn().mockResolvedValue([
    {
      id: 'run-1',
      started_at: '2026-07-10T08:00:00Z',
      finished_at: '2026-07-10T08:01:00Z',
      duration_seconds: 60,
      status: 'success',
      entity_counts: { products: { updated: 2 } },
    },
  ]),
  testOdooConnection: vi.fn(),
  updateOdooConfig: vi.fn(),
  runSyncNow: vi.fn(),
}));

describe('OdooConfigPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders partner wizard and monitor tables', async () => {
    render(<OdooConfigPanel />);

    await waitFor(() => {
      expect(screen.getByText('admin.odoo.wizardTitle')).toBeInTheDocument();
    });

    expect(screen.getByText('admin.odoo.dqTitle')).toBeInTheDocument();
    expect(screen.getByText('MISSING_BOM')).toBeInTheDocument();
    expect(screen.getByText('admin.odoo.historyTitle')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
  });
});
