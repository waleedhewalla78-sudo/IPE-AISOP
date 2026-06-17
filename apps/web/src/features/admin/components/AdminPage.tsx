import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fetchConfig, fetchDataQuality, updateConfig } from '../api';
import type { ConfigData, DataQualityMetrics } from '../types';

type Tab = 'config' | 'data-quality';

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('config');
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [metrics, setMetrics] = useState<DataQualityMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([fetchConfig(), fetchDataQuality()]).then(([cfg, m]) => {
      setConfig(cfg);
      setMetrics(m);
      setLoading(false);
    });
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
        <h1 className="text-2xl font-bold text-ipe-text">Admin Console</h1>
        <p className="text-sm text-ipe-text-muted">Tenant configuration and data quality monitoring</p>
      </div>

      <div className="flex gap-1 border-b border-ipe-border">
        <button className={tabClass('config')} onClick={() => setActiveTab('config')}>Configuration</button>
        <button className={tabClass('data-quality')} onClick={() => setActiveTab('data-quality')}>Data Quality</button>
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
    </div>
  );
}
