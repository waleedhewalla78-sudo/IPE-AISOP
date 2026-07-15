import { useEffect, useState } from 'react';
import api from '@/lib/api';

interface PlanHealth {
  plan_coverage_pct: number;
  demand_supply_balance_pct: number;
  horizon_coverage_pct: number;
  plan_stability_pct: number;
  schedule_frozen_weeks: number;
}

interface AttentionItem {
  severity: string;
  code: string;
  message: string;
  action: string;
}

interface CockpitPayload {
  plan_health: PlanHealth;
  attention: AttentionItem[];
  timeline: { week: string; coverage_pct: number; mos: number; at_risk: number; materials: string; capacity: string }[];
  actions: string[];
}

const severityClass: Record<string, string> = {
  red: 'text-red-700',
  amber: 'text-amber-700',
  blue: 'text-sky-700',
};

export function PlanningCockpitPage() {
  const [data, setData] = useState<CockpitPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toolResult, setToolResult] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/v1/planning-command/cockpit');
        setData(res.data?.data ?? null);
      } catch {
        setError('Cockpit API unavailable — offline shell.');
        setData({
          plan_health: {
            plan_coverage_pct: 94,
            demand_supply_balance_pct: 97,
            horizon_coverage_pct: 78,
            plan_stability_pct: 91,
            schedule_frozen_weeks: 2,
          },
          attention: [
            { severity: 'red', code: 'MOS_AT_RISK', message: '5 MOs at risk (next 7 days)', action: 'resolve' },
            { severity: 'blue', code: 'MRP_NEEDED', message: 'MRP run needed (new orders)', action: 'run_mrp' },
          ],
          timeline: [],
          actions: ['run_mrp', 'update_mps', 'check_atp'],
        });
      }
    })();
  }, []);

  async function runTool(name: string, path: string, body: Record<string, unknown> = {}) {
    setBusy(name);
    setToolResult(null);
    try {
      const res = await api.post(`/api/v1/planning-command/${path}`, body);
      setToolResult(`${name}: ${JSON.stringify(res.data?.data ?? res.data, null, 2)}`);
    } catch {
      setToolResult(`${name}: offline / unavailable`);
    } finally {
      setBusy(null);
    }
  }

  if (!data) {
    return <p className="text-sm text-ipe-text-muted">Loading planning cockpit…</p>;
  }

  const h = data.plan_health;

  return (
    <div className="space-y-6">
      {error ? <p className="text-sm text-amber-700">{error}</p> : null}
      <section>
        <h2 className="text-lg font-semibold text-ipe-text">Planning Cockpit</h2>
        <p className="text-sm text-ipe-text-muted">Plan health, attention queue, and weekly horizon.</p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[
          ['Plan coverage', `${h.plan_coverage_pct}%`],
          ['Demand-supply', `${h.demand_supply_balance_pct}%`],
          ['Horizon', `${h.horizon_coverage_pct}%`],
          ['Stability', `${h.plan_stability_pct}%`],
          ['Frozen weeks', String(h.schedule_frozen_weeks)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-ipe-border bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-ipe-text-muted">{label}</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
          </div>
        ))}
      </div>

      <section className="rounded-lg border border-ipe-border bg-white p-4">
        <h3 className="text-sm font-semibold">Attention required</h3>
        <ul className="mt-3 space-y-2">
          {data.attention.map((a) => (
            <li key={a.code} className={`text-sm ${severityClass[a.severity] ?? ''}`}>
              {a.message} <span className="text-ipe-text-muted">→ {a.action}</span>
            </li>
          ))}
        </ul>
      </section>

      {data.timeline.length > 0 ? (
        <section className="overflow-x-auto rounded-lg border border-ipe-border bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-ipe-border bg-ipe-surface text-ipe-text-muted">
              <tr>
                <th className="px-3 py-2">Week</th>
                <th className="px-3 py-2">Coverage</th>
                <th className="px-3 py-2">MOs</th>
                <th className="px-3 py-2">At risk</th>
                <th className="px-3 py-2">Materials</th>
                <th className="px-3 py-2">Capacity</th>
              </tr>
            </thead>
            <tbody>
              {data.timeline.map((w) => (
                <tr key={w.week} className="border-b border-ipe-border/60">
                  <td className="px-3 py-2 font-medium">{w.week}</td>
                  <td className="px-3 py-2">{w.coverage_pct}%</td>
                  <td className="px-3 py-2">{w.mos}</td>
                  <td className="px-3 py-2">{w.at_risk}</td>
                  <td className="px-3 py-2">{w.materials}</td>
                  <td className="px-3 py-2">{w.capacity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <section className="flex flex-wrap gap-2">
        {[
          ['Update MPS', 'mps', {}],
          ['Run MRP', 'mrp/explode', { mo_qty: 20 }],
          ['Check ATP/CTP', 'promise', { qty: 5 }],
          ['RCCP', 'capacity/rccp', {}],
          ['Level production', 'level', {}],
          ['Scenario +20%', 'scenarios/cascade', { demand_uplift_pct: 20 }],
        ].map(([label, path, body]) => (
          <button
            key={String(label)}
            type="button"
            disabled={busy !== null}
            onClick={() => runTool(String(label), String(path), body as Record<string, unknown>)}
            className="rounded-md border border-ipe-border bg-white px-3 py-2 text-sm hover:bg-ipe-surface disabled:opacity-50"
          >
            {busy === label ? 'Running…' : String(label)}
          </button>
        ))}
      </section>

      {toolResult ? (
        <pre className="max-h-64 overflow-auto rounded-lg border border-ipe-border bg-ipe-surface p-3 text-xs">
          {toolResult}
        </pre>
      ) : null}
    </div>
  );
}
