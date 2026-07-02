import { useCallback, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

type OtdBaseline = {
  baseline: { otd_pct?: number; captured_at?: string } | null;
  current_30d: { otd_pct?: number; completed_mos?: number; on_time_mos?: number };
  delta_vs_baseline: number | null;
};

type RoiMetrics = {
  mos_saved_count?: number;
  avg_feasibility?: number;
  weeks?: Array<{ week_start: string; completed_mos: number; at_risk_count: number }>;
};

type SyncStatus = {
  last_sync?: { status: string; started_at: string; entity_counts?: Record<string, unknown> };
};

export function OutcomesPage() {
  const [otd, setOtd] = useState<OtdBaseline | null>(null);
  const [roi, setRoi] = useState<RoiMetrics | null>(null);
  const [sync, setSync] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [otdRes, roiRes, syncRes] = await Promise.all([
        api.get('/api/v1/analytics/otd-baseline'),
        api.get('/api/v1/analytics/roi-metrics'),
        api.get('/api/v1/sync/status'),
      ]);
      setOtd(otdRes.data?.data ?? null);
      setRoi(roiRes.data?.data ?? null);
      setSync(syncRes.data?.data ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load outcomes');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const captureBaseline = async () => {
    setCapturing(true);
    try {
      await api.post('/api/v1/analytics/otd-baseline/capture', {
        lookback_days: 30,
        source: 'outcomes_dashboard',
      });
      await load();
    } finally {
      setCapturing(false);
    }
  };

  const copySummary = () => {
    const lines = [
      'IPE Customer Outcomes Summary',
      `OTD (30d): ${otd?.current_30d?.otd_pct ?? '—'}%`,
      `Baseline: ${otd?.baseline?.otd_pct ?? 'not captured'}%`,
      `Delta: ${otd?.delta_vs_baseline ?? '—'}%`,
      `MOs saved: ${roi?.mos_saved_count ?? '—'}`,
      `Last sync: ${sync?.last_sync?.status ?? '—'} @ ${sync?.last_sync?.started_at ?? '—'}`,
    ];
    void navigator.clipboard.writeText(lines.join('\n'));
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
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ipe-text">
            {t('outcomes.title', 'Customer Outcomes')}
          </h1>
          <p className="text-sm text-ipe-text-muted">
            {t('outcomes.subtitle', 'OTD proof, ROI metrics, and sync health for QBR')}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={captureBaseline}
            disabled={capturing}
            className="rounded-md bg-ipe-primary px-4 py-2 text-sm font-medium text-white hover:bg-ipe-primary/90 disabled:opacity-50"
          >
            {capturing
              ? t('outcomes.capturing', 'Capturing…')
              : t('outcomes.captureBaseline', 'Capture OTD baseline')}
          </button>
          <button
            type="button"
            onClick={copySummary}
            className="rounded-md border border-ipe-border px-4 py-2 text-sm font-medium text-ipe-text hover:bg-ipe-surface-alt"
          >
            {t('outcomes.copySummary', 'Copy QBR summary')}
          </button>
        </div>
      </div>

      {error ? (
        <Card className="border-red-200 bg-red-50 p-4 text-red-800">{error}</Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <p className="text-sm text-ipe-text-muted">{t('outcomes.otd30d', 'OTD (30 days)')}</p>
          <p className="mt-1 text-3xl font-bold text-ipe-text">
            {otd?.current_30d?.otd_pct != null ? `${otd.current_30d.otd_pct}%` : '—'}
          </p>
          <p className="mt-1 text-xs text-ipe-text-muted">
            {otd?.current_30d?.on_time_mos ?? 0} / {otd?.current_30d?.completed_mos ?? 0} on time
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-ipe-text-muted">{t('outcomes.vsBaseline', 'vs baseline')}</p>
          <p className="mt-1 text-3xl font-bold text-ipe-text">
            {otd?.delta_vs_baseline != null
              ? `${otd.delta_vs_baseline > 0 ? '+' : ''}${otd.delta_vs_baseline}%`
              : '—'}
          </p>
          <p className="mt-1 text-xs text-ipe-text-muted">
            {otd?.baseline?.otd_pct != null
              ? `Baseline ${otd.baseline.otd_pct}%`
              : t('outcomes.noBaseline', 'No baseline — capture above')}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-ipe-text-muted">{t('outcomes.mosSaved', 'MOs saved')}</p>
          <p className="mt-1 text-3xl font-bold text-ipe-text">{roi?.mos_saved_count ?? '—'}</p>
          <p className="mt-1 text-xs text-ipe-text-muted">
            {t('outcomes.avgFeasibility', 'Avg feasibility')}: {roi?.avg_feasibility ?? '—'}
          </p>
        </Card>
      </div>

      <Card className="p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ipe-text">{t('outcomes.syncHealth', 'Odoo sync health')}</h2>
          <Badge variant={sync?.last_sync?.status === 'success' ? 'success' : 'warning'}>
            {sync?.last_sync?.status ?? 'unknown'}
          </Badge>
        </div>
        <p className="mt-2 text-sm text-ipe-text-muted">
          {sync?.last_sync?.started_at
            ? `Last sync: ${new Date(sync.last_sync.started_at).toLocaleString()}`
            : 'No sync recorded'}
        </p>
      </Card>
    </div>
  );
}
