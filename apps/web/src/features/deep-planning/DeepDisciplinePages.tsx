import { useState } from 'react';
import api from '@/lib/api';

type ToolMethod = 'GET' | 'POST';

interface Tool {
  label: string;
  method: ToolMethod;
  path: string;
  body?: Record<string, unknown>;
  note?: string;
}

interface WorkbenchProps {
  title: string;
  subtitle: string;
  tools: Tool[];
}

function DeepWorkbench({ title, subtitle, tools }: WorkbenchProps) {
  const [result, setResult] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [active, setActive] = useState<string | null>(null);

  async function run(tool: Tool) {
    setBusy(tool.label);
    setResult(null);
    setActive(tool.label);
    try {
      const url = `/api/v1/planning-command/${tool.path}`;
      const res =
        tool.method === 'GET' ? await api.get(url) : await api.post(url, tool.body ?? {});
      setResult(JSON.stringify(res.data?.data ?? res.data, null, 2));
    } catch {
      setResult(`${tool.label}: offline / unavailable`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-lg font-semibold text-ipe-text">{title}</h2>
        <p className="text-sm text-ipe-text-muted">{subtitle}</p>
      </section>

      <section className="flex flex-wrap gap-2">
        {tools.map((tool) => (
          <button
            key={tool.label}
            type="button"
            disabled={busy !== null}
            onClick={() => run(tool)}
            title={tool.note}
            className={`rounded-md border px-3 py-2 text-sm disabled:opacity-50 ${
              active === tool.label
                ? 'border-ipe-primary bg-ipe-surface'
                : 'border-ipe-border bg-white hover:bg-ipe-surface'
            }`}
          >
            {busy === tool.label ? 'Running…' : tool.label}
          </button>
        ))}
      </section>

      {result ? (
        <pre className="max-h-[28rem] overflow-auto rounded-lg border border-ipe-border bg-ipe-surface p-3 text-xs">
          {result}
        </pre>
      ) : (
        <p className="text-sm text-ipe-text-muted">Select an analysis above to run it.</p>
      )}
    </div>
  );
}

export function SopDeepPage() {
  return (
    <DeepWorkbench
      title="S&OP Deep — Financial, Rolling, Shaping, Portfolio"
      subtitle="Every S&OP decision is simultaneously a volume and a financial decision."
      tools={[
        { label: 'Financial S&OP (P&L per consensus)', method: 'POST', path: 'sop/financial' },
        { label: 'Rolling S&OP (event-driven)', method: 'POST', path: 'sop/rolling' },
        { label: 'Demand shaping options', method: 'POST', path: 'sop/demand-shaping' },
        { label: 'Portfolio mix optimization', method: 'POST', path: 'sop/portfolio' },
      ]}
    />
  );
}

export function DemandDeepPage() {
  return (
    <DeepWorkbench
      title="Demand Deep — Decomposition, Collaboration, NPI"
      subtitle="Demand decomposed into 5 components, each independently managed."
      tools={[
        { label: 'Decompose demand', method: 'POST', path: 'demand/decompose', body: { month: 10, base: 20, trend_per_month: 2 } },
        { label: 'Decompose (with promo)', method: 'POST', path: 'demand/decompose', body: { month: 10, promo_active: true, promo_price_change_pct: -5 } },
        { label: 'Collaboration consensus', method: 'POST', path: 'demand/collaborate' },
        { label: 'NPI forecast', method: 'POST', path: 'demand/npi', body: { months: 12 } },
      ]}
    />
  );
}

export function ProductionDeepPage() {
  return (
    <DeepWorkbench
      title="Production Deep — Scheduling, Labour, Make-or-Buy"
      subtitle="Sequence-dependent setup, multi-resource, campaign, skills SPOF, dynamic make-or-buy."
      tools={[
        { label: 'Setup-sequence optimize', method: 'POST', path: 'production/setup-sequence' },
        { label: 'Multi-resource schedule', method: 'POST', path: 'production/multi-resource' },
        { label: 'Campaign plan', method: 'POST', path: 'production/campaign' },
        { label: 'Labour + SPOF flags', method: 'POST', path: 'production/labour' },
        { label: 'Make-or-buy (at bottleneck)', method: 'POST', path: 'production/make-or-buy', body: { current_utilisation_pct: 95 } },
      ]}
    />
  );
}

export function OperationsDeepPage() {
  return (
    <DeepWorkbench
      title="Operations Deep — OEE, Gemba, Andon, KPI Tree, Standard Work"
      subtitle="Digital Gemba + Andon; IoT/machine telemetry is a stub (PH1-02 OPEN)."
      tools={[
        { label: 'OEE improvement programme', method: 'POST', path: 'operations/oee-programme' },
        { label: 'Digital Gemba (stub live)', method: 'GET', path: 'operations/gemba', note: 'iot_live=false — PH1-02 OPEN' },
        { label: 'Andon board', method: 'GET', path: 'operations/andon' },
        { label: 'Trigger Andon (yellow)', method: 'POST', path: 'operations/andon', body: { color: 'yellow', work_centre: 'WC-WND', reported_by: 'Mohamed', message: 'Wire tensioner needs adjustment' } },
        { label: 'KPI tree drill-down', method: 'GET', path: 'operations/kpi-tree' },
        { label: 'Standard work (A16)', method: 'POST', path: 'operations/standard-work' },
        { label: 'Planning calendar', method: 'GET', path: 'calendar' },
      ]}
    />
  );
}
