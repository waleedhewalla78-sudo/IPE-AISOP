import { useEffect, useState } from 'react';

type AuditRow = {
  query_id: string;
  created_at: string;
  user_id?: string;
  query_mode?: string;
  q?: string;
  r?: string;
  sources?: number;
};

/** Admin → Governance → Copilot Audit (BATCH1-3). History begins at migration 085. */
export function CopilotAuditPage() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    fetch('/api/v1/governance/copilot-audit')
      .then(async (res) => {
        if (res.status === 403) throw new Error('Admin role required');
        const body = await res.json();
        setRows(body?.data?.rows ?? []);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="p-6 space-y-4" data-testid="copilot-audit-page">
      <h1 className="text-xl font-semibold">Copilot audit trail</h1>
      <p className="text-sm text-muted-foreground">
        Audit history begins when migration 085 was applied. Prior Copilot activity was not audited.
      </p>
      {error ? <p className="text-red-600">{error}</p> : null}
      <table className="w-full text-sm border">
        <thead>
          <tr>
            <th className="text-left p-2">Time</th>
            <th className="text-left p-2">Mode</th>
            <th className="text-left p-2">Query</th>
            <th className="text-left p-2">Sources</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.query_id}
              className="border-t cursor-pointer hover:bg-muted/40"
              onClick={() => {
                fetch(`/api/v1/governance/copilot-audit/${row.query_id}`)
                  .then((r) => r.json())
                  .then((b) => setSelected(b.data ?? null));
              }}
            >
              <td className="p-2">{row.created_at}</td>
              <td className="p-2">{row.query_mode}</td>
              <td className="p-2">{row.q}</td>
              <td className="p-2">{row.sources}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {selected ? (
        <pre className="text-xs bg-muted p-3 overflow-auto max-h-80">{JSON.stringify(selected, null, 2)}</pre>
      ) : null}
      <a className="underline text-sm" href="/api/v1/governance/copilot-audit/export">
        Export CSV
      </a>
    </div>
  );
}
