import { useCallback, useEffect, useState } from 'react';
import { t } from '@/lib/i18n';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  activateErpConnection,
  createErpConnection,
  deleteErpConnection,
  fetchErpConnectionLogs,
  listErpConnections,
  syncErpConnectionNow,
  testErpConnection,
  updateErpConnection,
  type ErpConnection,
  type ErpConnectionLog,
  type ErpTestResult,
} from '../erpConnectionsApi';

const SYNC_OPTIONS = [
  { label: '5 min', value: 300 },
  { label: '15 min', value: 900 },
  { label: '30 min', value: 1800 },
  { label: '60 min', value: 3600 },
];

const EMPTY_FORM = {
  display_name: '',
  host_url: '',
  database_name: '',
  username: '',
  password: '',
  is_production: false,
  sync_interval_seconds: 900,
};

function StatusDot({ result }: { result: string | null }) {
  const color =
    result === 'success' ? 'bg-green-500' : result == null ? 'bg-gray-400' : 'bg-red-500';
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} title={result ?? 'never tested'} />;
}

export function OdooConnectionsPage() {
  const [rows, setRows] = useState<ErpConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [busy, setBusy] = useState(false);
  const [testMsg, setTestMsg] = useState<string | null>(null);
  const [testOk, setTestOk] = useState<boolean | null>(null);
  const [logsFor, setLogsFor] = useState<string | null>(null);
  const [logs, setLogs] = useState<ErpConnectionLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRows(await listErpConnections());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load connections');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setTestMsg(null);
    setTestOk(null);
    setShowForm(true);
  };

  const openEdit = (row: ErpConnection) => {
    setEditingId(row.id);
    setForm({
      display_name: row.display_name,
      host_url: row.host_url,
      database_name: row.database_name,
      username: row.username,
      password: '',
      is_production: row.is_production,
      sync_interval_seconds: row.sync_interval_seconds,
    });
    setTestMsg(null);
    setTestOk(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    setBusy(true);
    setError(null);
    try {
      if (editingId) {
        const payload: Record<string, unknown> = {
          display_name: form.display_name,
          host_url: form.host_url,
          database_name: form.database_name,
          username: form.username,
          is_production: form.is_production,
          sync_interval_seconds: form.sync_interval_seconds,
        };
        if (form.password) payload.password = form.password;
        await updateErpConnection(editingId, payload);
      } else {
        if (!form.password) {
          setError('Password is required for new connections');
          setBusy(false);
          return;
        }
        await createErpConnection({
          display_name: form.display_name,
          host_url: form.host_url,
          database_name: form.database_name,
          username: form.username,
          password: form.password,
          is_production: form.is_production,
          sync_interval_seconds: form.sync_interval_seconds,
        });
      }
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setBusy(false);
    }
  };

  const handleTestSaved = async (id: string) => {
    setBusy(true);
    try {
      const result: ErpTestResult = await testErpConnection(id);
      setTestOk(result.result === 'success');
      setTestMsg(`${result.message}${result.odoo_version ? ` (v${result.odoo_version})` : ''}`);
      await load();
    } catch (err) {
      setTestOk(false);
      setTestMsg(err instanceof Error ? err.message : t('admin.odoo.connectionFailed'));
    } finally {
      setBusy(false);
    }
  };

  const handleActivate = async (id: string) => {
    setBusy(true);
    try {
      await activateErpConnection(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Activate failed');
    } finally {
      setBusy(false);
    }
  };

  const handleDeactivate = async (id: string) => {
    setBusy(true);
    try {
      await deleteErpConnection(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deactivate failed');
    } finally {
      setBusy(false);
    }
  };

  const handleSyncNow = async (id: string) => {
    setBusy(true);
    try {
      const result = await syncErpConnectionNow(id);
      setTestMsg(`Sync started: ${result.sync_run_id}`);
      setTestOk(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
    } finally {
      setBusy(false);
    }
  };

  const handleViewLogs = async (id: string) => {
    setLogsFor(id);
    setLogs(await fetchErpConnectionLogs(id));
  };

  const active = rows.find((r) => r.is_active);
  const nextSync =
    active && active.last_test_at
      ? new Date(new Date(active.last_test_at).getTime() + active.sync_interval_seconds * 1000).toLocaleString()
      : '—';

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ipe-text">{t('admin.odoo.title')}</h1>
          <p className="text-sm text-ipe-muted">Self-service Odoo connection management</p>
        </div>
        <Button onClick={openCreate} disabled={busy}>
          {t('admin.odoo.add')}
        </Button>
      </div>

      {error && <div className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      {testMsg && (
        <div
          className={`rounded border px-3 py-2 text-sm ${
            testOk ? 'border-green-300 bg-green-50 text-green-800' : 'border-red-300 bg-red-50 text-red-700'
          }`}
        >
          {testOk ? '✓ ' : '✗ '}
          {testMsg}
        </div>
      )}

      <Card className="p-4">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ipe-muted">Sync status</h2>
        <div className="grid gap-3 sm:grid-cols-3 text-sm">
          <div>
            <div className="text-ipe-muted">{t('admin.odoo.lastSync')}</div>
            <div>{active?.last_test_at ? new Date(active.last_test_at).toLocaleString() : '—'}</div>
          </div>
          <div>
            <div className="text-ipe-muted">{t('admin.odoo.nextSync')}</div>
            <div>{nextSync}</div>
          </div>
          <div>
            <div className="text-ipe-muted">Active</div>
            <div>{active?.display_name ?? 'None'}</div>
          </div>
        </div>
      </Card>

      <Card className="overflow-x-auto p-0">
        <table className="min-w-full text-sm">
          <thead className="bg-ipe-surface border-b border-ipe-border text-left">
            <tr>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">{t('admin.odoo.url')}</th>
              <th className="px-4 py-3">{t('admin.odoo.database')}</th>
              <th className="px-4 py-3">{t('admin.odoo.environment')}</th>
              <th className="px-4 py-3">Active</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ipe-muted">
                  No connections yet. Add one to get started.
                </td>
              </tr>
            )}
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-ipe-border">
                <td className="px-4 py-3">
                  <StatusDot result={row.last_test_result} />
                </td>
                <td className="px-4 py-3 font-medium">{row.display_name}</td>
                <td className="px-4 py-3 font-mono text-xs">{row.host_url}</td>
                <td className="px-4 py-3">{row.database_name}</td>
                <td className="px-4 py-3">
                  <Badge variant={row.is_production ? 'success' : 'default'}>
                    {row.is_production ? t('admin.odoo.production') : t('admin.odoo.staging')}
                  </Badge>
                </td>
                <td className="px-4 py-3">{row.is_active ? 'Yes' : 'No'}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    <Button size="sm" variant="ghost" disabled={busy} onClick={() => void handleTestSaved(row.id)}>
                      {t('admin.odoo.test')}
                    </Button>
                    <Button size="sm" variant="ghost" disabled={busy} onClick={() => openEdit(row)}>
                      Edit
                    </Button>
                    {!row.is_active ? (
                      <Button size="sm" variant="ghost" disabled={busy} onClick={() => void handleActivate(row.id)}>
                        {t('admin.odoo.activate')}
                      </Button>
                    ) : (
                      <Button size="sm" variant="ghost" disabled={busy} onClick={() => void handleDeactivate(row.id)}>
                        {t('admin.odoo.deactivate')}
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" disabled={busy || !row.is_active} onClick={() => void handleSyncNow(row.id)}>
                      {t('admin.odoo.syncNow')}
                    </Button>
                    <Button size="sm" variant="ghost" disabled={busy} onClick={() => void handleViewLogs(row.id)}>
                      {t('admin.odoo.logs')}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {showForm && (
        <Card className="space-y-4 p-4">
          <h2 className="text-lg font-semibold">{editingId ? 'Edit connection' : t('admin.odoo.add')}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm">
              Display name
              <input
                className="mt-1 w-full rounded border border-ipe-border px-3 py-2"
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              />
            </label>
            <label className="text-sm">
              {t('admin.odoo.url')}
              <input
                className="mt-1 w-full rounded border border-ipe-border px-3 py-2"
                value={form.host_url}
                onChange={(e) => setForm({ ...form, host_url: e.target.value })}
                placeholder="http://odoo.example:8069"
              />
            </label>
            <label className="text-sm">
              {t('admin.odoo.database')}
              <input
                className="mt-1 w-full rounded border border-ipe-border px-3 py-2"
                value={form.database_name}
                onChange={(e) => setForm({ ...form, database_name: e.target.value })}
              />
            </label>
            <label className="text-sm">
              {t('admin.odoo.username')}
              <input
                className="mt-1 w-full rounded border border-ipe-border px-3 py-2"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
              />
            </label>
            <label className="text-sm">
              {t('admin.odoo.password')}
              <input
                type="password"
                className="mt-1 w-full rounded border border-ipe-border px-3 py-2"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder={editingId ? '•••••••• (leave blank to keep)' : ''}
              />
            </label>
            <label className="text-sm">
              {t('admin.odoo.syncInterval')}
              <select
                className="mt-1 w-full rounded border border-ipe-border px-3 py-2"
                value={form.sync_interval_seconds}
                onChange={(e) => setForm({ ...form, sync_interval_seconds: Number(e.target.value) })}
              >
                {SYNC_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm sm:col-span-2">
              <input
                type="checkbox"
                checked={form.is_production}
                onChange={(e) => setForm({ ...form, is_production: e.target.checked })}
              />
              {t('admin.odoo.environment')}: {form.is_production ? t('admin.odoo.production') : t('admin.odoo.staging')}
            </label>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => void handleSave()} disabled={busy}>
              {t('admin.odoo.save')}
            </Button>
            <Button variant="ghost" onClick={() => setShowForm(false)} disabled={busy}>
              Cancel
            </Button>
          </div>
        </Card>
      )}

      {logsFor && (
        <Card className="space-y-3 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">{t('admin.odoo.logs')}</h2>
            <Button variant="ghost" size="sm" onClick={() => setLogsFor(null)}>
              Close
            </Button>
          </div>
          {logs.length === 0 ? (
            <p className="text-sm text-ipe-muted">No log entries.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {logs.map((log) => (
                <li key={log.id} className="rounded border border-ipe-border px-3 py-2">
                  <div className="flex justify-between gap-2">
                    <span className="font-medium">
                      {log.action} · {log.result ?? '—'}
                    </span>
                    <span className="text-ipe-muted">
                      {log.performed_at ? new Date(log.performed_at).toLocaleString() : ''}
                    </span>
                  </div>
                  {log.details && (
                    <pre className="mt-1 overflow-x-auto text-xs text-ipe-muted">
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  );
}
