import { useCallback, useEffect, useState } from 'react';
import { t } from '@/lib/i18n';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  fetchOdooConfigEntities,
  fetchOdooConfigVersions,
  rollbackOdooConfig,
  saveOdooConfig,
  testOdooConfigConnection,
} from '../api';
import type { OdooConfigEntity } from '../types';

const EMPTY_ENTITY: OdooConfigEntity = {
  entity_key: 'primary',
  version: 0,
  is_current: true,
  name: '',
  odoo_url: '',
  odoo_db: '',
  odoo_username: '',
  enabled: true,
  sync_interval_minutes: 900,
  password_set: false,
  field_mappings: {},
};

export function OdooConfigPage() {
  const [entities, setEntities] = useState<OdooConfigEntity[]>([]);
  const [selectedKey, setSelectedKey] = useState('primary');
  const [form, setForm] = useState<OdooConfigEntity>(EMPTY_ENTITY);
  const [password, setPassword] = useState('');
  const [versions, setVersions] = useState<OdooConfigEntity[]>([]);
  const [newEntityKey, setNewEntityKey] = useState('');
  const [testMsg, setTestMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const loadEntity = useCallback(async (key: string) => {
    const list = await fetchOdooConfigEntities();
    setEntities(list.entities);
    const current = list.entities.find((e) => e.entity_key === key) ?? {
      ...EMPTY_ENTITY,
      entity_key: key,
    };
    setForm(current);
    setPassword('');
    const hist = await fetchOdooConfigVersions(key);
    setVersions(hist);
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadEntity(selectedKey);
      setLoading(false);
    })();
  }, [selectedKey, loadEntity]);

  const handleTest = async () => {
    setBusy(true);
    setTestMsg(t('odooConfig.testing'));
    try {
      const result = await testOdooConfigConnection({
        ...form,
        odoo_password: password || undefined,
        entity_key: form.entity_key,
      });
      if (result.connected) {
        const latency = result.latency_ms != null ? ` (${result.latency_ms}ms)` : '';
        const ver = result.server_version ? ` v${result.server_version}` : '';
        setTestMsg(`${t('odooConfig.connected')}${ver}${latency}`);
      } else {
        setTestMsg(t('odooConfig.failed'));
      }
    } catch {
      setTestMsg(t('odooConfig.failed'));
    }
    setBusy(false);
  };

  const handleSave = async () => {
    setBusy(true);
    try {
      const saved = await saveOdooConfig({
        ...form,
        odoo_password: password || undefined,
        expected_version: form.version > 0 ? form.version : undefined,
        change_summary: t('odooConfig.savedViaUi'),
      });
      setForm(saved);
      setPassword('');
      await loadEntity(saved.entity_key);
      setTestMsg(t('odooConfig.saveSuccess'));
    } catch {
      setTestMsg(t('odooConfig.saveFailed'));
    }
    setBusy(false);
  };

  const handleRollback = async (version: number) => {
    setBusy(true);
    try {
      const rolled = await rollbackOdooConfig(form.entity_key, version);
      setForm(rolled);
      await loadEntity(rolled.entity_key);
      setTestMsg(`${t('odooConfig.rollbackSuccess')} v${version}`);
    } catch {
      setTestMsg(t('odooConfig.rollbackFailed'));
    }
    setBusy(false);
  };

  const handleAddEntity = () => {
    const key = newEntityKey.trim();
    if (!key) return;
    setSelectedKey(key);
    setForm({ ...EMPTY_ENTITY, entity_key: key });
    setNewEntityKey('');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">{t('odooConfig.title')}</h1>
        <p className="text-sm text-ipe-text-muted">{t('odooConfig.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">
                {t('odooConfig.entity')}
              </label>
              <select
                className="rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={selectedKey}
                onChange={(e) => setSelectedKey(e.target.value)}
              >
                {entities.map((e) => (
                  <option key={e.entity_key} value={e.entity_key}>
                    {e.name || e.entity_key}
                  </option>
                ))}
                {!entities.some((e) => e.entity_key === selectedKey) ? (
                  <option value={selectedKey}>{selectedKey}</option>
                ) : null}
              </select>
            </div>
            <div className="flex gap-2">
              <input
                className="rounded border border-ipe-border px-3 py-1.5 text-sm"
                placeholder={t('odooConfig.newEntityPlaceholder')}
                value={newEntityKey}
                onChange={(e) => setNewEntityKey(e.target.value)}
              />
              <Button variant="ghost" onClick={handleAddEntity} disabled={!newEntityKey.trim()}>
                {t('odooConfig.addEntity')}
              </Button>
            </div>
            {form.version > 0 ? (
              <Badge variant="success">
                {t('odooConfig.versionBadge')} {form.version}
              </Badge>
            ) : null}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('odooConfig.name')}</label>
              <input
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('odooConfig.syncInterval')}</label>
              <input
                type="number"
                min={1}
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={form.sync_interval_minutes}
                onChange={(e) =>
                  setForm({ ...form, sync_interval_minutes: parseInt(e.target.value, 10) || 900 })
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('odooConfig.url')}</label>
              <input
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={form.odoo_url}
                onChange={(e) => setForm({ ...form, odoo_url: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('odooConfig.db')}</label>
              <input
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={form.odoo_db}
                onChange={(e) => setForm({ ...form, odoo_db: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('odooConfig.username')}</label>
              <input
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                value={form.odoo_username}
                onChange={(e) => setForm({ ...form, odoo_username: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ipe-text-muted">{t('odooConfig.password')}</label>
              <input
                type="password"
                className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm"
                placeholder={form.password_set ? '••••••••' : ''}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="mt-1 text-xs text-ipe-text-muted">{t('odooConfig.passwordHint')}</p>
            </div>
          </div>

          <label className="mt-4 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            {t('odooConfig.enabled')}
          </label>

          {testMsg ? (
            <p
              className={`mt-3 text-sm ${
                testMsg.includes(t('odooConfig.connected')) || testMsg.includes(t('odooConfig.saveSuccess'))
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}
            >
              {testMsg}
            </p>
          ) : null}

          <div className="mt-4 flex justify-end gap-2">
            <Button variant="ghost" disabled={busy} onClick={handleTest}>
              {t('odooConfig.test')}
            </Button>
            <Button disabled={busy} onClick={handleSave}>
              {t('odooConfig.save')}
            </Button>
          </div>
        </Card>

        <Card>
          <h3 className="mb-3 font-medium">{t('odooConfig.versionHistory')}</h3>
          {versions.length === 0 ? (
            <p className="text-sm text-ipe-text-muted">{t('odooConfig.noVersions')}</p>
          ) : (
            <ul className="space-y-2">
              {versions.map((v) => (
                <li
                  key={`${v.entity_key}-${v.version}`}
                  className="flex items-center justify-between rounded border border-ipe-border px-3 py-2 text-sm"
                >
                  <div>
                    <span className="font-medium">v{v.version}</span>
                    {v.is_current ? (
                      <Badge variant="success" className="ml-2">
                        {t('odooConfig.current')}
                      </Badge>
                    ) : null}
                    {v.change_summary ? (
                      <p className="text-xs text-ipe-text-muted">{v.change_summary}</p>
                    ) : null}
                  </div>
                  {!v.is_current ? (
                    <Button variant="ghost" disabled={busy} onClick={() => handleRollback(v.version)}>
                      {t('odooConfig.rollback')}
                    </Button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
