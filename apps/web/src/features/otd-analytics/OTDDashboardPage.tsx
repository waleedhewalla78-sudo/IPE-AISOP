import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { t } from '@/lib/i18n';
import {
  fetchFilterOptions,
  fetchOtdBaseline,
  fetchOtdCostOfChaos,
  fetchOtdKpis,
  fetchOtdRootCause,
  fetchOtdTrend,
  type OtdFilters,
  type OtdKpis,
} from './api';

const BAR_COLORS = ['#ef4444', '#f97316', '#eab308', '#3b82f6', '#8b5cf6', '#22c55e'];
const RANGE_OPTIONS = [30, 60, 90, 180] as const;

function formatUsd(value: number): string {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function otdColor(pct: number | null | undefined): string {
  if (pct == null) return 'text-ipe-text';
  if (pct >= 90) return 'text-green-600';
  if (pct >= 80) return 'text-amber-500';
  return 'text-red-600';
}

export function OTDDashboardPage() {
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [trendRange, setTrendRange] = useState<(typeof RANGE_OPTIONS)[number]>(90);
  const [chaosRange, setChaosRange] = useState<'7d' | '30d'>('30d');
  const [filters, setFilters] = useState<OtdFilters>({});
  const [filterOptions, setFilterOptions] = useState({
    suppliers: [] as Array<{ id: string; name: string }>,
    lines: [] as Array<{ id: string; name: string }>,
    regions: [] as Array<{ id: string; name: string }>,
  });
  const [kpis, setKpis] = useState<OtdKpis | null>(null);
  const [trend, setTrend] = useState<Array<{ period_start: string | null; otd_pct: number | null }>>([]);
  const [rootCause, setRootCause] = useState<Array<{ cause_category: string; count: number; cost_usd: number }>>([]);
  const [chaos, setChaos] = useState<{ total_chaos_usd: number; categories: Array<{ label: string; usd: number }> } | null>(null);
  const [baseline, setBaseline] = useState<{
    baseline: { otd_pct?: number } | null;
    delta_vs_baseline: number | null;
    current: { otd_pct?: number | null };
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const rangeParam = `${trendRange}d`;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [k, tr, rc, ch, bl, opts] = await Promise.all([
        fetchOtdKpis(rangeParam, filters),
        fetchOtdTrend(period, rangeParam, filters),
        fetchOtdRootCause(rangeParam, filters),
        fetchOtdCostOfChaos(chaosRange),
        fetchOtdBaseline(),
        fetchFilterOptions(),
      ]);
      setKpis(k);
      setTrend(tr.points ?? []);
      setRootCause(Array.isArray(rc) ? rc : []);
      setChaos(ch);
      setBaseline(bl);
      setFilterOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load OTD analytics');
    } finally {
      setLoading(false);
    }
  }, [period, chaosRange, filters, rangeParam]);

  useEffect(() => {
    void load();
  }, [load]);

  const lateCount = useMemo(() => {
    if (!kpis) return 0;
    return Math.max(0, (kpis.completed_mos ?? 0) - (kpis.on_time_mos ?? 0));
  }, [kpis]);

  const exportPdf = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4 p-6">
        <h1 className="text-2xl font-bold text-ipe-text">{t('analytics.otd.title', t('otd.title', 'OTD Analytics'))}</h1>
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        <Button variant="secondary" size="sm" onClick={() => void load()}>
          {t('otd.retry', 'Retry')}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 print:p-4">
      <div className="flex flex-wrap items-start justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-2xl font-bold text-ipe-text">{t('analytics.otd.title', t('otd.title', 'OTD Analytics'))}</h1>
          <p className="text-sm text-ipe-text-muted">{t('otd.subtitle', 'On-time delivery KPIs, trends, and root cause analysis')}</p>
        </div>
        <Button variant="secondary" size="sm" onClick={exportPdf}>
          {t('otd.exportPdf', 'Export PDF')}
        </Button>
      </div>

      <Card className="p-4 print:hidden">
        <h3 className="mb-3 text-sm font-medium text-ipe-text-muted">{t('otd.filters', 'Filters')}</h3>
        <div className="flex flex-wrap gap-3">
          <select
            className="rounded border border-ipe-border bg-ipe-surface px-3 py-2 text-sm"
            value={filters.supplier_id ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, supplier_id: e.target.value || undefined }))}
            aria-label={t('otd.filterSupplier', 'Supplier')}
          >
            <option value="">{t('otd.allSuppliers', 'All suppliers')}</option>
            {filterOptions.suppliers.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <select
            className="rounded border border-ipe-border bg-ipe-surface px-3 py-2 text-sm"
            value={filters.line_id ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, line_id: e.target.value || undefined }))}
            aria-label={t('otd.filterLine', 'Production line')}
          >
            <option value="">{t('otd.allLines', 'All lines')}</option>
            {filterOptions.lines.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
          <select
            className="rounded border border-ipe-border bg-ipe-surface px-3 py-2 text-sm"
            value={filters.region_id ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, region_id: e.target.value || undefined }))}
            aria-label={t('otd.filterRegion', 'Region')}
          >
            <option value="">{t('otd.allRegions', 'All regions')}</option>
            {filterOptions.regions.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">{t('analytics.otd.currentOtd', 'Current OTD %')}</h3>
          <p className={`text-3xl font-bold ${otdColor(kpis?.otd_pct)}`}>{kpis?.otd_pct ?? '—'}%</p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">{t('analytics.otd.baseline', 'Baseline')}</h3>
          <p className="text-2xl font-bold text-ipe-text">{baseline?.baseline?.otd_pct ?? '—'}%</p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">{t('analytics.otd.improvement', 'Improvement')}</h3>
          <p className={`text-2xl font-bold ${ (baseline?.delta_vs_baseline ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {(baseline?.delta_vs_baseline ?? 0) >= 0 ? '↑' : '↓'} {baseline?.delta_vs_baseline ?? '—'}%
          </p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">{t('analytics.otd.lateOrders', 'Late orders')}</h3>
          <p className="text-2xl font-bold text-red-600">{lateCount}</p>
        </Card>
      </div>

      <Card className="p-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-medium">{t('analytics.otd.trend', t('otd.trendChart', 'OTD trend'))}</h3>
          <div className="flex flex-wrap gap-2 print:hidden">
            {(['daily', 'weekly', 'monthly'] as const).map((p) => (
              <Button key={p} variant={period === p ? 'primary' : 'secondary'} size="sm" onClick={() => setPeriod(p)}>
                {t(`analytics.otd.${p}`, t(`otd.period.${p}`, p))}
              </Button>
            ))}
            {RANGE_OPTIONS.map((r) => (
              <Button key={r} variant={trendRange === r ? 'primary' : 'secondary'} size="sm" onClick={() => setTrendRange(r)}>
                {r}d
              </Button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period_start" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
            <Tooltip />
            {baseline?.baseline?.otd_pct != null && (
              <ReferenceLine y={baseline.baseline.otd_pct} stroke="#94a3b8" strokeDasharray="6 4" label="baseline" />
            )}
            <Line type="monotone" dataKey="otd_pct" stroke="#22c55e" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="p-4">
          <h3 className="mb-4 font-medium">{t('analytics.otd.rootCauses', t('otd.rootCause', 'Root causes'))}</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={rootCause} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="cause_category" width={110} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {rootCause.map((_, idx) => (
                  <Cell key={idx} fill={BAR_COLORS[idx % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-medium">{t('analytics.otd.costOfChaos', t('otd.chaosSummary', 'Cost of chaos'))}</h3>
            <div className="flex gap-2 print:hidden">
              <Button variant={chaosRange === '7d' ? 'primary' : 'secondary'} size="sm" onClick={() => setChaosRange('7d')}>7d</Button>
              <Button variant={chaosRange === '30d' ? 'primary' : 'secondary'} size="sm" onClick={() => setChaosRange('30d')}>30d</Button>
            </div>
          </div>
          <p className="mb-3 text-2xl font-bold text-red-600">{formatUsd(chaos?.total_chaos_usd ?? 0)}</p>
          <ul className="space-y-2 text-sm">
            {(chaos?.categories ?? []).map((c) => (
              <li key={c.label} className="flex justify-between border-b border-ipe-border/50 py-1">
                <span>{c.label}</span>
                <span className="font-medium">{formatUsd(c.usd)}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
