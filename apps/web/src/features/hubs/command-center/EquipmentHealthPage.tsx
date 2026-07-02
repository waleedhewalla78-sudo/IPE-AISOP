import { useCallback, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';

interface EquipmentRow {
  id: string;
  name: string;
  health_score: number;
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('access_token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
    try {
      const payload = JSON.parse(atob(token.split('.')[1] ?? '')) as { tenant_id?: string };
      if (payload.tenant_id) headers['X-Tenant-ID'] = payload.tenant_id;
    } catch { /* ignore */ }
  }
  return headers;
}

function apiBase(): string {
  return import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
}

export function EquipmentHealthPage() {
  const [equipment, setEquipment] = useState<EquipmentRow[]>([]);
  const [alerts, setAlerts] = useState<{ machine_id: string; rul_hours: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [eqRes, schedRes] = await Promise.all([
        fetch(`${apiBase()}/api/v1/equipment`, { headers: authHeaders() }),
        fetch(`${apiBase()}/api/v1/maintenance/schedule`, { headers: authHeaders() }),
      ]);
      const eqBody = await eqRes.json() as { data?: { equipment?: EquipmentRow[] } };
      const schedBody = await schedRes.json() as { data?: { predictive_alerts?: { machine_id: string; rul_hours: number }[] } };
      setEquipment(eqBody.data?.equipment ?? []);
      setAlerts(schedBody.data?.predictive_alerts ?? []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-ipe-text">Equipment Health</h2>
        <p className="text-sm text-ipe-text-muted">Predictive maintenance telemetry and schedule</p>
      </div>
      {loading ? (
        <Card><p className="text-sm text-ipe-text-muted">Loading fleet…</p></Card>
      ) : (
        <>
          <Card>
            <h3 className="mb-2 font-medium">Fleet ({equipment.length})</h3>
            <ul className="space-y-1 text-sm">
              {equipment.slice(0, 12).map((e) => (
                <li key={e.id} className="flex justify-between">
                  <span>{e.name}</span>
                  <span className={e.health_score < 50 ? 'text-red-600 font-medium' : 'text-ipe-text-muted'}>
                    {e.health_score.toFixed(0)}% health
                  </span>
                </li>
              ))}
            </ul>
          </Card>
          {alerts.length > 0 && (
            <Card>
              <h3 className="mb-2 font-medium text-red-700">Predictive alerts (RUL &lt; 48h)</h3>
              <ul className="text-sm">
                {alerts.map((a) => (
                  <li key={a.machine_id}>{a.machine_id}: {a.rul_hours}h RUL</li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
