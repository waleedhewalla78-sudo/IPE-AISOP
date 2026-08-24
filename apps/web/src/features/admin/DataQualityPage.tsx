import { useState } from 'react';

/** Admin data quality dashboard (BATCH1-4). Does not auto-fix rows. */
export function DataQualityPage() {
  const [score, setScore] = useState<number | null>(null);
  const [msg, setMsg] = useState('Audit history of DQ runs is tenant-scoped. Click Run to compute.');

  async function run() {
    setMsg('Running…');
    const res = await fetch('/api/v1/data-quality/run', { method: 'POST' });
    if (res.status === 403) {
      setMsg('Admin role required');
      return;
    }
    const body = await res.json();
    setScore(body?.data?.score ?? null);
    setMsg(`Report ${body?.data?.report_id ?? ''} checks=${body?.data?.checks ?? 0}`);
  }

  return (
    <div className="p-6 space-y-4" data-testid="data-quality-page">
      <h1 className="text-xl font-semibold">Data quality</h1>
      <p className="text-4xl font-bold">{score === null ? '—' : score}</p>
      <button type="button" className="px-3 py-2 border rounded" onClick={() => void run()}>
        Run DQ checks
      </button>
      <p className="text-sm text-muted-foreground">{msg}</p>
    </div>
  );
}
