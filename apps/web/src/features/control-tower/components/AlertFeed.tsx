import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { DateCell } from '@/components/ui/DateCell';
import type { DelayAlert } from '../types';

interface AlertFeedProps {
  alerts: DelayAlert[];
}

const severityVariant = (s: string) => {
  switch (s) {
    case 'high': return 'danger';
    case 'medium': return 'warning';
    default: return 'default';
  }
};

export function AlertFeed({ alerts }: AlertFeedProps) {
  if (alerts.length === 0) {
    return (
      <Card>
        <h3 className="mb-2 font-medium">Recent Alerts</h3>
        <p className="text-sm text-ipe-text-muted">No recent alerts.</p>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-3 font-medium">Recent Alerts ({alerts.length})</h3>
      <div className="space-y-2">
        {alerts.slice(0, 5).map((a) => (
          <div key={a.id} className="flex items-start justify-between rounded-md border border-ipe-border p-3 text-sm">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{a.mo_ref}</span>
                <Badge variant={severityVariant(a.severity)}>{a.severity}</Badge>
              </div>
              <p className="mt-0.5 text-ipe-text-muted">{a.cause}</p>
            </div>
            <div className="text-right text-xs text-ipe-text-muted">
              <p>+{a.delay_minutes}m</p>
              <p><DateCell value={a.created_at} className="text-xs" /></p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
