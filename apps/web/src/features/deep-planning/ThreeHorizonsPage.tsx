import { useEffect, useState } from 'react';
import api from '@/lib/api';

interface HorizonCard {
  horizon: string;
  label: string;
  window_months: string;
  granularity: string;
  coverage_pct: number;
  health_bar: string;
  status: string;
  pending_decisions: number;
  metrics: Record<string, unknown>;
}

interface HorizonsPayload {
  as_of: string;
  horizons: Record<string, HorizonCard>;
  overall_coverage_pct: number;
  attention: { horizon: string; coverage_pct: number; pending_decisions: number }[];
}

const statusClass: Record<string, string> = {
  healthy: 'text-emerald-700',
  attention: 'text-amber-700',
  critical: 'text-red-700',
};

const FALLBACK: HorizonsPayload = {
  as_of: '2026-07-16',
  overall_coverage_pct: 89.3,
  horizons: {
    strategic: { horizon: 'strategic', label: 'Strategic', window_months: '12-24', granularity: 'monthly/quarterly', coverage_pct: 85, health_bar: '██████████░░', status: 'attention', pending_decisions: 2, metrics: { revenue_target_usd: 28000000, growth_pct: 15 } },
    tactical: { horizon: 'tactical', label: 'Tactical', window_months: '1-6', granularity: 'weekly', coverage_pct: 94, health_bar: '████████████', status: 'healthy', pending_decisions: 0, metrics: { sop_cycle: 'Aug', consensus_pct: 94 } },
    operational: { horizon: 'operational', label: 'Operational', window_months: '0-1', granularity: 'daily/shift', coverage_pct: 89, health_bar: '█████████░░░', status: 'attention', pending_decisions: 1, metrics: { mos_active: 47, mos_at_risk: 5 } },
  },
  attention: [],
};

export function ThreeHorizonsPage() {
  const [data, setData] = useState<HorizonsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cascade, setCascade] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/v1/planning-command/horizons');
        setData(res.data?.data ?? FALLBACK);
      } catch {
        setError('Horizons API unavailable — offline shell.');
        setData(FALLBACK);
      }
    })();
  }, []);

  async function runCascade(direction: string) {
    setBusy(true);
    setCascade(null);
    try {
      const res = await api.post('/api/v1/planning-command/horizons/cascade', { direction });
      setCascade(JSON.stringify(res.data?.data ?? res.data, null, 2));
    } catch {
      setCascade('cascade: offline / unavailable');
    } finally {
      setBusy(false);
    }
  }

  if (!data) return <p className="text-sm text-ipe-text-muted">Loading planning horizons…</p>;

  const order = ['strategic', 'tactical', 'operational'];

  return (
    <div className="space-y-6">
      {error ? <p className="text-sm text-amber-700">{error}</p> : null}
      <section>
        <h2 className="text-lg font-semibold text-ipe-text">Planning Horizons — آفاق التخطيط</h2>
        <p className="text-sm text-ipe-text-muted">
          Three simultaneous horizons with cascade planning. Overall coverage {data.overall_coverage_pct}%.
        </p>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        {order.map((key) => {
          const h = data.horizons[key];
          if (!h) return null;
          return (
            <div key={key} className="rounded-lg border border-ipe-border bg-white p-4">
              <div className="flex items-baseline justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wide">{h.label}</h3>
                <span className="text-xs text-ipe-text-muted">{h.window_months} mo</span>
              </div>
              <p className="mt-1 text-xs text-ipe-text-muted">{h.granularity}</p>
              <p className="mt-3 font-mono text-sm">{h.health_bar}</p>
              <p className={`mt-1 text-sm font-semibold ${statusClass[h.status] ?? ''}`}>
                {h.coverage_pct}% coverage
                {h.pending_decisions > 0 ? ` · ${h.pending_decisions} pending` : ''}
              </p>
              <dl className="mt-3 space-y-1 text-xs text-ipe-text-muted">
                {Object.entries(h.metrics).slice(0, 4).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2">
                    <dt>{k}</dt>
                    <dd className="tabular-nums text-ipe-text">{String(v)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          );
        })}
      </div>

      <section className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => runCascade('down')}
          className="rounded-md border border-ipe-border bg-white px-3 py-2 text-sm hover:bg-ipe-surface disabled:opacity-50"
        >
          Cascade decision down ▾
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => runCascade('up')}
          className="rounded-md border border-ipe-border bg-white px-3 py-2 text-sm hover:bg-ipe-surface disabled:opacity-50"
        >
          Escalate constraint up ▴
        </button>
      </section>

      {cascade ? (
        <pre className="max-h-72 overflow-auto rounded-lg border border-ipe-border bg-ipe-surface p-3 text-xs">
          {cascade}
        </pre>
      ) : null}
    </div>
  );
}
