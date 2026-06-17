import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { CapacitySummary } from '../types';

interface CapacityUtilizationProps {
  capacities: CapacitySummary[];
}

export function CapacityUtilization({ capacities }: CapacityUtilizationProps) {
  if (capacities.length === 0) {
    return (
      <Card>
        <h3 className="mb-2 font-medium">Capacity Utilization</h3>
        <p className="text-sm text-ipe-text-muted">No capacity data.</p>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-3 font-medium">Capacity Utilization</h3>
      <div className="space-y-3">
        {capacities.map((c) => (
          <div key={c.work_center}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium">{c.work_center}</span>
              <span className="text-ipe-text-muted">
                {c.utilized_hours}h / {c.total_hours}h
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.min(c.utilization_pct, 100)}%`,
                  backgroundColor: c.utilization_pct > 85 ? '#ef4444' : c.utilization_pct > 70 ? '#f59e0b' : '#22c55e',
                }}
              />
            </div>
            <div className="mt-1 flex items-center justify-between text-xs text-ipe-text-muted">
              <span>{c.utilization_pct.toFixed(1)}% utilized</span>
              <Badge variant={c.status === 'operational' ? 'success' : 'warning'}>{c.status}</Badge>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
