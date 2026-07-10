import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import api from '@/lib/api';

vi.mock('recharts', () => {
  const Passthrough = ({ children }: { children?: ReactNode }) => children ?? null;
  return {
    ResponsiveContainer: Passthrough,
    ComposedChart: Passthrough,
    CartesianGrid: Passthrough,
    XAxis: Passthrough,
    YAxis: Passthrough,
    Tooltip: Passthrough,
    Legend: Passthrough,
    Area: Passthrough,
    Line: Passthrough,
  };
});

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.stubGlobal('fetch', vi.fn());

function mockFetch(data: unknown) {
  vi.mocked(fetch).mockResolvedValue({
    ok: true,
    json: async () => ({ success: true, data }),
  } as Response);
}

describe('DemandForecastPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'header.payload.sig');
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes('/demand/forecast')) {
        return Promise.resolve({ data: { data: { forecasts: [] } } });
      }
      if (url.includes('/demand/accuracy')) {
        return Promise.resolve({ data: { data: { mape_pct: null } } });
      }
      return Promise.resolve({ data: { data: {} } });
    });
    vi.mocked(api.post).mockResolvedValue({ data: { success: true } });
  });

  it('renders demand forecast heading', async () => {
    const { DemandForecastPage } = await import('@/features/hubs/planning/DemandForecastPage');
    render(<DemandForecastPage />);
    expect(screen.getByText(/Demand Sensing/i)).toBeInTheDocument();
  });
});

describe('ScenarioWorkbenchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'header.payload.sig');
    vi.mocked(api.get).mockResolvedValue({ data: { data: { scenarios: [] } } });
    vi.mocked(api.post).mockResolvedValue({ data: { success: true } });
  });

  it('renders scenario workbench heading', async () => {
    const { ScenarioWorkbenchPage } = await import('@/features/hubs/planning/ScenarioWorkbenchPage');
    render(<ScenarioWorkbenchPage />);
    expect(screen.getByText(/Scenario Workbench/i)).toBeInTheDocument();
  });
});

describe('SupplyPlanningPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'header.payload.sig');
    mockFetch({ facilities: [], lanes: [] });
  });

  it('renders supply planning heading', async () => {
    const { SupplyPlanningPage } = await import('@/features/hubs/supply-chain/SupplyPlanningPage');
    render(<SupplyPlanningPage />);
    expect(screen.getByText(/Supply Planning/i)).toBeInTheDocument();
  });
});

describe('OrderManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'header.payload.sig');
    mockFetch({ orders: [] });
  });

  it('renders order management heading', async () => {
    const { OrderManagementPage } = await import('@/features/hubs/supply-chain/OrderManagementPage');
    render(<OrderManagementPage />);
    expect(screen.getByText(/Order Management/i)).toBeInTheDocument();
  });
});

describe('EquipmentHealthPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'header.payload.sig');
    mockFetch({ equipment: [{ id: '1', name: 'WC1', health_score: 90 }] });
  });

  it('renders equipment health heading', async () => {
    const { EquipmentHealthPage } = await import('@/features/hubs/command-center/EquipmentHealthPage');
    render(<EquipmentHealthPage />);
    expect(screen.getByText(/Equipment Health/i)).toBeInTheDocument();
  });
});

describe('DesignAIPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'header.payload.sig');
    mockFetch({ materials: [], count: 0 });
  });

  it('renders design AI heading', async () => {
    const { DesignAIPage } = await import('@/features/hubs/ai-governance/DesignAIPage');
    render(<DesignAIPage />);
    expect(screen.getByText(/Product Design AI/i)).toBeInTheDocument();
  });
});

describe('ProcurementDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'header.payload.sig');
    vi.mocked(fetch)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ success: true, data: { suppliers: [] } }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ success: true, data: { summary: { total: 0, by_category: {} } } }) } as Response);
  });

  it('renders procurement heading', async () => {
    const { ProcurementDashboardPage } = await import('@/features/hubs/supply-chain/ProcurementDashboardPage');
    render(<ProcurementDashboardPage />);
    expect(screen.getByText(/Responsible Procurement/i)).toBeInTheDocument();
  });
});
