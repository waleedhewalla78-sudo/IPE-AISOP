import { useEffect, useState } from 'react';
import api from '@/lib/api';

interface OpsPayload {
  right_now: {
    shift: string;
    supervisor: string;
    mos_in_production: number;
    on_schedule: number;
    behind: number;
    work_centres: { id: string; utilisation_pct: number; mo: string | null; product: string | null }[];
  };
  scorecard: {
    output_planned: number;
    output_done: number;
    oee_pct: number;
    quality_pct: number;
    on_time_starts: string;
    scrap_pct: number;
    safety_incidents: number;
  };
  live_alerts: { time: string; severity: string; message: string }[];
}

export function OpsLivePage() {
  const [data, setData] = useState<OpsPayload | null>(null);
  const [warRoom, setWarRoom] = useState<Record<string, unknown> | null>(null);
  const [performance, setPerformance] = useState<Record<string, unknown> | null>(null);
  const [predictive, setPredictive] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [dash, perf, pred] = await Promise.all([
          api.get('/api/v1/planning-command/ops/dashboard'),
          api.get('/api/v1/planning-command/ops/performance'),
          api.get('/api/v1/planning-command/ops/predictive'),
        ]);
        setData(dash.data?.data ?? null);
        setPerformance(perf.data?.data ?? null);
        setPredictive(pred.data?.data ?? null);
      } catch {
        setError('Ops API unavailable — offline shell.');
        setData({
          right_now: {
            shift: 'B',
            supervisor: 'Mohamed',
            mos_in_production: 4,
            on_schedule: 3,
            behind: 1,
            work_centres: [
              { id: 'WC-WND', utilisation_pct: 94, mo: 'MO-ST-003', product: 'PT500' },
              { id: 'WC-ASM', utilisation_pct: 42, mo: 'MO-ST-008', product: 'DT250' },
            ],
          },
          scorecard: {
            output_planned: 6,
            output_done: 4,
            oee_pct: 78,
            quality_pct: 99.2,
            on_time_starts: '5/6',
            scrap_pct: 0.8,
            safety_incidents: 0,
          },
          live_alerts: [{ time: '15:23', severity: 'amber', message: 'MO-ST-003 started 15 min late' }],
        });
      }
    })();
  }, []);

  async function activateWarRoom() {
    try {
      const res = await api.post('/api/v1/planning-command/ops/war-room', {});
      setWarRoom(res.data?.data ?? null);
    } catch {
      setWarRoom({
        mode: 'war_room',
        title: 'Demo War Room (offline)',
        recommended_option: 2,
        status: 'active',
      });
    }
  }

  if (!data) {
    return <p className="text-sm text-ipe-text-muted">Loading operations live…</p>;
  }

  const rn = data.right_now;
  const sc = data.scorecard;

  return (
    <div className="space-y-6">
      {error ? <p className="text-sm text-amber-700">{error}</p> : null}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ipe-text">Operations Live</h2>
          <p className="text-sm text-ipe-text-muted">
            Shift {rn.shift} · Supervisor {rn.supervisor} · {rn.mos_in_production} MOs in production
          </p>
        </div>
        <button
          type="button"
          onClick={activateWarRoom}
          className="rounded-md bg-red-700 px-3 py-2 text-sm font-medium text-white hover:bg-red-800"
        >
          Activate War Room
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ['Output', `${sc.output_done}/${sc.output_planned}`],
          ['OEE', `${sc.oee_pct}%`],
          ['Quality', `${sc.quality_pct}%`],
          ['On-time starts', sc.on_time_starts],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-ipe-border bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-ipe-text-muted">{label}</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
          </div>
        ))}
      </div>

      <section className="rounded-lg border border-ipe-border bg-white p-4">
        <h3 className="text-sm font-semibold">Work centres</h3>
        <ul className="mt-3 space-y-2 text-sm">
          {rn.work_centres.map((wc) => (
            <li key={wc.id} className="flex justify-between gap-4">
              <span>
                {wc.id} {wc.mo ? `· ${wc.mo} (${wc.product})` : '· idle'}
              </span>
              <span className="tabular-nums text-ipe-text-muted">{wc.utilisation_pct}%</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-lg border border-ipe-border bg-white p-4">
        <h3 className="text-sm font-semibold">Live alerts</h3>
        <ul className="mt-3 space-y-2 text-sm">
          {data.live_alerts.map((a) => (
            <li key={`${a.time}-${a.message}`}>
              <span className="text-ipe-text-muted">{a.time}</span> · {a.message}
            </li>
          ))}
        </ul>
      </section>

      {performance ? (
        <section className="rounded-lg border border-ipe-border bg-white p-4 text-sm">
          <h3 className="font-semibold">Performance cockpit</h3>
          <p className="mt-1 text-ipe-text-muted">
            Factory OEE {String((performance as { factory_oee_pct?: number }).factory_oee_pct ?? '—')}%
            {' · '}
            OTD{' '}
            {String(
              (performance as { kpis?: { otd_pct?: number } }).kpis?.otd_pct ?? '—',
            )}
            %
          </p>
        </section>
      ) : null}

      {predictive ? (
        <section className="rounded-lg border border-ipe-border bg-white p-4 text-sm">
          <h3 className="font-semibold">Predictive command (3/7/14d)</h3>
          <p className="mt-1 text-ipe-text-muted">
            {(predictive as { summary?: { total_signals?: number; critical?: number } }).summary?.total_signals ?? 0}{' '}
            signals · {(predictive as { summary?: { critical?: number } }).summary?.critical ?? 0} critical
          </p>
        </section>
      ) : null}

      {warRoom ? (
        <section className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm">
          <h3 className="font-semibold text-red-900">War Room active</h3>
          <pre className="mt-2 overflow-x-auto text-xs text-red-900/90">{JSON.stringify(warRoom, null, 2)}</pre>
        </section>
      ) : null}
    </div>
  );
}
