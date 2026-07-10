import { useEffect, useState } from 'react';

interface SopReportSummary {
  report_id: string;
  report_name: string;
  horizon_weeks: number;
  status: string;
  summary: Record<string, unknown>;
  gap_analysis: Record<string, unknown>;
  recommendations: Array<Record<string, unknown>>;
  generated_at: string | null;
}

export function SOPReport() {
  const [reports, setReports] = useState<SopReportSummary[]>([]);
  const [selected, setSelected] = useState<SopReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadReports = () => {
    fetch('/api/v1/reports/sop')
      .then((r) => r.json())
      .then((res) => {
        const list = res.data?.reports || [];
        setReports(list);
        setSelected(list[0] || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadReports();
  }, []);

  const generateReport = () => {
    setGenerating(true);
    fetch('/api/v1/reports/sop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_name: 'S&OP Executive Summary', horizon_weeks: 12 }),
    })
      .then((r) => r.json())
      .then((res) => {
        if (res.data) {
          setSelected(res.data);
          loadReports();
        }
      })
      .finally(() => setGenerating(false));
  };

  const exportPdf = () => {
    if (!selected) return;
    const text = JSON.stringify(selected, null, 2);
    const blob = new Blob([text], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sop-report-${selected.report_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="p-6">Loading S&OP reports...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">S&OP Executive Report</h1>
          <p className="text-gray-500">Demand-capacity synthesis and recommendations</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={generateReport}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
          <button
            type="button"
            onClick={exportPdf}
            disabled={!selected}
            className="px-4 py-2 border rounded hover:bg-gray-50 disabled:opacity-50"
          >
            Export
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Horizon</div>
          <div className="text-2xl font-bold">{selected?.horizon_weeks ?? '—'} wks</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Forecast Buckets</div>
          <div className="text-2xl font-bold">{String(selected?.summary?.forecast_buckets ?? '—')}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Active MOs</div>
          <div className="text-2xl font-bold">{String(selected?.summary?.active_mo_count ?? '—')}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Bottlenecks</div>
          <div className="text-2xl font-bold text-red-600">{String(selected?.summary?.bottleneck_count ?? '—')}</div>
        </div>
      </div>

      {selected && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold mb-3">Recommendations</h2>
          <ul className="list-disc pl-5 space-y-2">
            {(selected.recommendations || []).map((rec, i) => (
              <li key={i} className="text-sm">
                <span className="font-medium uppercase text-xs text-gray-500">{String(rec.priority)}</span>
                {' — '}
                {String(rec.action)}
              </li>
            ))}
            {(!selected.recommendations || selected.recommendations.length === 0) && (
              <li className="text-gray-500">No recommendations — generate a fresh report</li>
            )}
          </ul>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-4 py-3 border-b font-medium">Report History</div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Name</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Generated</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((r) => (
              <tr
                key={r.report_id}
                className="border-t cursor-pointer hover:bg-gray-50"
                onClick={() => setSelected(r)}
              >
                <td className="px-4 py-2">{r.report_name}</td>
                <td className="px-4 py-2">{r.status}</td>
                <td className="px-4 py-2">{r.generated_at || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
