import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import {
  fetchExecutiveSummary, fetchOTDByWorkCenter, fetchDelayBreakdown, fetchPlanningAccuracy,
  fetchPnL, fetchSopGapAnalysis, fetchWhatIfScenarios,
  type ExecutiveSummary, type WorkCenterOTD, type DelayBreakdownItem, type PlanningAccuracy,
  type PnLSummary, type SopGapAnalysis, type WhatIfResult,
} from '../api';

const PIE_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280'];

function formatCurrency(val: number): string {
  return `$${(val / 1000).toFixed(0)}K`;
}

export function ExecutiveDashboardPage() {
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [workCenters, setWorkCenters] = useState<WorkCenterOTD[]>([]);
  const [delayBreakdown, setDelayBreakdown] = useState<DelayBreakdownItem[]>([]);
  const [planningAccuracy, setPlanningAccuracy] = useState<PlanningAccuracy | null>(null);
  const [pnl, setPnl] = useState<PnLSummary | null>(null);
  const [sopGap, setSopGap] = useState<SopGapAnalysis | null>(null);
  const [whatIf, setWhatIf] = useState<WhatIfResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [s, wc, db, pa, p, sg, wi] = await Promise.all([
        fetchExecutiveSummary(),
        fetchOTDByWorkCenter(),
        fetchDelayBreakdown(),
        fetchPlanningAccuracy(),
        fetchPnL(),
        fetchSopGapAnalysis(),
        fetchWhatIfScenarios(),
      ]);
      setSummary(s);
      setWorkCenters(wc);
      setDelayBreakdown(db);
      setPlanningAccuracy(pa);
      setPnl(p);
      setSopGap(sg);
      setWhatIf(wi);
      setLoading(false);
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  if (!summary) return null;

  type ChartRow = { day: string; ai: number | null; manual: number | null };
  const chartData: ChartRow[] = summary.otd_trend.length > 0
    ? summary.otd_trend.reduce<ChartRow[]>((acc, r) => {
      const existing = acc.find(d => d.day === r.day);
      if (existing) {
        if (r.is_ai) existing.ai = r.otd_pct;
        else existing.manual = r.otd_pct;
      } else {
        acc.push({ day: r.day, ai: r.is_ai ? r.otd_pct : null, manual: r.is_ai ? null : r.otd_pct });
      }
      return acc;
    }, [] as ChartRow[])
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Executive Analytics</h1>
        <p className="text-sm text-ipe-text-muted">High-level KPIs, A/B comparison, work center drill-down, delay root cause analysis, and planning accuracy tracking</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">AI-Scheduled OTD</h3>
          <p className="text-2xl font-bold text-green-600">{summary.ai_otd_pct ?? 'N/A'}%</p>
          <Badge variant="success" className="mt-1">Auto-confirmed MOs</Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Manual-Scheduled OTD</h3>
          <p className="text-2xl font-bold text-ipe-text">{summary.manual_otd_pct ?? 'N/A'}%</p>
          <Badge variant="default" className="mt-1">Non-autonomous MOs</Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Planning Cycle Time</h3>
          <p className="text-2xl font-bold text-ipe-text">{summary.avg_planning_cycle_days ?? 'N/A'}<span className="text-sm font-normal text-ipe-text-muted"> days</span></p>
          <Badge variant={summary.avg_planning_cycle_days !== null && summary.avg_planning_cycle_days <= 7 ? 'success' : 'warning'} className="mt-1">
            {summary.avg_planning_cycle_days !== null && summary.avg_planning_cycle_days <= 7 ? 'On target' : 'Needs improvement'}
          </Badge>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Inventory Investment</h3>
          <p className="text-2xl font-bold text-ipe-text">{formatCurrency(summary.inventory_value)}</p>
          <Badge variant={summary.inventory_value < 5000000 ? 'success' : 'warning'} className="mt-1">Current value</Badge>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <h3 className="mb-4 font-medium">AI vs. Manual OTD Trend (Last 90 Days)</h3>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="ai" stroke="#16a34a" name="AI OTD %" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="manual" stroke="#6b7280" name="Manual OTD %" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-sm text-ipe-text-muted">
                <div className="text-center">
                  <p className="font-medium">Simulated Comparison</p>
                  <p className="mt-1">AI OTD: 94.2% &mdash; Manual OTD: 71.8%</p>
                  <p className="mt-1 text-xs">(+22.4% improvement with autonomous scheduling)</p>
                </div>
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <h3 className="mb-3 font-medium">Delay Root Cause Coverage</h3>
            <p className="text-3xl font-bold text-ipe-text">{summary.delay_coverage_pct}%</p>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-100">
              <div className="h-full rounded-full bg-blue-500 transition-all" style={{ width: `${summary.delay_coverage_pct}%` }} />
            </div>
            <p className="mt-2 text-xs text-ipe-text-muted">Classified delays / total delays</p>
          </Card>
          <Card>
            <h3 className="mb-2 font-medium">Planner Productivity</h3>
            <p className="text-sm text-ipe-text-muted">Estimated after AI adoption</p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-center">
              <div className="rounded bg-green-50 p-2">
                <p className="text-lg font-bold text-green-600">-40%</p>
                <p className="text-xs text-green-700">Manual review time</p>
              </div>
              <div className="rounded bg-blue-50 p-2">
                <p className="text-lg font-bold text-blue-600">+28%</p>
                <p className="text-xs text-blue-700">Orders processed/hr</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="mb-4 font-medium">OTD by Work Center</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                  <th className="pb-2 pr-4">Work Center</th>
                  <th className="pb-2 pr-4 text-right">Total MOs</th>
                  <th className="pb-2 pr-4 text-right">On-Time</th>
                  <th className="pb-2 text-right">OTD %</th>
                </tr>
              </thead>
              <tbody>
                {workCenters.map(wc => (
                  <tr key={wc.work_center} className="border-b border-ipe-border/50">
                    <td className="py-2 pr-4 font-medium">{wc.work_center}</td>
                    <td className="py-2 pr-4 text-right">{wc.total_mos}</td>
                    <td className="py-2 pr-4 text-right">{wc.on_time_mos}</td>
                    <td className="py-2 text-right">
                      <span className={`font-semibold ${wc.otd_pct >= 90 ? 'text-green-600' : wc.otd_pct >= 80 ? 'text-amber-600' : 'text-red-600'}`}>
                        {wc.otd_pct}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <div className="space-y-6">
          <Card>
            <h3 className="mb-4 font-medium">Delay Root Cause Breakdown</h3>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <ResponsiveContainer width={160} height={160}>
                  <PieChart>
                    <Pie data={delayBreakdown} dataKey="count" nameKey="cause_category" cx="50%" cy="50%" outerRadius={70} innerRadius={40}>
                      {delayBreakdown.map((_, i) => (
                        // eslint-disable-next-line @typescript-eslint/no-deprecated
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="min-w-0 flex-1">
                {delayBreakdown.slice(0, 6).map((item, i) => (
                  <div key={item.cause_category} className="mb-1 flex items-center gap-2 text-xs">
                    <span className="h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="flex-1 truncate capitalize">{item.cause_category.replace(/_/g, ' ')}</span>
                    <span className="font-medium">{item.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="mb-3 font-medium">Planning Accuracy</h3>
            {planningAccuracy && (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Avg. plan vs. actual</span>
                  <span className="font-medium">{planningAccuracy.avg_planned_vs_actual_days}d</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Median overrun</span>
                  <span className="font-medium">{planningAccuracy.median_planned_vs_actual_days}d</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Within 1 day</span>
                  <span className="font-medium text-green-600">{planningAccuracy.pct_within_1_day}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Within 3 days</span>
                  <span className="font-medium text-amber-600">{planningAccuracy.pct_within_3_days}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Within 7 days</span>
                  <span className="font-medium">{planningAccuracy.pct_within_7_days}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ipe-text-muted">Worst overrun</span>
                  <span className="font-medium text-red-600">{planningAccuracy.max_overrun_days}d</span>
                </div>
                <div className="mt-2 border-t border-ipe-border pt-2 text-xs text-ipe-text-muted">
                  Based on {planningAccuracy.total_mos_analyzed} completed MOs
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* P&L Section */}
      {pnl && (
        <Card>
          <h3 className="mb-4 font-medium">P&L Statement (S&OP View)</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4 mb-4">
            <div className="rounded bg-blue-50 p-3 text-center">
              <p className="text-xs text-ipe-text-muted">Revenue</p>
              <p className="text-xl font-bold text-blue-700">${(pnl.revenue / 1e6).toFixed(1)}M</p>
            </div>
            <div className="rounded bg-green-50 p-3 text-center">
              <p className="text-xs text-ipe-text-muted">Gross Margin</p>
              <p className="text-xl font-bold text-green-700">{pnl.gross_margin_pct}%</p>
            </div>
            <div className="rounded bg-purple-50 p-3 text-center">
              <p className="text-xs text-ipe-text-muted">Net Margin</p>
              <p className="text-xl font-bold text-purple-700">{pnl.net_margin_pct}%</p>
            </div>
            <div className="rounded bg-amber-50 p-3 text-center">
              <p className="text-xs text-ipe-text-muted">COPQ Impact</p>
              <div className="text-xl font-bold text-amber-700">
                {((1 - pnl.net_margin_pct / Math.max(pnl.gross_margin_pct, 0.01)) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                  <th className="pb-2 pr-4">Category</th>
                  <th className="pb-2 pr-4 text-right">Amount</th>
                  <th className="pb-2 text-right">% of Revenue</th>
                </tr>
              </thead>
              <tbody>
                {pnl.rows.map(row => (
                  <tr key={row.category} className="border-b border-ipe-border/50">
                    <td className={`py-1.5 pr-4 font-medium ${row.amount < 0 ? 'text-red-600' : ''}`}>
                      {row.category}
                    </td>
                    <td className="py-1.5 pr-4 text-right">
                      ${Math.abs(row.amount / 1e3).toFixed(0)}K
                    </td>
                    <td className="py-1.5 text-right">{row.pct_of_revenue}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* S&OP Gap Analysis + What-If */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {sopGap && (
          <Card>
            <h3 className="mb-4 font-medium">S&OP Gap Analysis ({sopGap.horizon_weeks} Weeks)</h3>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="rounded bg-blue-50 p-2 text-center">
                <p className="text-xs text-ipe-text-muted">Total Demand</p>
                <p className="text-lg font-bold text-blue-700">{(sopGap.total_demand / 1e3).toFixed(1)}K</p>
              </div>
              <div className="rounded bg-green-50 p-2 text-center">
                <p className="text-xs text-ipe-text-muted">Total Capacity</p>
                <p className="text-lg font-bold text-green-700">{(sopGap.total_capacity / 1e3).toFixed(1)}K</p>
              </div>
              <div className={`rounded p-2 text-center ${sopGap.gap_pct > 10 ? 'bg-red-50' : sopGap.gap_pct > 0 ? 'bg-amber-50' : 'bg-green-50'}`}>
                <p className="text-xs text-ipe-text-muted">Gap</p>
                <p className={`text-lg font-bold ${sopGap.gap_pct > 10 ? 'text-red-700' : sopGap.gap_pct > 0 ? 'text-amber-700' : 'text-green-700'}`}>
                  {sopGap.gap_pct}%
                </p>
              </div>
            </div>
            {sopGap.bottlenecks.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                      <th className="pb-2">Week</th>
                      <th className="pb-2">Family</th>
                      <th className="pb-2 text-right">Demand</th>
                      <th className="pb-2 text-right">Capacity</th>
                      <th className="pb-2 text-right">Gap</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sopGap.bottlenecks.map((b, i) => (
                      <tr key={i} className="border-b border-ipe-border/50">
                        <td className="py-1.5 font-medium">{b.week}</td>
                        <td className="py-1.5">{b.product_family}</td>
                        <td className="py-1.5 text-right">{b.demand.toLocaleString()}</td>
                        <td className="py-1.5 text-right">{b.capacity.toLocaleString()}</td>
                        <td className="py-1.5 text-right font-semibold text-red-600">-{b.gap.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}

        {whatIf.length > 0 && (
          <Card>
            <h3 className="mb-4 font-medium">What-If Simulation</h3>
            <p className="mb-3 text-xs text-ipe-text-muted">
              Compare scenarios for capacity and margin impact
            </p>
            <div className="space-y-3">
              {whatIf.map((s, i) => (
                <div key={i} className="rounded border border-ipe-border p-3">
                  <div className="mb-2 font-medium text-sm">{s.scenario}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-ipe-text-muted">New Margin: </span>
                      <span className={`font-semibold ${s.delta_margin_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {s.new_margin_pct}% ({s.delta_margin_pct > 0 ? '+' : ''}{s.delta_margin_pct}%)
                      </span>
                    </div>
                    <div>
                      <span className="text-ipe-text-muted">New OTD: </span>
                      <span className={`font-semibold ${s.delta_otd_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {s.new_otd_pct}% ({s.delta_otd_pct > 0 ? '+' : ''}{s.delta_otd_pct}%)
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
