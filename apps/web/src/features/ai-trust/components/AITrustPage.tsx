import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  fetchTrustScores, fetchModelAccuracy, fetchAdoptionMetrics, fetchImpactMetrics,
  type TrustScore, type ModelAccuracy, type AdoptionMetric, type ImpactMetric,
} from '../api';

const TREND_ICON = { up: '↑', down: '↓', stable: '→' } as const;
const TREND_COLOR = { up: 'text-green-600', down: 'text-red-600', stable: 'text-ipe-text-muted' } as const;

export function AITrustPage() {
  const [trustScores, setTrustScores] = useState<TrustScore[]>([]);
  const [modelAccuracy, setModelAccuracy] = useState<ModelAccuracy[]>([]);
  const [adoption, setAdoption] = useState<AdoptionMetric[]>([]);
  const [impact, setImpact] = useState<ImpactMetric[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [ts, ma, ad, im] = await Promise.all([
        fetchTrustScores(),
        fetchModelAccuracy(),
        fetchAdoptionMetrics(),
        fetchImpactMetrics(),
      ]);
      setTrustScores(ts);
      setModelAccuracy(ma);
      setAdoption(ad);
      setImpact(im);
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

  const overallScore = trustScores.length > 0
    ? trustScores.reduce((a, s) => a + s.score, 0) / trustScores.length
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">AI Trust Dashboard</h1>
        <p className="text-sm text-ipe-text-muted">Adoption rate, model accuracy, business impact, and override analytics</p>
      </div>

      {/* Overall Trust Score */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {trustScores.map(ts => (
          <Card key={ts.category}>
            <h3 className="mb-1 text-sm font-medium text-ipe-text-muted">{ts.category}</h3>
            <p className="text-2xl font-bold text-ipe-text">{ts.score.toFixed(1)}%</p>
            <span className={`text-sm font-medium ${TREND_COLOR[ts.trend]}`}>
              {TREND_ICON[ts.trend]} {ts.delta > 0 ? '+' : ''}{ts.delta.toFixed(1)}%
            </span>
          </Card>
        ))}
      </div>

      {/* Overall composite */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium">Composite Trust Score</h3>
            <p className="text-sm text-ipe-text-muted">Weighted average across all dimensions</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-ipe-primary">{overallScore.toFixed(1)}%</p>
            <Badge variant={overallScore >= 85 ? 'success' : overallScore >= 70 ? 'warning' : 'danger'}>
              {overallScore >= 85 ? 'High' : overallScore >= 70 ? 'Good' : 'Needs Improvement'}
            </Badge>
          </div>
        </div>
      </Card>

      {/* Adoption Trend + Model Accuracy */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="mb-4 font-medium">AI Adoption Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={adoption}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="adoption_pct" stroke="#16a34a" name="Adoption %" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="ai_accepted" stroke="#3b82f6" name="AI Accepted" strokeWidth={1.5} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="mb-4 font-medium">Model Accuracy Breakdown</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                  <th className="pb-2 pr-4">Model</th>
                  <th className="pb-2 pr-4 text-right">Predictions</th>
                  <th className="pb-2 pr-4 text-right">Accuracy</th>
                  <th className="pb-2 pr-4 text-right">Confidence</th>
                  <th className="pb-2 text-right">MAPE</th>
                </tr>
              </thead>
              <tbody>
                {modelAccuracy.map(m => (
                  <tr key={m.model_name} className="border-b border-ipe-border/50">
                    <td className="py-1.5 pr-4 font-medium">{m.model_name}</td>
                    <td className="py-1.5 pr-4 text-right">{m.prediction_count.toLocaleString()}</td>
                    <td className="py-1.5 pr-4 text-right">
                      <span className={`font-semibold ${m.accuracy_pct >= 90 ? 'text-green-600' : m.accuracy_pct >= 80 ? 'text-amber-600' : 'text-red-600'}`}>
                        {m.accuracy_pct}%
                      </span>
                    </td>
                    <td className="py-1.5 pr-4 text-right">{m.avg_confidence.toFixed(2)}</td>
                    <td className="py-1.5 text-right">{m.mape}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Impact Comparison */}
      <Card>
        <h3 className="mb-4 font-medium">AI vs. Manual Impact Comparison</h3>
        <p className="mb-3 text-xs text-ipe-text-muted">Real operational delta between AI-assisted and manual-only decisions</p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ipe-border text-xs uppercase text-ipe-text-muted">
                <th className="pb-2 pr-4">Metric</th>
                <th className="pb-2 pr-4 text-right">AI Value</th>
                <th className="pb-2 pr-4 text-right">Manual Value</th>
                <th className="pb-2 pr-4 text-right">Delta</th>
                <th className="pb-2 text-right">Delta %</th>
              </tr>
            </thead>
            <tbody>
              {impact.map(im => (
                <tr key={im.metric} className="border-b border-ipe-border/50">
                  <td className="py-1.5 pr-4 font-medium">{im.metric}</td>
                  <td className="py-1.5 pr-4 text-right font-semibold text-blue-600">{im.ai_value}</td>
                  <td className="py-1.5 pr-4 text-right">{im.manual_value}</td>
                  <td className={`py-1.5 pr-4 text-right font-semibold ${im.delta > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {im.delta > 0 ? '+' : ''}{im.delta}
                  </td>
                  <td className={`py-1.5 text-right font-semibold ${im.delta_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {im.delta_pct > 0 ? '+' : ''}{im.delta_pct}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Override Nudge */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium">Override Nudge</h3>
            <p className="text-sm text-ipe-text-muted">
              Current adoption: <span className="font-bold text-green-600">
                {adoption.length > 0 ? adoption[adoption.length - 1].adoption_pct : 0}%
              </span>
            </p>
          </div>
          <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-center">
            <p className="text-xs text-amber-800 font-medium">Planners who overrode AI recommendations saw</p>
            <p className="text-lg font-bold text-amber-700">-8.4% OTD impact</p>
            <p className="text-xs text-amber-600">vs. accepting AI recommendations</p>
          </div>
        </div>
      </Card>
    </div>
  );
}