import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { ROUTES } from '@/lib/constants';

interface ModuleCard {
  module_id: string;
  name: string;
  route: string;
  kpis: Record<string, number | string>;
  agents: string[];
}

interface PulsePayload {
  pulse: {
    mos_on_track: number;
    mos_total: number;
    at_risk: number;
    otd_pct: number;
    margin_pct: number;
    auto_actions_overnight: number;
    brief: string;
  };
  modules: ModuleCard[];
  agent_activity: { agent_id: string; message: string }[];
}

const MODULE_ROUTE: Record<string, string> = {
  M1: ROUTES.INTELLIGENCE_DEMAND,
  M2: ROUTES.INTELLIGENCE_PRODUCTION,
  M3: ROUTES.INTELLIGENCE_SUPPLY,
  M4: ROUTES.INTELLIGENCE_QUALITY,
  M5: ROUTES.INTELLIGENCE_FINANCE,
  M6: ROUTES.INTELLIGENCE_CUSTOMER,
};

export function IntelligencePulsePage() {
  const [data, setData] = useState<PulsePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/v1/intelligence/pulse');
        setData(res.data?.data ?? null);
      } catch {
        setError('Pulse API unavailable — showing offline shell.');
        setData({
          pulse: {
            mos_on_track: 42,
            mos_total: 47,
            at_risk: 5,
            otd_pct: 89,
            margin_pct: 28,
            auto_actions_overnight: 3,
            brief: 'Offline pulse. Connect Kong/dpe-svc for live intelligence.',
          },
          modules: [],
          agent_activity: [],
        });
      }
    })();
  }, []);

  if (!data) {
    return <p className="text-sm text-ipe-text-muted">Loading intelligence pulse…</p>;
  }

  const p = data.pulse;

  return (
    <div className="space-y-6">
      {error ? <p className="text-sm text-amber-700">{error}</p> : null}

      <section className="rounded-lg border border-ipe-border bg-gradient-to-br from-slate-50 to-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ipe-text-muted">Today&apos;s Pulse</h2>
        <div className="mt-3 flex flex-wrap gap-6 text-sm">
          <span>
            {p.mos_on_track}/{p.mos_total} MOs on track
          </span>
          <span>OTD: {p.otd_pct}%</span>
          <span>Margin: {p.margin_pct}%</span>
          <span>{p.at_risk} at risk</span>
          <span>{p.auto_actions_overnight} auto-actions overnight</span>
        </div>
        <p className="mt-4 max-w-3xl text-base text-ipe-text">{p.brief}</p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(data.modules.length
          ? data.modules
          : [
              { module_id: 'M1', name: 'Demand Command', route: '', kpis: {}, agents: [] },
              { module_id: 'M2', name: 'Production Command', route: '', kpis: {}, agents: [] },
              { module_id: 'M3', name: 'Supply Command', route: '', kpis: {}, agents: [] },
              { module_id: 'M4', name: 'Quality Command', route: '', kpis: {}, agents: [] },
              { module_id: 'M5', name: 'Finance Command', route: '', kpis: {}, agents: [] },
              { module_id: 'M6', name: 'Customer Command', route: '', kpis: {}, agents: [] },
            ]
        ).map((m) => (
          <Link
            key={m.module_id}
            to={MODULE_ROUTE[m.module_id] || ROUTES.INTELLIGENCE_PULSE}
            className="block rounded-lg border border-ipe-border bg-white p-4 transition hover:border-ipe-primary"
          >
            <h3 className="font-semibold text-ipe-text">
              {m.module_id} {m.name.replace(' Command', '')}
            </h3>
            <ul className="mt-2 space-y-1 text-sm text-ipe-text-muted">
              {Object.entries(m.kpis || {})
                .slice(0, 3)
                .map(([k, v]) => (
                  <li key={k}>
                    {k}: {String(v)}
                  </li>
                ))}
            </ul>
            <span className="mt-3 inline-block text-sm text-ipe-primary">Open ▸</span>
          </Link>
        ))}
      </section>

      <section className="rounded-lg border border-ipe-border bg-white p-4">
        <h3 className="text-sm font-semibold">Agent Activity</h3>
        <ul className="mt-2 space-y-1 text-sm text-ipe-text-muted">
          {(data.agent_activity || []).map((a, i) => (
            <li key={`${a.agent_id}-${i}`}>
              {a.agent_id}: {a.message}
            </li>
          ))}
        </ul>
        <div className="mt-4 flex flex-wrap gap-3 text-sm">
          <Link className="text-ipe-primary" to={ROUTES.CUSTOMER_PORTAL}>
            Customer portal
          </Link>
          <Link className="text-ipe-primary" to={ROUTES.SHOP_FLOOR}>
            Digital factory (shop floor)
          </Link>
          <Link className="text-ipe-primary" to={ROUTES.PLATFORM_AGENTS}>
            All agents
          </Link>
        </div>
      </section>
    </div>
  );
}
