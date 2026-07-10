import { useCallback, useEffect, useState } from 'react';
import { t } from '@/lib/i18n';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  fetchOdooConfig,
  fetchSyncDqFlags,
  fetchSyncHistory,
  runSyncNow,
  testOdooConnection,
  updateOdooConfig,
} from '../api';
import type { DataQualityFlag, OdooConfig, SyncRun } from '../types';

const DQ_GUIDANCE: Record<string, string> = {
  MISSING_BOM: 'admin.odoo.dq.missingBom',
  MISSING_ROUTING: 'admin.odoo.dq.missingRouting',
  MISSING_WC: 'admin.odoo.dq.missingWc',
  SYNC_CONFLICT: 'admin.odoo.dq.syncConflict',
  MISSING_PRODUCT: 'admin.odoo.dq.missingProduct',
  INVALID_QUANTITY: 'admin.odoo.dq.invalidQuantity',
};

const WIZARD_STEPS = ['connection', 'schedule', 'monitor'] as const;
type WizardStep = (typeof WIZARD_STEPS)[number];

function statusBadge(status: string) {
  if (status === 'success') return 'success';
  if (status === 'partial') return 'warning';
  if (status === 'failed' || status === 'running') return 'danger';
  return 'default';
}

function formatEntityCounts(counts: Record<string, unknown> | undefined): string {
  if (!counts || typeof counts !== 'object') return '—';
  const parts = Object.entries(counts)
    .filter(([, v]) => v != null)
    .slice(0, 4)
    .map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : String(v)}`);
  return parts.length ? parts.join(' · ') : '—';
}

export function OdooConfigPanel() {
  const [wizardStep, setWizardStep] = useState<WizardStep>('connection');
  const [odooConfig, setOdooConfig] = useState<OdooConfig | null>(null);
  const [odooPassword, setOdooPassword] = useState('');
  const [syncIntervalMinutes, setSyncIntervalMinutes] = useState(900);
  const [odooTestMsg, setOdooTestMsg] = useState('');
  const [testingOdoo, setTestingOdoo] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState('');
  const [flags, setFlags] = useState<DataQualityFlag[]>([]);
  const [history, setHistory] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshMonitor = useCallback(async () => {
    const [dq, hist] = await Promise.all([fetchSyncDqFlags(), fetchSyncHistory(10)]);
    setFlags(dq);
    setHistory(hist);
  }, []);

  useEffect(() => {
    async function load() {
      const odoo = await fetchOdooConfig();
      setOdooConfig(odoo);
      setSyncIntervalMinutes(odoo.sync_interval_minutes ?? 900);
      await refreshMonitor();
      setLoading(false);
    }
    load();
  }, [refreshMonitor]);

  if (loading || !odooConfig) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  const stepIndex = WIZARD_STEPS.indexOf(wizardStep);

  return (
    <div className="space-y-6">
      <Card>
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <h3 className="font-medium text-ipe-text">{t('admin.odoo.wizardTitle')}</h3>
            <p className="text-sm text-ipe-text-muted">{t('admin.odoo.wizardSubtitle')}</p>
          </div>
          <div className="flex items-center gap-2">
            {WIZARD_STEPS.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setWizardStep(step)}
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                    i <= stepIndex ? 'bg-ipe-primary text-white' : 'bg-ipe-surface-alt text-ipe-text-muted'
                  }`}
                  aria-label={t(`admin.odoo.step.${step}`)}
                >
                  {i < stepIndex ? '✓' : i + 1}
                </button>
                {i < WIZARD_STEPS.length - 1 ? (
                  <div className={`h-0.5 w-8 ${i < stepIndex ? 'bg-ipe-primary' : 'bg-ipe-border'}`} />
                ) : null}
              </div>
            ))}
          </div>
        </div>

        <p className="mb-4 text-sm font-medium text-ipe-text">{t(`admin.odoo.step.${wizardStep}`)}</p>

        {wizardStep === 'connection' && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('admin.odoo.url')}</label>
              <input
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={odooConfig.odoo_url}
                onChange={(e) => setOdooConfig({ ...odooConfig, odoo_url: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('admin.odoo.db')}</label>
              <input
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={odooConfig.odoo_db}
                onChange={(e) => setOdooConfig({ ...odooConfig, odoo_db: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('admin.odoo.username')}</label>
              <input
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={odooConfig.odoo_username}
                onChange={(e) => setOdooConfig({ ...odooConfig, odoo_username: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('admin.odoo.password')}</label>
              <input
                type="password"
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                placeholder={odooConfig.password_set ? '••••••••' : ''}
                value={odooPassword}
                onChange={(e) => setOdooPassword(e.target.value)}
              />
              <p className="mt-1 text-xs text-ipe-text-muted">{t('admin.odoo.passwordHint')}</p>
            </div>
          </div>
        )}

        {wizardStep === 'schedule' && (
          <div className="max-w-md space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('admin.odoo.syncInterval')}</label>
              <input
                type="number"
                min={5}
                max={10080}
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={syncIntervalMinutes}
                onChange={(e) => setSyncIntervalMinutes(parseInt(e.target.value, 10) || 900)}
              />
              <p className="mt-1 text-xs text-ipe-text-muted">{t('admin.odoo.syncIntervalHint')}</p>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={odooConfig.enabled}
                onChange={(e) => setOdooConfig({ ...odooConfig, enabled: e.target.checked })}
              />
              {t('admin.odoo.enabled')}
            </label>
          </div>
        )}

        {wizardStep === 'monitor' && (
          <div className="space-y-3 text-sm text-ipe-text-muted">
            <p>{t('admin.odoo.monitorHint')}</p>
            <Button
              disabled={syncing}
              onClick={async () => {
                setSyncing(true);
                setSyncMsg(t('admin.odoo.syncing'));
                const result = await runSyncNow();
                setSyncMsg(result.ok ? t('admin.odoo.syncSuccess') : `${t('admin.odoo.syncFailed')}: ${result.message ?? ''}`);
                await refreshMonitor();
                setSyncing(false);
              }}
            >
              {syncing ? t('admin.odoo.syncing') : t('admin.odoo.syncNow')}
            </Button>
            {syncMsg ? <p className={syncMsg.includes(t('admin.odoo.syncSuccess')) ? 'text-green-600' : 'text-red-600'}>{syncMsg}</p> : null}
          </div>
        )}

        {odooTestMsg ? (
          <p
            className={`mt-3 text-sm ${
              odooTestMsg.includes(t('admin.odoo.connected')) ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {odooTestMsg}
          </p>
        ) : null}

        <div className="mt-6 flex justify-between gap-2">
          <Button variant="ghost" disabled={stepIndex === 0} onClick={() => setWizardStep(WIZARD_STEPS[stepIndex - 1])}>
            {t('admin.odoo.back')}
          </Button>
          <div className="flex gap-2">
            {wizardStep === 'connection' ? (
              <Button
                variant="ghost"
                disabled={testingOdoo}
                onClick={async () => {
                  setTestingOdoo(true);
                  setOdooTestMsg(t('admin.odoo.testing'));
                  const result = await testOdooConnection({
                    ...odooConfig,
                    odoo_password: odooPassword || undefined,
                  });
                  setOdooTestMsg(
                    result.connected
                      ? `${t('admin.odoo.connected')}${result.message ? ` (${result.message})` : ''}`
                      : `${t('admin.odoo.failed')}: ${result.message ?? ''}`,
                  );
                  setTestingOdoo(false);
                }}
              >
                {t('admin.odoo.test')}
              </Button>
            ) : null}
            {wizardStep === 'monitor' ? (
              <Button variant="ghost" onClick={() => refreshMonitor()}>
                {t('admin.odoo.refresh')}
              </Button>
            ) : null}
            {stepIndex < WIZARD_STEPS.length - 1 ? (
              <Button onClick={() => setWizardStep(WIZARD_STEPS[stepIndex + 1])}>{t('admin.odoo.next')}</Button>
            ) : (
              <Button
                disabled={saving}
                onClick={async () => {
                  setSaving(true);
                  const updated = await updateOdooConfig({
                    ...odooConfig,
                    odoo_password: odooPassword || undefined,
                    sync_interval_minutes: syncIntervalMinutes,
                  });
                  setOdooConfig(updated);
                  setOdooPassword('');
                  setSaving(false);
                }}
              >
                {t('admin.odoo.save')}
              </Button>
            )}
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-medium text-ipe-text">{t('admin.odoo.dqTitle')}</h3>
            <Badge variant={flags.length === 0 ? 'success' : flags.length <= 3 ? 'warning' : 'danger'}>
              {flags.length} {t('admin.odoo.dqOpen')}
            </Badge>
          </div>
          {flags.length === 0 ? (
            <p className="text-sm text-ipe-text-muted">{t('admin.odoo.dqEmpty')}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ipe-border text-xs text-ipe-text-muted">
                    <th className="py-2 pr-2">{t('admin.odoo.dqMo')}</th>
                    <th className="py-2 pr-2">{t('admin.odoo.dqFlag')}</th>
                    <th className="py-2">{t('admin.odoo.dqGuidance')}</th>
                  </tr>
                </thead>
                <tbody>
                  {flags.map((flag) => (
                    <tr key={`${flag.mo_id}-${flag.flag_code}`} className="border-b border-ipe-border/60">
                      <td className="py-2 pr-2 font-mono text-xs">{flag.erp_mo_id ?? flag.mo_id.slice(0, 8)}</td>
                      <td className="py-2 pr-2">
                        <Badge variant="warning">{flag.flag_code}</Badge>
                      </td>
                      <td className="py-2 text-xs text-ipe-text-muted">
                        {t(DQ_GUIDANCE[flag.flag_code] ?? 'admin.odoo.dq.generic')}
                        {flag.message ? ` — ${flag.message}` : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="mb-4 font-medium text-ipe-text">{t('admin.odoo.historyTitle')}</h3>
          {history.length === 0 ? (
            <p className="text-sm text-ipe-text-muted">{t('admin.odoo.historyEmpty')}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ipe-border text-xs text-ipe-text-muted">
                    <th className="py-2 pr-2">{t('admin.odoo.colStarted')}</th>
                    <th className="py-2 pr-2">{t('admin.odoo.colStatus')}</th>
                    <th className="py-2 pr-2">{t('admin.odoo.colDuration')}</th>
                    <th className="py-2">{t('admin.odoo.colCounts')}</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((run) => (
                    <tr key={run.id} className="border-b border-ipe-border/60">
                      <td className="py-2 pr-2 text-xs">
                        {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
                      </td>
                      <td className="py-2 pr-2">
                        <Badge variant={statusBadge(run.status)}>{run.status}</Badge>
                      </td>
                      <td className="py-2 pr-2 text-xs">
                        {run.duration_seconds != null ? `${run.duration_seconds}s` : '—'}
                      </td>
                      <td className="py-2 text-xs text-ipe-text-muted">{formatEntityCounts(run.entity_counts)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
