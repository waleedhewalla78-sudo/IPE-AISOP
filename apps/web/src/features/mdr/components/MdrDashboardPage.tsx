import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { fetchMdrDashboard, type MdrDashboardData } from '../api';

function scoreVariant(score: number): 'success' | 'warning' | 'danger' {
  if (score >= 80) return 'success';
  if (score >= 70) return 'warning';
  return 'danger';
}

export function MdrDashboardPage() {
  const [data, setData] = useState<MdrDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMdrDashboard()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-ipe-text">Master Data Readiness</h1>
        <Card><p className="text-sm text-ipe-text-muted">Unable to load MDR dashboard.</p></Card>
      </div>
    );
  }

  const threshold = data.composite_threshold ?? data.gate_threshold ?? 70;
  const gatePassed = data.ai_scheduling_allowed ?? data.gate_passed ?? data.passed ?? data.composite_score >= threshold;
  const dimensions = data.dimensions ?? {
    bom: { score: data.bom_completeness_pct ?? 0, weight: 0.35 },
    lead_time: { score: data.lead_time_accuracy_pct ?? 0, weight: 0.25 },
    routing: { score: data.routing_accuracy_pct ?? 0, weight: 0.2 },
    inventory: { score: data.inventory_accuracy_pct ?? 0, weight: 0.2 },
  };
  const recommendations = data.remediation ?? data.recommendations ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Master Data Readiness</h1>
        <p className="text-sm text-ipe-text-muted">
          Composite score gates autonomous scheduling at {threshold}% threshold
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <h3 className="mb-2 text-sm font-medium text-ipe-text-muted">Composite Score</h3>
          <p className="text-3xl font-bold text-ipe-text">{data.composite_score.toFixed(1)}%</p>
          <Badge variant={scoreVariant(data.composite_score)} className="mt-2">
            {gatePassed ? 'Scheduling allowed' : 'Below gate — scheduling blocked'}
          </Badge>
        </Card>
        <Card>
          <h3 className="mb-2 text-sm font-medium text-ipe-text-muted">Gate Threshold</h3>
          <p className="text-3xl font-bold text-ipe-text">{threshold}%</p>
        </Card>
        <Card>
          <h3 className="mb-2 text-sm font-medium text-ipe-text-muted">Dimensions</h3>
          <p className="text-3xl font-bold text-ipe-text">{Object.keys(dimensions).length}</p>
        </Card>
      </div>

      <Card>
        <h3 className="mb-4 font-medium">Dimension Breakdown</h3>
        <div className="space-y-3">
          {Object.entries(dimensions).map(([key, dim]) => (
            <div key={key} className="flex items-center justify-between rounded border border-ipe-border px-3 py-2">
              <span className="text-sm capitalize text-ipe-text">{key.replace(/_/g, ' ')}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-ipe-text-muted">weight {(dim.weight * 100).toFixed(0)}%</span>
                <Badge variant={scoreVariant(dim.score)}>{dim.score.toFixed(1)}%</Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {recommendations.length > 0 && (
        <Card>
          <h3 className="mb-3 font-medium">Recommendations</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-ipe-text-muted">
            {recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
