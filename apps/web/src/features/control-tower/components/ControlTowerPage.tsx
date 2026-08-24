import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronUp, Wrench } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { ControlTowerSkeleton } from '@/components/ui/Skeleton';
import { FeatureErrorBoundary } from '@/components/ui/FeatureErrorBoundary';
import { PlanPageHeader } from '@/components/planning/PlanPageHeader';
import { FeasibilityBadge, ConstraintChip } from '@/components/planning';
import { DateCell, isUnsetDate } from '@/components/ui/DateCell';
import { TariffShockPanel } from '@/features/tariff/components/TariffShockPanel';
import { SyncStatusBar } from './SyncStatusBar';
import { PlannerAssistPanel } from './PlannerAssistPanel';
import { ForecastOverlayWidget } from './ForecastOverlayWidget';
import { HeroMetrics, type HeroMetricKey } from './HeroMetrics';
import { ROUTES } from '@/lib/constants';
import { IS_RELEASE1 } from '@/lib/releaseProfile';
import { t } from '@/lib/i18n';
import { showToast } from '@/lib/toast';
import api from '@/lib/api';
import {
  scoreRowBg,
} from '@/lib/scoreVisuals';
import { MO_STATUS_META, moStatusFromScore } from '@/lib/moStatusBadge';
import { fetchQueue, fetchKPIs, getMockBottlenecks } from '../api';
import { FeasibilityWebSocket } from '@/lib/ws';
import { shortMoLabel } from '@/lib/planningLabels';
import { cn } from '@/lib/utils';
import type { MOQueueItem, KPI, BottleneckItem } from '../types';

const wsClient = new FeasibilityWebSocket();

type SortKey = 'erp' | 'product' | 'customer' | 'required' | 'score' | 'constraint';
type SortDir = 'asc' | 'desc';

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

function isNeedsData(item: MOQueueItem): boolean {
  return Boolean(
    item.unscorable ||
      (item.feasibility_score == null && (item.data_quality_flags?.length ?? 0) > 0) ||
      (item.feasibility_score == null && isUnsetDate(item.required_date)),
  );
}

function unscoredReason(item: MOQueueItem): string {
  const flags = item.data_quality_flags ?? [];
  const blob = flags.map((f) => `${f.flag_code} ${f.message}`).join(' ').toLowerCase();
  if (blob.includes('bom')) return t('controlTower.needs.bom', 'missing BOM');
  if (blob.includes('routing') || blob.includes('route')) return t('controlTower.needs.routing', 'missing routing');
  if (blob.includes('due') || blob.includes('date') || isUnsetDate(item.required_date)) {
    return t('controlTower.needs.due', 'missing due date');
  }
  if (flags[0]?.message) return flags[0].message;
  return t('controlTower.needs.incomplete', 'incomplete scoring data');
}

function sortValue(item: MOQueueItem, key: SortKey): string | number {
  switch (key) {
    case 'erp':
      return (item.erp_mo_id ?? item.mo_id).toLowerCase();
    case 'product':
      return (item.product_name ?? '').toLowerCase();
    case 'customer':
      return (item.customer_name ?? '').toLowerCase();
    case 'required':
      return new Date(item.required_date).getTime();
    case 'score':
      return item.feasibility_score ?? -1;
    case 'constraint':
      return (item.primary_constraint ?? '').toLowerCase();
    default:
      return '';
  }
}

export function ControlTowerPage() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState<MOQueueItem[]>([]);
  const [kpis, setKPIs] = useState<KPI | null>(null);
  const [bottlenecks, setBottlenecks] = useState<BottleneckItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [metricFilter, setMetricFilter] = useState<HeroMetricKey | null>(null);
  const [textFilter, setTextFilter] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('score');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [batchBusy, setBatchBusy] = useState(false);
  const [syncMeta, setSyncMeta] = useState<{ label: string; healthy: boolean }>({
    label: '—',
    healthy: false,
  });
  const [toolsOpen, setToolsOpen] = useState(false);
  const [needsDataOpen, setNeedsDataOpen] = useState(false);

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

  const overloadedWcNames = useMemo(
    () => new Set(bottlenecks.filter((b) => b.utilization_pct > 85).map((b) => b.work_center_name.toLowerCase())),
    [bottlenecks],
  );

  const needsDataQueue = useMemo(() => queue.filter(isNeedsData), [queue]);

  const filteredQueue = useMemo(() => {
    let rows = queue.filter((r) => !isNeedsData(r));
    if (metricFilter === 'atRisk') {
      rows = rows.filter((r) => (r.feasibility_score ?? 100) < 70);
    } else if (metricFilter === 'bottlenecks') {
      rows = rows.filter((r) => {
        const c = (r.primary_constraint ?? '').toLowerCase();
        return c.includes('capacity') || c.includes('wc') || [...overloadedWcNames].some((n) => c.includes(n));
      });
    } else if (metricFilter === 'avgScore') {
      rows = rows.filter((r) => r.feasibility_score != null);
    }
    const q = textFilter.trim().toLowerCase();
    if (q) {
      rows = rows.filter(
        (r) =>
          (r.erp_mo_id ?? r.mo_id).toLowerCase().includes(q) ||
          (r.product_name ?? '').toLowerCase().includes(q) ||
          (r.customer_name ?? '').toLowerCase().includes(q) ||
          (r.primary_constraint ?? '').toLowerCase().includes(q),
      );
    }
    rows.sort((a, b) => {
      const av = sortValue(a, sortKey);
      const bv = sortValue(b, sortKey);
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return rows;
  }, [queue, metricFilter, textFilter, sortKey, sortDir, overloadedWcNames]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir(key === 'score' ? 'asc' : 'asc');
    }
  };

  const sortMark = (key: SortKey) => (sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '');

  const toggleSelect = (moId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(moId)) next.delete(moId);
      else next.add(moId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === filteredQueue.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredQueue.map((r) => r.mo_id)));
    }
  };

  const onMetricClick = (key: HeroMetricKey) => {
    if (key === 'otd') {
      navigate(ROUTES.COMMAND_OTD_ANALYTICS);
      return;
    }
    if (key === 'sync') return;
    setMetricFilter((prev) => (prev === key ? null : key));
  };

  const batchApproveRecommended = async () => {
    const ids = [...selected];
    if (ids.length === 0) return;
    setBatchBusy(true);
    let ok = 0;
    let fail = 0;
    try {
      for (const moId of ids) {
        try {
          const res = await api.get('/api/v1/resolution/scenarios', { params: { mo_id: moId } });
          const scenarios = (res.data?.data?.scenarios ?? []) as Array<{
            id: string;
            business_score?: number | null;
            status?: string;
          }>;
          if (scenarios.length === 0) {
            fail += 1;
            continue;
          }
          const best = scenarios.reduce((a, b) =>
            (a.business_score ?? -Infinity) >= (b.business_score ?? -Infinity) ? a : b,
          );
          await api.post(`/api/v1/resolution/scenarios/${best.id}/approve`).catch(() =>
            api.post('/api/v1/resolution/approve', { scenario_id: best.id }),
          );
          ok += 1;
        } catch {
          fail += 1;
        }
      }
      showToast({
        tone: fail ? 'warning' : 'success',
        title: t('controlTower.batchDone', 'Batch resolution complete'),
        message: t('controlTower.batchSummary', undefined, { ok, fail }),
      });
      setSelected(new Set());
      await reload();
    } finally {
      setBatchBusy(false);
    }
  };

  if (loading) {
    return <ControlTowerSkeleton />;
  }

  const avgScore = kpis?.avg_feasibility_score ?? null;
  const activeBottlenecks = kpis?.active_bottlenecks ?? null;
  const ordersAtRisk = kpis?.orders_at_risk ?? null;
  const otdPct = kpis?.otd_pct ?? null;

  return (
    <div className="control-tower space-y-4" data-testid="control-tower-page">
      <PlanPageHeader
        title={t('planning.ct.title', t('controlTower.title'))}
        subtitle={t(
          'planning.ct.subtitle',
          'Production overview · risk queue · bottleneck map',
        )}
        actions={
          <>
            <Button
              size="sm"
              disabled={selected.size === 0 || batchBusy}
              onClick={() => void batchApproveRecommended()}
            >
              {batchBusy
                ? '…'
                : t('controlTower.resolveSelected', 'Resolve selected ({count})', {
                    count: selected.size,
                  })}
            </Button>
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
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setToolsOpen((v) => !v)}
              aria-expanded={toolsOpen}
            >
              <Wrench size={14} className="me-1" aria-hidden />
              {t('controlTower.tools', 'Tools')}
              {toolsOpen ? <ChevronUp size={14} className="ms-1" /> : <ChevronDown size={14} className="ms-1" />}
            </Button>
          </>
        }
      />

      <HeroMetrics
        ordersAtRisk={ordersAtRisk}
        activeMoCount={queue.length}
        otdPct={otdPct}
        avgScore={avgScore}
        activeBottlenecks={activeBottlenecks}
        syncLabel={syncMeta.label}
        syncHealthy={syncMeta.healthy}
        worstMo={worstMo}
        activeFilter={metricFilter}
        onMetricClick={onMetricClick}
      />

      {IS_RELEASE1 ? <SyncStatusBar /> : null}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-8">
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
            <Card className="p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-ipe-text">
                  {t('planning.ct.risk_queue', t('controlTower.moQueue'))}{' '}
                  <span className="tabular-nums text-ipe-text-muted">
                    ({filteredQueue.length}
                    {filteredQueue.length !== queue.length ? ` / ${queue.length}` : ''})
                  </span>
                </h3>
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="search"
                    value={textFilter}
                    onChange={(e) => setTextFilter(e.target.value)}
                    placeholder={t('controlTower.filterPlaceholder', 'Filter MO / product / customer…')}
                    className="h-9 rounded-lg border border-ipe-border bg-ipe-surface px-3 text-sm"
                  />
                  {metricFilter ? (
                    <Button size="sm" variant="ghost" onClick={() => setMetricFilter(null)}>
                      {t('controlTower.clearFilter', 'Clear KPI filter')}
                    </Button>
                  ) : null}
                </div>
              </div>

              {selected.size > 0 ? (
                <div className="mb-3 flex flex-wrap items-center gap-2 rounded-md border border-ipe-primary/30 bg-ipe-primary/5 px-3 py-2">
                  <span className="text-sm font-medium text-ipe-text">
                    {t('controlTower.selectedCount', undefined, { count: selected.size })}
                  </span>
                  <Button size="sm" disabled={batchBusy} onClick={() => void batchApproveRecommended()}>
                    {batchBusy
                      ? '…'
                      : t('controlTower.batchApproveRecommended', 'Approve recommended for selected')}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())}>
                    {t('controlTower.clearSelection', 'Clear')}
                  </Button>
                </div>
              ) : null}

              <div className="control-tower-table hidden overflow-x-auto md:block">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeader>
                        <input
                          type="checkbox"
                          checked={filteredQueue.length > 0 && selected.size === filteredQueue.length}
                          onChange={toggleSelectAll}
                          aria-label={t('controlTower.selectAll', 'Select all')}
                        />
                      </TableHeader>
                      <TableHeader>
                        <button type="button" className="font-medium" onClick={() => toggleSort('erp')}>
                          {t('resolution.moId')}
                          {sortMark('erp')}
                        </button>
                      </TableHeader>
                      <TableHeader>
                        <button type="button" className="font-medium" onClick={() => toggleSort('product')}>
                          {t('controlTower.product')}
                          {sortMark('product')}
                        </button>
                      </TableHeader>
                      <TableHeader>
                        <button type="button" className="font-medium" onClick={() => toggleSort('customer')}>
                          {t('controlTower.customer')}
                          {sortMark('customer')}
                        </button>
                      </TableHeader>
                      <TableHeader>
                        <button type="button" className="font-medium" onClick={() => toggleSort('required')}>
                          {t('controlTower.required')}
                          {sortMark('required')}
                        </button>
                      </TableHeader>
                      <TableHeader>
                        <button type="button" className="font-medium" onClick={() => toggleSort('score')}>
                          {t('controlTower.feasibility')}
                          {sortMark('score')}
                        </button>
                      </TableHeader>
                      <TableHeader>
                        <button type="button" className="font-medium" onClick={() => toggleSort('constraint')}>
                          {t('controlTower.constraint')}
                          {sortMark('constraint')}
                        </button>
                      </TableHeader>
                      <TableHeader>{t('controlTower.status', 'Status')}</TableHeader>
                      <TableHeader />
                    </TableRow>
                  </TableHead>
                  <tbody>
                    {filteredQueue.map((item) => {
                      const status = moStatusFromScore(item.feasibility_score, item.unscorable);
                      const statusMeta = MO_STATUS_META[status];
                      return (
                      <TableRow key={item.mo_id} className={scoreRowBg(item.feasibility_score)}>
                        <TableCell>
                          <input
                            type="checkbox"
                            checked={selected.has(item.mo_id)}
                            onChange={() => toggleSelect(item.mo_id)}
                            aria-label={item.erp_mo_id ?? item.mo_id}
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          <span className="tabular-nums" dir="ltr">
                            {shortMoLabel(item.erp_mo_id, item.mo_id)}
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
                          <DateCell value={item.required_date} />
                        </TableCell>
                        <TableCell>
                          {item.unscorable || (item.feasibility_score === null && item.data_quality_flags?.length) ? (
                            <Badge variant="warning">{t('controlTower.unscorable')}</Badge>
                          ) : (
                            <FeasibilityBadge
                              score={item.feasibility_score}
                              size="sm"
                              moId={item.mo_id}
                              productName={item.product_name}
                              constraints={item.primary_constraint ? [item.primary_constraint] : []}
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          {item.primary_constraint ? (
                            <ConstraintChip type={item.primary_constraint} />
                          ) : (
                            <span className="text-xs text-ipe-text-muted">{t('controlTower.none')}</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <span
                            className={cn(
                              'inline-flex rounded-md px-2 py-0.5 text-[11px] font-semibold',
                              statusMeta.className,
                            )}
                          >
                            {t(`controlTower.status.${status}`, statusMeta.label)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() =>
                              navigate(`${ROUTES.PLANNING_RESOLUTION}?mo=${encodeURIComponent(item.mo_id)}`)
                            }
                          >
                            {t('controlTower.resolve')}
                          </Button>
                        </TableCell>
                      </TableRow>
                      );
                    })}
                  </tbody>
                </Table>
              </div>

              <div className="control-tower-cards flex flex-col gap-3 md:hidden">
                {filteredQueue.map((item) => (
                  <div
                    key={item.mo_id}
                    className={`rounded-lg border border-ipe-border p-4 ${scoreRowBg(item.feasibility_score)}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <label className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          className="mt-1"
                          checked={selected.has(item.mo_id)}
                          onChange={() => toggleSelect(item.mo_id)}
                        />
                        <div>
                          <p className="font-semibold tabular-nums text-ipe-text" dir="ltr">
                            {shortMoLabel(item.erp_mo_id, item.mo_id)}
                          </p>
                          <p className="text-sm text-ipe-text-muted">{item.product_name}</p>
                        </div>
                      </label>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() =>
                          navigate(`${ROUTES.PLANNING_RESOLUTION}?mo=${encodeURIComponent(item.mo_id)}`)
                        }
                      >
                        {t('controlTower.resolve')}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {needsDataQueue.length > 0 ? (
            <Card className="mt-4 p-4">
              <button
                type="button"
                className="flex w-full items-center justify-between text-start"
                aria-expanded={needsDataOpen}
                onClick={() => setNeedsDataOpen((o) => !o)}
              >
                <div>
                  <h3 className="text-sm font-semibold text-ipe-text">
                    {t('controlTower.needsData', 'Needs data ({count})', { count: needsDataQueue.length })}
                  </h3>
                  <p className="text-xs text-ipe-text-muted">
                    {t(
                      'controlTower.needsDataHint',
                      'Unscored MOs are held here until BOM, routing, or due date is complete.',
                    )}
                  </p>
                </div>
                {needsDataOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              {needsDataOpen ? (
                <ul className="mt-3 divide-y divide-ipe-border border-t border-ipe-border">
                  {needsDataQueue.map((item) => (
                    <li key={item.mo_id} className="flex flex-wrap items-center justify-between gap-2 py-2.5 text-sm">
                      <div>
                        <span className="font-medium tabular-nums" dir="ltr">
                          {shortMoLabel(item.erp_mo_id, item.mo_id)}
                        </span>
                        <span className="ms-2 text-ipe-text-muted">{item.product_name}</span>
                      </div>
                      <Badge variant="warning">{unscoredReason(item)}</Badge>
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}
        </div>

        <div className="space-y-4 xl:col-span-4">
          <Card className="p-4">
            <h3 className="mb-1 text-sm font-semibold">
              {t('planning.ct.bottleneck_map', t('controlTower.bottleneckMap'))}
            </h3>
            <p className="mb-4 text-xs text-ipe-text-muted">{t('controlTower.bottleneckHint')}</p>
            <div className="space-y-3">
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
                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-ipe-surface-alt">
                      <div
                        className={`h-full rounded-full transition-all ${bottleneckColor(b.utilization_pct)}`}
                        style={{ width: `${barPct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
              {bottlenecks.length === 0 && (
                <p className="text-sm text-ipe-text-muted">{t('controlTower.noBottlenecks')}</p>
              )}
            </div>
          </Card>

          {toolsOpen ? (
            <Card className="p-4" data-testid="ct-tools-panel">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold">{t('controlTower.tariffShock')}</h3>
                <Button size="sm" variant="ghost" onClick={() => navigate(ROUTES.SUPPLY_TARIFF)}>
                  {t('controlTower.fullView')} →
                </Button>
              </div>
              <TariffShockPanel />
            </Card>
          ) : null}
        </div>
      </div>

      <FeatureErrorBoundary fallbackTitle={t('controlTower.assistError')}>
        <PlannerAssistPanel compact />
      </FeatureErrorBoundary>

      <ForecastOverlayWidget />
    </div>
  );
}
