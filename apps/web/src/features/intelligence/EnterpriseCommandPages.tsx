import { useEffect, useState } from 'react';
import api from '@/lib/api';

type Json = Record<string, unknown>;

const severityClass: Record<string, string> = {
  warning: 'text-amber-700',
  info: 'text-sky-700',
  critical: 'text-red-700',
};

function ToolRunner({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle: string;
  actions: { label: string; path: string; body?: Json }[];
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  async function run(label: string, path: string, body: Json = {}) {
    setBusy(label);
    setResult(null);
    try {
      const res = await api.post(`/api/v1/enterprise/${path}`, body);
      setResult(JSON.stringify(res.data?.data ?? res.data, null, 2));
    } catch {
      setResult(`${label}: offline / unavailable`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <section>
        <h2 className="text-lg font-semibold text-ipe-text">{title}</h2>
        <p className="text-sm text-ipe-text-muted">{subtitle}</p>
      </section>
      <section className="flex flex-wrap gap-2">
        {actions.map((a) => (
          <button
            key={a.label}
            type="button"
            disabled={busy !== null}
            onClick={() => run(a.label, a.path, a.body ?? {})}
            className="rounded-md border border-ipe-border bg-white px-3 py-2 text-sm hover:bg-ipe-surface disabled:opacity-50"
          >
            {busy === a.label ? 'Running…' : a.label}
          </button>
        ))}
      </section>
      {result ? (
        <pre className="max-h-96 overflow-auto rounded-lg border border-ipe-border bg-ipe-surface p-3 text-xs">
          {result}
        </pre>
      ) : null}
    </div>
  );
}

interface Insight {
  insight_id: string;
  category: string;
  title: string;
  detail: string;
  confidence: number;
  suggested_action: string;
  severity: string;
}

export function AnalyticsCommandPage() {
  const [insights, setInsights] = useState<Insight[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.post('/api/v1/enterprise/analytics/insights', {});
        setInsights((res.data?.data?.insights as Insight[]) ?? []);
      } catch {
        setError('Analytics API unavailable — offline shell.');
        setInsights([]);
      }
    })();
  }, []);

  return (
    <div className="space-y-6">
      {error ? <p className="text-sm text-amber-700">{error}</p> : null}
      <section>
        <h2 className="text-lg font-semibold text-ipe-text">M7 · Analytics Command (A14)</h2>
        <p className="text-sm text-ipe-text-muted">
          Automated insight generation, trend detection, anomaly alerting, and predictive analytics — SAC-equivalent, zero analyst setup.
        </p>
      </section>

      <section className="space-y-2">
        {(insights ?? []).map((i) => (
          <div key={i.insight_id} className="rounded-lg border border-ipe-border bg-white p-4">
            <div className="flex items-center justify-between">
              <p className={`text-sm font-semibold ${severityClass[i.severity] ?? ''}`}>{i.title}</p>
              <span className="text-xs text-ipe-text-muted">
                {i.category} · {Math.round(i.confidence * 100)}%
              </span>
            </div>
            <p className="mt-1 text-sm text-ipe-text">{i.detail}</p>
            <p className="mt-1 text-xs text-ipe-text-muted">→ {i.suggested_action}</p>
          </div>
        ))}
      </section>

      <ToolRunner
        title="Run analytics tools"
        subtitle="Predictions, trend, and anomaly detection on live series."
        actions={[
          { label: 'Predictions', path: 'analytics/predictions' },
          { label: 'Trend (copper)', path: 'analytics/trend', body: { series: [175, 181, 186, 190, 193, 196], label: 'copper' } },
          { label: 'Anomaly (throughput)', path: 'analytics/anomaly', body: { series: [120, 122, 119, 121, 118, 90], label: 'throughput' } },
        ]}
      />
    </div>
  );
}

export function CommercialCommandPage() {
  return (
    <div className="space-y-8">
      <ToolRunner
        title="M8 · Commercial Command (A13)"
        subtitle="Dynamic pricing optimization, deal profitability, and contract compliance — SD-equivalent intelligence above Odoo/SAP."
        actions={[
          { label: 'Optimize price', path: 'commercial/pricing', body: { customer_tier: 'A', list_price: 85000, unit_cost: 59200, quantity: 10 } },
          { label: 'Deal profitability', path: 'commercial/deal-profitability' },
          { label: 'Contract compliance', path: 'commercial/contract-compliance' },
        ]}
      />
      <ToolRunner
        title="Cross-Functional Orchestrator (A17)"
        subtitle="The meta-agent: cross-functional ATP/CTP (A1·A3·A11·A13), enterprise policy gate, conflict resolution, and cascading events."
        actions={[
          { label: 'Orchestrated ATP/CTP', path: 'orchestrator/atp', body: { qty: 50, inventory_available: 12, capacity_available_hrs: 200 } },
          { label: 'Enforce policies', path: 'orchestrator/enforce-policies' },
          { label: 'Cascade demand change', path: 'orchestrator/cascade' },
        ]}
      />
    </div>
  );
}

export function ProcurementCommandPage() {
  return (
    <ToolRunner
      title="M9 · Procurement + Shop Floor Command (A15 · A16)"
      subtitle="3-way match, receipt confirmation, digital work instructions, time tracking, and live production progress. IoT = stub, Odoo write-back = PH1-02 (mock)."
      actions={[
        { label: '3-way match', path: 'procurement/three-way-match' },
        { label: 'Confirm receipt', path: 'procurement/receipt' },
        { label: 'Work instructions', path: 'shop-floor/work-instructions' },
        { label: 'Time tracking', path: 'shop-floor/time-track' },
        { label: 'Production progress', path: 'shop-floor/progress' },
      ]}
    />
  );
}
