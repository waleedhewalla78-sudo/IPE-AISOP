import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts';
import {
  fetchCircularityScore, fetchEolPlan, fetchRecyclabilityScore,
  type CircularityScoreResponse, type EolPlanResponse, type RecyclabilityScoreResponse, type BOMComponent,
} from '../api';

const MOCK_BOM: BOMComponent[] = [
  { component_id: 'CMP-001', material_type: 'Steel', weight_kg: 12.5, recyclable: true },
  { component_id: 'CMP-002', material_type: 'Aluminum', weight_kg: 3.2, recyclable: true },
  { component_id: 'CMP-003', material_type: 'Copper', weight_kg: 1.8, recyclable: true },
  { component_id: 'CMP-004', material_type: 'ABS Plastic', weight_kg: 4.5, recyclable: false },
  { component_id: 'CMP-005', material_type: 'Electronics', weight_kg: 2.1, recyclable: false },
];

type TabKey = 'circularity' | 'eol' | 'recyclability';

function gradeColor(grade: string): 'success' | 'warning' | 'danger' | 'default' {
  if (grade === 'A' || grade === 'A+') return 'success';
  if (grade === 'B' || grade === 'B+') return 'warning';
  return 'danger';
}

function riskColor(risk: string): string {
  if (risk === 'compliant') return 'text-green-600';
  if (risk === 'action_required') return 'text-red-600';
  return 'text-amber-600';
}

function riskBg(risk: string): string {
  if (risk === 'compliant') return 'bg-green-50';
  if (risk === 'action_required') return 'bg-red-50';
  return 'bg-amber-50';
}

function phaseColor(phase: string): string {
  switch (phase) {
    case 'Active Sale': return 'bg-green-500';
    case 'Mature Sale': return 'bg-blue-500';
    case 'Phase-Out': return 'bg-amber-500';
    case 'End of Life': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
}

function CircularityTab({ data }: { data: CircularityScoreResponse }) {
  const barData = data.breakdown.map(b => ({
    material: b.material,
    recovery: b.recovery_pct,
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Circularity Score</h3>
          <p className="text-3xl font-bold text-ipe-text">{data.circularity_score}<span className="text-lg font-normal text-ipe-text-muted">/100</span></p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Material Recovery</h3>
          <p className="text-3xl font-bold text-green-600">{data.material_recovery_pct}<span className="text-lg font-normal text-ipe-text-muted">%</span></p>
        </Card>
        <Card>
          <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">Take-Back Eligibility</h3>
          <div className="mt-1">
            <Badge variant={data.take_back_eligible ? 'success' : 'danger'}>
              {data.take_back_eligible ? 'Eligible' : 'Not Eligible'}
            </Badge>
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="mb-4 font-medium">Material Recovery Rate by Material</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="material" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
            <Tooltip formatter={(value) => [`${value ?? 0}%`, 'Recovery']} />
            <Legend />
            <Bar dataKey="recovery" name="Recovery %" radius={[4, 4, 0, 0]}>
              {barData.map((entry, idx) => (
                <Cell
                  key={idx}
                  fill={entry.recovery >= 75 ? '#22c55e' : entry.recovery >= 50 ? '#eab308' : '#ef4444'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card>
        <h3 className="mb-2 font-medium">Disassembly Cost</h3>
        <p className="text-2xl font-bold text-ipe-text">
          ${data.disassembly_cost.toLocaleString()}
        </p>
        <p className="text-sm text-ipe-text-muted mt-1">Estimated cost to disassemble product for material recovery</p>
      </Card>
    </div>
  );
}

function EolTab({ data }: { data: EolPlanResponse }) {
  return (
    <div className="space-y-6">
      <Card>
        <h3 className="mb-2 font-medium">Predicted End-of-Life Date</h3>
        <p className="text-3xl font-bold text-ipe-text">
          {new Date(data.predicted_eol_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </Card>

      <Card>
        <h3 className="mb-4 font-medium">Phase-Out Schedule</h3>
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-ipe-border" />
          {data.phase_out_schedule.map((phase, idx) => (
            <div key={idx} className="relative mb-6 ml-10 last:mb-0">
              <div className={`absolute -left-7 top-1 h-4 w-4 rounded-full ${phaseColor(phase.phase)}`} />
              <div className="rounded-lg border border-ipe-border bg-white p-4">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-ipe-text">{phase.phase}</h4>
                  <span className="text-xs text-ipe-text-muted">{new Date(phase.date).toLocaleDateString()}</span>
                </div>
                <p className="text-sm text-ipe-text-muted">{phase.description}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="mb-4 font-medium">Regulatory Notices</h3>
        <div className="space-y-3">
          {data.regulatory_notices.map((notice, idx) => (
            <div key={idx} className={`rounded-md border border-ipe-border p-4 ${riskBg(notice.status)}`}>
              <div className="flex items-center justify-between mb-1">
                <h4 className={`font-medium text-sm ${riskColor(notice.status)}`}>{notice.regulation}</h4>
                <Badge variant={notice.status === 'compliant' ? 'success' : notice.status === 'action_required' ? 'danger' : 'warning'}>
                  {notice.status.replace(/_/g, ' ')}
                </Badge>
              </div>
              <p className="text-xs text-ipe-text-muted">Deadline: {notice.deadline === 'ongoing' ? 'Ongoing' : new Date(notice.deadline).toLocaleDateString()}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function RecyclabilityTab({ data }: { data: RecyclabilityScoreResponse }) {
  const scorePct = data.recyclability_score;
  const gaugeAngle = (scorePct / 100) * 180;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="flex flex-col items-center justify-center py-8">
          <h3 className="mb-4 font-medium">Recyclability Score</h3>
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
                stroke={scorePct >= 80 ? '#22c55e' : scorePct >= 60 ? '#eab308' : '#ef4444'}
                strokeWidth="16"
                strokeLinecap="round"
                strokeDasharray={`${(gaugeAngle / 180) * 251.33} 251.33`}
              />
            </svg>
            <div className="absolute inset-0 flex items-end justify-center pb-1">
              <span className="text-4xl font-bold text-ipe-text">{scorePct}</span>
            </div>
          </div>
          <Badge variant={gradeColor(data.grade)} className="mt-4 text-base px-4 py-1">
            Grade: {data.grade}
          </Badge>
        </Card>

        <Card>
          <h3 className="mb-4 font-medium">Component Breakdown</h3>
          <div className="space-y-3">
            {data.breakdown.map((item, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-ipe-text">
                    <span className="font-medium">{item.component}</span>
                    <span className="text-ipe-text-muted ml-2">{item.material}</span>
                  </span>
                  <span className={`font-semibold ${item.recyclability_pct >= 75 ? 'text-green-600' : item.recyclability_pct >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                    {item.recyclability_pct}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                  <div
                    className={`h-full rounded-full transition-all ${item.recyclability_pct >= 75 ? 'bg-green-500' : item.recyclability_pct >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                    style={{ width: `${item.recyclability_pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="mb-3 font-medium">Recommendations</h3>
        <ul className="space-y-2">
          {data.recommendations.map((rec, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-ipe-text">
              <span className="mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-700">
                {idx + 1}
              </span>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

export function SustainabilityPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('circularity');
  const [circularityData, setCircularityData] = useState<CircularityScoreResponse | null>(null);
  const [eolData, setEolData] = useState<EolPlanResponse | null>(null);
  const [recyclabilityData, setRecyclabilityData] = useState<RecyclabilityScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const productId = 'PROD-001';
  const region = 'EU';

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      fetchCircularityScore(productId, MOCK_BOM),
      fetchEolPlan(productId, region),
      fetchRecyclabilityScore(productId, MOCK_BOM),
    ]).then(([c, e, r]) => {
      if (c.status === 'fulfilled') setCircularityData(c.value);
      if (e.status === 'fulfilled') setEolData(e.value);
      if (r.status === 'fulfilled') setRecyclabilityData(r.value);
      setLoading(false);
    });
  }, []);

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'circularity', label: 'Circularity' },
    { key: 'eol', label: 'EOL Planning' },
    { key: 'recyclability', label: 'Recyclability' },
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
        <h1 className="text-2xl font-bold text-ipe-text">Sustainability Dashboard</h1>
        <p className="text-sm text-ipe-text-muted">Circular economy metrics, end-of-life planning, and recyclability analysis</p>
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

      {activeTab === 'circularity' && circularityData && <CircularityTab data={circularityData} />}
      {activeTab === 'eol' && eolData && <EolTab data={eolData} />}
      {activeTab === 'recyclability' && recyclabilityData && <RecyclabilityTab data={recyclabilityData} />}
    </div>
  );
}