import { useEffect, useState } from 'react';

interface TenantHealthRow {
  tenant_id: string;
  tenant_name: string;
  tier: string;
  erp_type: string;
  is_active: boolean;
  health_status: string;
  sync_status: string;
  last_sync_at: string | null;
  failed_sync_count_24h: number;
  mdr_passed: boolean | null;
  mdr_score_pct: number | null;
  active_mo_count: number;
  open_alert_count: number;
}

interface TenantAlert {
  alert_id: string;
  tenant_id: string;
  tenant_name: string;
  severity: string;
  category: string;
  message: string;
  occurred_at: string | null;
  source: string;
}

function statusColor(status: string): string {
  if (status === 'healthy') return 'text-green-600 bg-green-50';
  if (status === 'degraded') return 'text-yellow-700 bg-yellow-50';
  if (status === 'critical') return 'text-red-700 bg-red-50';
  return 'text-gray-600 bg-gray-50';
}

export function OpsDashboard() {
  const [tenants, setTenants] = useState<TenantHealthRow[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [alerts, setAlerts] = useState<TenantAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/v1/ops/tenants/health').then((r) => r.json()),
      fetch('/api/v1/ops/tenants/alerts?limit=20').then((r) => r.json()),
    ])
      .then(([healthRes, alertsRes]) => {
        setTenants(healthRes.data?.tenants || []);
        setSummary(healthRes.data?.summary || {});
        setAlerts(alertsRes.data?.alerts || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6">Loading ops dashboard...</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Multi-Tenant Operations</h1>
        <p className="text-gray-500">Platform health, sync status, and tenant alerts</p>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {(['total', 'healthy', 'degraded', 'critical', 'inactive'] as const).map((key) => (
          <div key={key} className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500 capitalize">{key}</div>
            <div className="text-3xl font-bold">{summary[key] ?? 0}</div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-4 py-3 border-b font-medium">Tenant Health</div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Tenant</th>
              <th className="px-4 py-2 text-left">Tier</th>
              <th className="px-4 py-2 text-left">Health</th>
              <th className="px-4 py-2 text-left">Sync</th>
              <th className="px-4 py-2 text-left">MDR</th>
              <th className="px-4 py-2 text-right">Active MOs</th>
              <th className="px-4 py-2 text-right">Alerts 24h</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((t) => (
              <tr key={t.tenant_id} className="border-t">
                <td className="px-4 py-2 font-medium">{t.tenant_name}</td>
                <td className="px-4 py-2">{t.tier}</td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-1 rounded text-xs ${statusColor(t.health_status)}`}>
                    {t.health_status}
                  </span>
                </td>
                <td className="px-4 py-2">{t.sync_status}</td>
                <td className="px-4 py-2">
                  {t.mdr_passed == null ? '—' : t.mdr_passed ? 'PASS' : 'FAIL'}
                </td>
                <td className="px-4 py-2 text-right">{t.active_mo_count}</td>
                <td className="px-4 py-2 text-right">{t.failed_sync_count_24h}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-4 py-3 border-b font-medium">Recent Alerts</div>
        <ul className="divide-y">
          {alerts.length === 0 && (
            <li className="px-4 py-3 text-gray-500">No active alerts</li>
          )}
          {alerts.map((a) => (
            <li key={a.alert_id} className="px-4 py-3 flex justify-between gap-4">
              <div>
                <span className={`text-xs font-medium uppercase ${a.severity === 'critical' ? 'text-red-600' : 'text-yellow-600'}`}>
                  {a.severity}
                </span>
                <span className="ml-2 font-medium">{a.tenant_name}</span>
                <p className="text-sm text-gray-600">{a.message}</p>
              </div>
              <span className="text-xs text-gray-400 whitespace-nowrap">{a.occurred_at || '—'}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
