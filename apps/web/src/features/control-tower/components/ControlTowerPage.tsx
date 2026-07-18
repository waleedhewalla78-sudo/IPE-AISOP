import { useEffect, useState, useCallback, useMemo, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { ControlTowerSkeleton } from '@/components/ui/Skeleton';
import { FeatureErrorBoundary } from '@/components/ui/FeatureErrorBoundary';
import { TariffShockPanel } from '@/features/tariff/components/TariffShockPanel';
import { SyncStatusBar } from './SyncStatusBar';
import { PlannerAssistPanel } from './PlannerAssistPanel';
import { ForecastOverlayWidget } from './ForecastOverlayWidget';
import { HeroMetrics } from './HeroMetrics';
import { InlineResolutionPanel } from './InlineResolutionPanel';
import { ROUTES } from '@/lib/constants';
import { IS_RELEASE1 } from '@/lib/releaseProfile';
import { t } from '@/lib/i18n';
import {
  scoreTextClass,
  scoreBadgeClass,
  scoreRowBg,
  scoreTier,
  scoreTierLabelKey,
  constraintIcon,
} from '@/lib/scoreVisuals';
import { fetchQueue, fetchKPIs, getMockBottlenecks } from '../api';
import { FeasibilityWebSocket } from '@/lib/ws';
import api from '@/lib/api';
import type { MOQueueItem, KPI, BottleneckItem } from '../types';

const wsClient = new FeasibilityWebSocket();

function bottleneckColor(pct: number): string {
  if (pct > 95) return 'bg-score-critical';
  if (pct > 85) return 'bg-score-warning';
  if (pct > 70) return 'bg-score-good';
  return 'bg-score-excellent';
}

function relativeSyncLabel(iso: string | undefined): { label: string; healthy: boolean } {
  if (!iso) return { label: '—', healthy: false };
  const ms = Date.now() - new Date(iso).getTime();
  const mins = Math.max(0, Math.round(ms / 60_000));
  const healthy = mins <= 30;
  if (mins < 1) return { label: t('controlTower.syncJustNow'), healthy: true };
  return { label: t('controlTower.syncMinutesAgo', undefined, { mins }), healthy };
}

export function ControlTowerPage() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState<MOQueueItem[]>([]);
  const [kpis, setKPIs] = useState<KPI | null>(null);
  const [bottlenecks, setBottlenecks] = useState<BottleneckItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedMoId, setExpandedMoId] = useState<string | null>(null);
  const [syncMeta, setSyncMeta] = useState<{ label: string; healthy: boolean }>({
    label: '—',
    healthy: false,
  });

  const handleWsMessage = useCallback((data: unknown) => {
    const item = data as Partial<MOQueueItem>;
    if (!item.mo_id) return;
    setQueue((prev) => {
      const idx = prev.findIndex((q) => q.mo_id === item.mo_id);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { ...next[idx], ...item } as MOQueueItem;
        return next;
      }
      return [item as MOQueueItem, ...prev];
    });
  }, []);

  const reload = useCallback(() => {
    return Promise.all([fetchQueue(), fetchKPIs(), getMockBottlenecks()]).then(([q, k, b]) => {
      setQueue(q);
      setKPIs(k);
      setBottlenecks(b);
    });
  }, []);

  useEffect(() => {
    reload().finally(() => setLoading(false));

    api
      .get<{ success: boolean; data: { last_sync?: { finished_at?: string } | null } }>('/api/v1/sync/status')
      .then((res) => setSyncMeta(relativeSyncLabel(res.data.data?.last_sync?.finished_at)))
      .catch(() => setSyncMeta({ label: '—', healthy: false }));

    wsClient.onMessage(handleWsMessage);
    wsClient.connect();

    return () => {
      wsClient.disconnect();
    };
  }, [handleWsMessage, reload]);

  const worstMo = useMemo(() => {
    const scored = queue.filter((q) => q.feasibility_score != null);
    if (scored.length === 0) return null;
    return scored.reduce((a, b) =>
      (a.feasibility_score ?? 100) <= (b.feasibility_score ?? 100) ? a : b,
    );
  }, [queue]);

  if (loading) {
    return <ControlTowerSkeleton />;
  }

  const avgScore = kpis?.avg_feasibility_score ?? null;
  const activeBottlenecks = kpis?.active_bottlenecks ?? null;
  const ordersAtRisk = kpis?.orders_at_risk ?? null;
  const otdPct = kpis?.otd_pct ?? null;

  const toggleExpand = (moId: string) => {
    setExpandedMoId((prev) => (prev === moId ? null : moId));
  };

  return (
    <div className="control-tower space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">{t('controlTower.title')}</h1>
        <p className="text-sm text-ipe-text-muted">{t('controlTower.subtitle')}</p>
      </div>

      <HeroMetrics
        ordersAtRisk={ordersAtRisk}
        activeMoCount={queue.length}
        otdPct={otdPct}
        avgScore={avgScore}
        activeBottlenecks={activeBottlenecks}
        syncLabel={syncMeta.label}
        syncHealthy={syncMeta.healthy}
        worstMo={worstMo}
      />

      {IS_RELEASE1 ? <SyncStatusBar /> : null}

      <FeatureErrorBoundary fallbackTitle={t('controlTower.assistError')}>
        <PlannerAssistPanel />
      </FeatureErrorBoundary>

      <ForecastOverlayWidget />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {queue.length === 0 ? (
            <EmptyState
              title={t('controlTower.emptyTitle')}
              description={t('controlTower.emptyHint')}
              action={
                <Button size="sm" variant="secondary" onClick={() => navigate(ROUTES.PLATFORM_ODOO_CONFIG)}>
                  {t('controlTower.openOdooSettings')}
                </Button>
              }
            />
          ) : (
            <Card>
              <div className="mb-3 flex items-center justify-between gap-2">
                <h3 className="font-medium">
                  {t('controlTower.moQueue')} ({queue.length})
                </h3>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    const base = import.meta.env.VITE_API_BASE_URL ?? '';
                    window.open(`${base}/api/v1/phase8/export/risk-queue.csv`, '_blank');
                  }}
                >
                  {t('controlTower.exportRiskQueue')}
                </Button>
              </div>

              {/* Desktop table */}
              <div className="control-tower-table hidden overflow-x-auto md:block">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeader>{t('resolution.moId')}</TableHeader>
                      <TableHeader>{t('controlTower.product')}</TableHeader>
                      <TableHeader>{t('controlTower.customer')}</TableHeader>
                      <TableHeader>{t('controlTower.required')}</TableHeader>
                      <TableHeader>
                        {t('controlTower.feasibility')}{' '}
                        <span className="text-xs font-normal text-ipe-text-muted" title={t('controlTower.scorePendingNote')}>
                          *
                        </span>
                      </TableHeader>
                      <TableHeader>{t('controlTower.constraint')}</TableHeader>
                      <TableHeader />
                    </TableRow>
                  </TableHead>
                  <tfoot>
                    <TableRow>
                      <TableCell colSpan={7} className="pt-2 text-xs italic text-ipe-text-muted">
                        * {t('controlTower.scorePendingNote')}
                      </TableCell>
                    </TableRow>
                  </tfoot>
                  <tbody>
                    {queue.map((item) => (
                      <Fragment key={item.mo_id}>
                        <TableRow className={scoreRowBg(item.feasibility_score)}>
                          <TableCell className="font-medium">
                            <span className="tabular-nums" dir="ltr">
                              {item.erp_mo_id ?? item.mo_id.slice(0, 8)}
                            </span>
                            {(item.sync_conflict ||
                              item.data_quality_flags?.some((f) => f.flag_code === 'SYNC_CONFLICT')) && (
                              <Badge variant="warning" className="ms-2" title={JSON.stringify(item.sync_conflict ?? {})}>
                                {t('controlTower.syncConflict')}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>{item.product_name}</TableCell>
                          <TableCell>{item.customer_name}</TableCell>
                          <TableCell>
                            <span className="tabular-nums" dir="ltr">
                              {new Date(item.required_date).toLocaleDateString()}
                            </span>
                          </TableCell>
                          <TableCell>
                            {item.unscorable || (item.feasibility_score === null && item.data_quality_flags?.length) ? (
                              <Badge variant="warning">{t('controlTower.unscorable')}</Badge>
                            ) : (
                              <span className="inline-flex items-center gap-2">
                                <span className="relative inline-flex h-6 w-14 items-center justify-center overflow-hidden rounded-md bg-ipe-surface-alt">
                                  <span
                                    className="absolute inset-y-0 start-0 opacity-35"
                                    style={{
                                      width: `${item.feasibility_score ?? 0}%`,
                                      background:
                                        'linear-gradient(90deg, var(--score-critical), var(--score-warning), var(--score-excellent))',
                                    }}
                                  />
                                  <span
                                    className={`relative text-xs font-bold tabular-nums ${scoreTextClass(item.feasibility_score)}`}
                                    dir="ltr"
                                  >
                                    {item.feasibility_score !== null ? item.feasibility_score : '-'}
                                  </span>
                                </span>
                                <span
                                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${scoreBadgeClass(item.feasibility_score)}`}
                                >
                                  {t(scoreTierLabelKey(scoreTier(item.feasibility_score)))}
                                </span>
                              </span>
                            )}
                          </TableCell>
                          <TableCell>
                            {item.primary_constraint ? (
                              <span className="inline-flex items-center gap-1 rounded bg-ipe-surface-alt px-2 py-0.5 text-xs font-medium">
                                <span aria-hidden>{constraintIcon(item.primary_constraint)}</span>
                                {item.primary_constraint}
                              </span>
                            ) : (
                              <span className="text-xs text-ipe-text-muted">{t('controlTower.none')}</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button size="sm" variant="secondary" onClick={() => toggleExpand(item.mo_id)}>
                              {expandedMoId === item.mo_id ? t('resolution.collapse') : t('controlTower.resolve')}
                            </Button>
                          </TableCell>
                        </TableRow>
                        {expandedMoId === item.mo_id ? (
                          <tr>
                            <td colSpan={7} className="p-0">
                              <InlineResolutionPanel
                                moId={item.mo_id}
                                productName={item.product_name}
                                primaryConstraint={item.primary_constraint}
                                onClose={() => setExpandedMoId(null)}
                                onApproved={() => void reload()}
                              />
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    ))}
                  </tbody>
                </Table>
              </div>

              {/* Mobile cards */}
              <div className="control-tower-cards flex flex-col gap-3 md:hidden">
                {queue.map((item) => (
                  <div
                    key={item.mo_id}
                    className={`rounded-lg border border-ipe-border p-4 ${scoreRowBg(item.feasibility_score)}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold tabular-nums text-ipe-text" dir="ltr">
                          {item.erp_mo_id ?? item.mo_id.slice(0, 8)}
                        </p>
                        <p className="text-sm text-ipe-text-muted">{item.product_name}</p>
                      </div>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium tabular-nums ${scoreBadgeClass(item.feasibility_score)}`}
                        dir="ltr"
                      >
                        {item.feasibility_score ?? '—'}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="inline-flex items-center gap-1 text-xs text-ipe-text-muted">
                        {item.primary_constraint ? (
                          <>
                            <span aria-hidden>{constraintIcon(item.primary_constraint)}</span>
                            {item.primary_constraint}
                          </>
                        ) : (
                          t('controlTower.none')
                        )}
                      </span>
                      <Button size="sm" variant="secondary" onClick={() => toggleExpand(item.mo_id)}>
                        {t('controlTower.resolve')}
                      </Button>
                    </div>
                    {expandedMoId === item.mo_id ? (
                      <div className="-mx-4 mt-3">
                        <InlineResolutionPanel
                          moId={item.mo_id}
                          productName={item.product_name}
                          primaryConstraint={item.primary_constraint}
                          onClose={() => setExpandedMoId(null)}
                          onApproved={() => void reload()}
                        />
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <h3 className="mb-3 font-medium">{t('controlTower.bottleneckMap')}</h3>
            <p className="mb-4 text-xs text-ipe-text-muted">{t('controlTower.bottleneckHint')}</p>
            <div className="space-y-4">
              {bottlenecks.map((b) => {
                const barPct = Math.min(b.utilization_pct, 100);
                return (
                  <div key={b.work_center_id}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="truncate font-medium">{b.work_center_name}</span>
                      <span className="tabular-nums text-ipe-text-muted" dir="ltr">
                        {b.utilization_pct}%
                      </span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-gray-100">
                      <div
                        className={`h-full rounded-full transition-all ${bottleneckColor(b.utilization_pct)}`}
                        style={{ width: `${barPct}%` }}
                      />
                    </div>
                    <div className="mt-0.5 text-xs text-ipe-text-muted">
                      {b.utilization_pct > 95
                        ? t('controlTower.criticalOverload')
                        : b.utilization_pct > 85
                          ? t('controlTower.bottleneckRisk')
                          : t('controlTower.moderateLoad')}
                    </div>
                  </div>
                );
              })}
              {bottlenecks.length === 0 && (
                <p className="text-sm text-ipe-text-muted">{t('controlTower.noBottlenecks')}</p>
              )}
            </div>
          </Card>

          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-medium">{t('controlTower.tariffShock')}</h3>
              <Button size="sm" variant="ghost" onClick={() => navigate(ROUTES.SUPPLY_TARIFF)}>
                {t('controlTower.fullView')} →
              </Button>
            </div>
            <TariffShockPanel />
          </Card>
        </div>
      </div>
    </div>
  );
}
