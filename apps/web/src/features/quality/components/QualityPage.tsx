import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import {
  fetchSpcXbar, fetchPChart, fetchDefectPrediction,
  type SpcXbarResponse, type PChartResponse, type DefectPredictionResponse,
} from '../api';

type TabKey = 'spc' | 'defect' | 'pchart';

function riskBadge(level: string): 'success' | 'warning' | 'danger' | 'default' {
  if (level === 'low') return 'success';
  if (level === 'medium') return 'warning';
  return 'danger';
}

function factorBarColor(weight: number): string {
  if (weight >= 0.35) return 'bg-red-500';
  if (weight >= 0.25) return 'bg-amber-500';
  return 'bg-blue-500';
}

function SpcTab({ data }: { data: SpcXbarResponse }) {
  const chartData = data.x_bar_values.map((val, idx) => ({
    sample: `#${idx + 1}`,
    xBar: val,
    isOOC: data.out_of_control_points.includes(idx),
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Process Sigma</h3>
          <p className="text-2xl font-bold text-ipe-text">{data.sigma.toFixed(3)}</p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Center Line (CL)</h3>
          <p className="text-2xl font-bold text-ipe-text">{data.cl.toFixed(2)}</p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Out-of-Control Points</h3>
          <p className="text-2xl font-bold text-red-600">{data.out_of_control_points.length}</p>
        </Card>
      </div>

      <Card>
        <h3 className="mb-4 font-medium">X-bar Control Chart</h3>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="sample" tick={{ fontSize: 11 }} />
            <YAxis domain={[data.lcl - 0.5, data.ucl + 0.5]} tick={{ fontSize: 11 }} />
            <Tooltip
              content={({ payload }) => {
                if (!payload || payload.length === 0) return null;
                const point = payload[0].payload;
                return (
                  <div className="rounded border border-ipe-border bg-white p-2 shadow-sm text-sm">
                    <p className="font-medium">Sample {point.sample}</p>
                    <p>X-bar: {point.xBar?.toFixed(2)}</p>
                    {point.isOOC && <p className="text-red-600 font-medium">Out of Control</p>}
                  </div>
                );
              }}
            />
            <Legend />
            <ReferenceLine y={data.ucl} stroke="#ef4444" strokeDasharray="6 3" label={{ value: 'UCL', position: 'right', fontSize: 11 }} />
            <ReferenceLine y={data.cl} stroke="#6b7280" strokeDasharray="3 3" label={{ value: 'CL', position: 'right', fontSize: 11 }} />
            <ReferenceLine y={data.lcl} stroke="#ef4444" strokeDasharray="6 3" label={{ value: 'LCL', position: 'right', fontSize: 11 }} />
            <Line
              type="monotone"
              dataKey="xBar"
              stroke="#3b82f6"
              name="X-bar"
              strokeWidth={2}
              dot={(props: Record<string, unknown>) => {
                const { cx, cy, payload } = props as { cx: number; cy: number; payload: { isOOC: boolean } };
                return (
                  <circle
                    key={`dot-${cx}-${cy}`}
                    cx={cx}
                    cy={cy}
                    r={4}
                    fill={payload.isOOC ? '#ef4444' : '#3b82f6'}
                    stroke={payload.isOOC ? '#dc2626' : '#2563eb'}
                    strokeWidth={2}
                  />
                );
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

function DefectPredictionTab({ data }: { data: DefectPredictionResponse }) {
  const probability = data.defect_probability;
  const angle = (probability / 1) * 180;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="flex flex-col items-center justify-center py-8">
          <h3 className="mb-4 font-medium">Defect Risk Meter</h3>
          <div className="relative w-48 h-28">
            <svg viewBox="0 0 200 110" className="w-full h-full">
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="16"
                strokeLinecap="round"
              />
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke={probability >= 0.5 ? '#ef4444' : probability >= 0.25 ? '#eab308' : '#22c55e'}
                strokeWidth="16"
                strokeLinecap="round"
                strokeDasharray={`${(angle / 180) * 251.33} 251.33`}
              />
            </svg>
            <div className="absolute inset-0 flex items-end justify-center pb-1">
              <span className="text-4xl font-bold text-ipe-text">{(probability * 100).toFixed(0)}%</span>
            </div>
          </div>
          <Badge variant={riskBadge(data.risk_level)} className="mt-4 text-base px-4 py-1">
            Risk: {data.risk_level.charAt(0).toUpperCase() + data.risk_level.slice(1)}
          </Badge>
        </Card>

        <Card>
          <h3 className="mb-4 font-medium">Contributing Factors</h3>
          <div className="space-y-4">
            {data.contributing_factors.map((factor, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-ipe-text">{factor.factor}</span>
                  <span className="text-sm font-semibold text-ipe-text">{(factor.weight * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                  <div
                    className={`h-full rounded-full transition-all ${factorBarColor(factor.weight)}`}
                    style={{ width: `${factor.weight * 100}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-ipe-text-muted">{factor.description}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="mb-3 font-medium">Recommended Actions</h3>
        <ul className="space-y-2">
          {data.recommended_actions.map((action, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-ipe-text">
              <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-green-100 text-xs font-medium text-green-700">
                {idx + 1}
              </span>
              <span>{action}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function PChartTab({ data }: { data: PChartResponse }) {
  const chartData = data.defect_rates.map((rate, idx) => ({
    sample: `#${idx + 1}`,
    rate: (rate * 100).toFixed(1),
    rateNum: rate * 100,
    isOOC: data.out_of_control_points.includes(idx),
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Average Defect Rate (p-bar)</h3>
          <p className="text-2xl font-bold text-ipe-text">{(data.cl * 100).toFixed(1)}%</p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">UCL</h3>
          <p className="text-2xl font-bold text-red-600">{(data.ucl * 100).toFixed(1)}%</p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Out-of-Control Points</h3>
          <p className="text-2xl font-bold text-red-600">{data.out_of_control_points.length}</p>
        </Card>
      </div>

      <Card>
        <h3 className="mb-4 font-medium">P-Chart — Defect Rate Over Time</h3>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="sample" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, (data.ucl * 100) + 5]} tick={{ fontSize: 11 }} unit="%" />
            <Tooltip formatter={(value) => [`${value ?? 0}%`, 'Defect Rate']} />
            <Legend />
            <ReferenceLine y={data.ucl * 100} stroke="#ef4444" strokeDasharray="6 3" label={{ value: 'UCL', position: 'right', fontSize: 11 }} />
            <ReferenceLine y={data.cl * 100} stroke="#6b7280" strokeDasharray="3 3" label={{ value: 'CL', position: 'right', fontSize: 11 }} />
            <ReferenceLine y={data.lcl * 100} stroke="#ef4444" strokeDasharray="6 3" label={{ value: 'LCL', position: 'right', fontSize: 11 }} />
            <Line
              type="monotone"
              dataKey="rateNum"
              stroke="#3b82f6"
              name="Defect Rate %"
              strokeWidth={2}
              dot={(props: Record<string, unknown>) => {
                const { cx, cy, payload } = props as { cx: number; cy: number; payload: { isOOC: boolean } };
                return (
                  <circle
                    key={`pdot-${cx}-${cy}`}
                    cx={cx}
                    cy={cy}
                    r={4}
                    fill={payload.isOOC ? '#ef4444' : '#3b82f6'}
                    stroke={payload.isOOC ? '#dc2626' : '#2563eb'}
                    strokeWidth={2}
                  />
                );
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

export function QualityPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('spc');
  const [spcData, setSpcData] = useState<SpcXbarResponse | null>(null);
  const [defectData, setDefectData] = useState<DefectPredictionResponse | null>(null);
  const [pChartData, setPChartData] = useState<PChartResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      fetchSpcXbar(
        [[24.2, 24.5, 24.3], [24.8, 25.1, 24.9], [25.3, 24.7, 25.0], [24.6, 24.4, 24.8], [25.2, 25.5, 25.3],
         [24.3, 24.8, 24.9], [25.1, 24.6, 25.0], [25.4, 24.7, 24.9], [24.3, 24.6, 24.8], [25.0, 24.5, 24.7],
         [25.8, 25.9, 25.7], [24.4, 24.6, 24.5], [24.9, 25.0, 24.8], [25.1, 25.2, 25.0], [24.7, 24.8, 24.6],
         [24.5, 24.9, 25.0], [25.3, 25.1, 24.9], [24.8, 24.6, 25.0], [25.0, 24.7, 24.9], [24.6, 24.8, 25.1]],
        3, 26, 24,
      ),
      fetchDefectPrediction('MO-1001', 'assembly', 'WC-003', 'night', 'OP-0042', 12),
      fetchPChart(
        [2, 3, 1, 2, 3, 2, 4, 2, 1, 3, 6, 2, 2, 1, 3],
        [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
        3,
      ),
    ]).then(([s, d, p]) => {
      if (s.status === 'fulfilled') setSpcData(s.value);
      if (d.status === 'fulfilled') setDefectData(d.value);
      if (p.status === 'fulfilled') setPChartData(p.value);
      setLoading(false);
    });
  }, []);

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'spc', label: 'SPC Charts' },
    { key: 'defect', label: 'Defect Prediction' },
    { key: 'pchart', label: 'P-Chart' },
  ];

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
        <h1 className="text-2xl font-bold text-ipe-text">Quality Dashboard</h1>
        <p className="text-sm text-ipe-text-muted">Statistical process control, defect prediction, and P-chart analysis</p>
      </div>

      <div className="flex gap-1 border-b border-ipe-border">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.key
                ? 'border-ipe-primary text-ipe-primary'
                : 'border-transparent text-ipe-text-muted hover:text-ipe-text hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'spc' && spcData && <SpcTab data={spcData} />}
      {activeTab === 'defect' && defectData && <DefectPredictionTab data={defectData} />}
      {activeTab === 'pchart' && pChartData && <PChartTab data={pChartData} />}
    </div>
  );
}