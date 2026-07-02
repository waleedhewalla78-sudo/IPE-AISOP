import { useEffect, useState } from 'react';
import { t } from '@/lib/i18n';
import { IS_RELEASE1 } from '@/lib/releaseProfile';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fetchConfig, fetchDataQuality, fetchLlmStatus, fetchOdooConfig, testOdooConnection, updateConfig, updateOdooConfig, type LlmTierStatus } from '../api';
import type { ConfigData, DataQualityMetrics, OdooConfig } from '../types';

type Tab = 'config' | 'data-quality' | 'llm' | 'odoo';

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('config');
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [metrics, setMetrics] = useState<DataQualityMetrics | null>(null);
  const [llmStatus, setLlmStatus] = useState<LlmTierStatus | null>(null);
  const [odooConfig, setOdooConfig] = useState<OdooConfig | null>(null);
  const [odooPassword, setOdooPassword] = useState('');
  const [odooTestMsg, setOdooTestMsg] = useState('');
  const [testingOdoo, setTestingOdoo] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      const [cfg, m, llm] = await Promise.all([
        fetchConfig(),
        fetchDataQuality(),
        fetchLlmStatus(),
      ]);
      setConfig(cfg);
      setMetrics(m);
      setLlmStatus(llm);
      if (IS_RELEASE1) {
        const odoo = await fetchOdooConfig();
        setOdooConfig(odoo);
      }
      setLoading(false);
    }
    load();
  }, []);

  const handleSaveConfig = async () => {
    if (!config) return;
    setSaving(true);
    const updated = await updateConfig({
      priority_weights: config.priority_weights,
      strategic_product_ids: config.strategic_product_ids,
      feasibility_thresholds: config.feasibility_thresholds,
      autonomy_mode: config.autonomy_mode,
    });
    setConfig(updated);
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  const tabClass = (tab: Tab) =>
    `px-4 py-2 text-sm font-medium rounded-t-md transition-colors ${
      activeTab === tab
        ? 'bg-white border border-b-0 border-ipe-border text-ipe-text'
        : 'bg-ipe-surface-alt text-ipe-text-muted hover:text-ipe-text cursor-pointer'
    }`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">{t('admin.title')}</h1>
        <p className="text-sm text-ipe-text-muted">{t('admin.subtitle')}</p>
      </div>

      <div className="flex gap-1 border-b border-ipe-border">
        <button className={tabClass('config')} onClick={() => setActiveTab('config')}>{t('admin.tab.config')}</button>
        <button className={tabClass('data-quality')} onClick={() => setActiveTab('data-quality')}>{t('admin.tab.dataQuality')}</button>
        <button className={tabClass('llm')} onClick={() => setActiveTab('llm')}>{t('admin.tab.llm')}</button>
        {IS_RELEASE1 ? (
          <button className={tabClass('odoo')} onClick={() => setActiveTab('odoo')}>{t('admin.tab.odoo')}</button>
        ) : null}
      </div>

      {activeTab === 'config' && config && (
        <div className="space-y-6">
          <Card>
            <h3 className="mb-4 font-medium">Priority Weights</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(config.priority_weights).map(([key, val]) => (
                <div key={key}>
                  <label className="mb-1 block text-xs font-medium text-ipe-text-muted capitalize">{key.replace(/_/g, ' ')}</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={val}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        priority_weights: { ...config.priority_weights, [key]: parseFloat(e.target.value) || 0 },
                      })
                    }
                    className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ipe-primary"
                  />
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h3 className="mb-4 font-medium">Feasibility Thresholds</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-ipe-text-muted">Auto-Confirm Threshold</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={config.feasibility_thresholds.auto_confirm}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      feasibility_thresholds: { ...config.feasibility_thresholds, auto_confirm: parseFloat(e.target.value) || 0 },
                    })
                  }
                  className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ipe-primary"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-ipe-text-muted">Planner Threshold</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={config.feasibility_thresholds.planner}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      feasibility_thresholds: { ...config.feasibility_thresholds, planner: parseFloat(e.target.value) || 0 },
                    })
                  }
                  className="w-full rounded border border-ipe-border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ipe-primary"
                />
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="mb-4 font-medium">Autonomy Mode</h3>
            <div className="flex gap-3">
              {(['shadow', 'suggest', 'autonomous'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setConfig({ ...config, autonomy_mode: mode })}
                  className={`rounded-md border px-4 py-2 text-sm font-medium capitalize transition-colors ${
                    config.autonomy_mode === mode
                      ? 'border-ipe-primary bg-ipe-primary text-white'
                      : 'border-ipe-border text-ipe-text-muted hover:border-ipe-text'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </Card>

          <div className="flex justify-end">
            <Button onClick={handleSaveConfig} disabled={saving}>
              {saving ? 'Saving...' : 'Save Configuration'}
            </Button>
          </div>
        </div>
      )}

      {activeTab === 'data-quality' && metrics && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <h3 className="mb-2 text-sm font-medium text-ipe-text-muted">BOM Completeness</h3>
            <p className="text-3xl font-bold text-ipe-text">{metrics.bom_completeness_pct}%</p>
            <Badge variant={metrics.bom_completeness_pct >= 80 ? 'success' : metrics.bom_completeness_pct >= 60 ? 'warning' : 'danger'} className="mt-2">
              {metrics.bom_completeness_pct >= 80 ? 'Good' : metrics.bom_completeness_pct >= 60 ? 'Needs Review' : 'Critical'}
            </Badge>
          </Card>
          <Card>
            <h3 className="mb-2 text-sm font-medium text-ipe-text-muted">Lead Time Accuracy</h3>
            <p className="text-3xl font-bold text-ipe-text">{metrics.lead_time_accuracy_pct}%</p>
            <Badge variant={metrics.lead_time_accuracy_pct >= 80 ? 'success' : metrics.lead_time_accuracy_pct >= 60 ? 'warning' : 'danger'} className="mt-2">
              {metrics.lead_time_accuracy_pct >= 80 ? 'Good' : metrics.lead_time_accuracy_pct >= 60 ? 'Needs Review' : 'Critical'}
            </Badge>
          </Card>
          <Card>
            <h3 className="mb-2 text-sm font-medium text-ipe-text-muted">Inventory Record Accuracy</h3>
            <p className="text-3xl font-bold text-ipe-text">{metrics.inventory_record_accuracy_pct}%</p>
            <Badge variant={metrics.inventory_record_accuracy_pct >= 80 ? 'success' : metrics.inventory_record_accuracy_pct >= 60 ? 'warning' : 'danger'} className="mt-2">
              {metrics.inventory_record_accuracy_pct >= 80 ? 'Good' : metrics.inventory_record_accuracy_pct >= 60 ? 'Needs Review' : 'Critical'}
            </Badge>
          </Card>
        </div>
      )}

      {activeTab === 'llm' && llmStatus && (
        <div className="space-y-4">
          <Card>
            <h3 className="mb-3 font-medium">Active Provider</h3>
            <p className="text-lg font-semibold text-ipe-text">
              {llmStatus.active_provider ?? 'None available'}
            </p>
            <p className="mt-1 text-sm text-ipe-text-muted">
              Routing {llmStatus.routing_enabled ? 'enabled' : 'disabled (structured fallback allowed)'}
            </p>
          </Card>
          <Card>
            <h3 className="mb-3 font-medium">Provider Health</h3>
            <div className="space-y-2">
              {Object.entries(llmStatus.providers).map(([name, info]) => (
                <div key={name} className="flex items-center justify-between rounded border border-ipe-border px-3 py-2 text-sm">
                  <span className="capitalize">{name.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-ipe-text-muted">{info.detail}</span>
                    <Badge variant={info.available ? 'success' : 'danger'}>
                      {info.available ? 'Available' : 'Unavailable'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'odoo' && odooConfig && (
        <Card>
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
          <label className="mt-4 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={odooConfig.enabled}
              onChange={(e) => setOdooConfig({ ...odooConfig, enabled: e.target.checked })}
            />
            {t('admin.odoo.enabled')}
          </label>
          {odooTestMsg ? (
            <p className={`mt-3 text-sm ${odooTestMsg.includes('Connected') || odooTestMsg.includes('متصل') ? 'text-green-600' : 'text-red-600'}`}>
              {odooTestMsg}
            </p>
          ) : null}
          <div className="mt-4 flex justify-end gap-2">
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
            <Button
              disabled={saving}
              onClick={async () => {
                setSaving(true);
                const updated = await updateOdooConfig({
                  ...odooConfig,
                  odoo_password: odooPassword || undefined,
                });
                setOdooConfig(updated);
                setOdooPassword('');
                setSaving(false);
              }}
            >
              {t('admin.odoo.save')}
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
