import { useMemo, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import type { GanttRow, GanttOperation } from '../types';

interface Props {
  rows: GanttRow[];
  loading?: boolean;
  onApprove?: (moIds: string[]) => void;
}

function barColor(op: GanttOperation): string {
  if (op.is_frozen) return 'bg-gray-400';
  if (op.is_disrupted) return 'bg-red-500';
  if (op.status === 'on_time' || !op.status) return 'bg-blue-500';
  return 'bg-yellow-500';
}

export function GanttChart({ rows, loading = false, onApprove }: Props) {
  const [selectedMo, setSelectedMo] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

  const { minMinute, maxMinute, totalMinutes } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;
    for (const row of rows) {
      for (const op of row.operations) {
        if (op.planned_start < min) min = op.planned_start;
        if (op.planned_end > max) max = op.planned_end;
        if (op.ai_start && op.ai_start < min) min = op.ai_start;
        if (op.ai_end && op.ai_end > max) max = op.ai_end;
      }
    }
    if (!isFinite(min)) min = 0;
    if (!isFinite(max)) max = 480;
    return { minMinute: min, maxMinute: max, totalMinutes: max - min };
  }, [rows]);

  const toPct = (minute: number) => ((minute - minMinute) / totalMinutes) * 100;

  const hours = useMemo(() => {
    const h = [];
    for (let t = minMinute; t <= maxMinute; t += 60) {
      h.push(t);
    }
    return h;
  }, [minMinute, maxMinute]);

  const disruptedOps = useMemo(() => {
    if (!selectedMo) return [];
    const row = rows.find((r) => r.mo_id === selectedMo);
    if (!row) return [];
    const selOps = row.operations.map((o) => o.work_center_id);
    return rows
      .flatMap((r) => r.operations)
      .filter((o) => o.work_center_id && selOps.includes(o.work_center_id) && o.mo_id !== selectedMo);
  }, [rows, selectedMo]);

  const pendingApproval = useMemo(
    () => rows.filter((r) => r.ai_suggested_start != null && !r.approved),
    [rows],
  );

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64 text-ipe-text-muted">
          Loading schedule...
        </div>
      </Card>
    );
  }

  if (!rows.length) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64 text-ipe-text-muted">
          No schedule data available. Run a capacity schedule first.
        </div>
      </Card>
    );
  }

  const handleApprove = async () => {
    if (!onApprove || !pendingApproval.length) return;
    setApproving(true);
    await onApprove(pendingApproval.map((r) => r.mo_id));
    setApproving(false);
  };

  return (
    <div className="space-y-6">
      {/* Approval Queue */}
      {pendingApproval.length > 0 && (
        <Card className="p-4 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-ipe-text">Approval Queue</h3>
              <p className="text-sm text-ipe-text-muted">
                {pendingApproval.length} MO{pendingApproval.length > 1 ? 's' : ''} with AI suggestions pending approval
              </p>
            </div>
            <Button onClick={handleApprove} disabled={approving} variant="primary" size="sm">
              {approving ? 'Approving...' : `Approve All (${pendingApproval.length})`}
            </Button>
          </div>
        </Card>
      )}

      {/* Gantt Chart */}
      <Card className="p-4 overflow-x-auto">
        <h3 className="font-semibold text-ipe-text mb-4">Schedule Gantt</h3>

        {/* Time axis */}
        <div className="relative h-6 mb-2" style={{ minWidth: `${Math.max(totalMinutes / 10, 600)}px` }}>
          {hours.map((h) => (
            <div
              key={h}
              className="absolute text-xs text-ipe-text-muted -translate-x-1/2"
              style={{ left: `${toPct(h)}%` }}
            >
              {Math.floor(h / 60)}h
            </div>
          ))}
        </div>

        {/* Rows */}
        <div className="space-y-1" style={{ minWidth: `${Math.max(totalMinutes / 10, 600)}px` }}>
          {rows.map((row) => (
            <div
              key={row.mo_id}
              className={`relative rounded cursor-pointer transition-colors ${
                selectedMo === row.mo_id ? 'bg-blue-50 ring-1 ring-blue-300' : 'hover:bg-gray-50'
              }`}
              onClick={() => setSelectedMo(selectedMo === row.mo_id ? null : row.mo_id)}
            >
              <div className="flex items-center h-8">
                {/* MO label */}
                <div className="w-40 shrink-0 text-xs font-medium text-ipe-text truncate px-2">
                  {row.mo_name}
                  {row.primary_constraint && (
                    <Badge variant="warning" className="ml-1">
                      {row.primary_constraint}
                    </Badge>
                  )}
                </div>

                {/* Operations */}
                <div className="flex-1 relative h-6">
                  {row.operations.map((op) => (
                    <div key={op.id} className="absolute inset-y-0" style={{ left: `${toPct(op.planned_start)}%`, width: `${Math.max(toPct(op.planned_end) - toPct(op.planned_start), 0.5)}%` }}>
                      {/* Planned bar */}
                      <div
                        className={`h-3 rounded ${barColor(op)} ${op.is_disrupted ? 'animate-pulse' : ''}`}
                        title={`${op.id}: ${Math.round(op.duration)}min`}
                      />
                      {/* AI suggested bar (overlay) */}
                      {op.ai_start != null && op.ai_end != null && (
                        <div
                          className="h-1 rounded mt-0.5 opacity-70"
                          style={{ backgroundColor: '#4ade80' }}
                          title={`AI: ${op.ai_start}-${op.ai_end}`}
                        />
                      )}
                    </div>
                  ))}
                </div>

                {/* Status icon */}
                <div className="w-16 shrink-0 text-xs text-ipe-text-muted px-2 text-right">
                  {row.disruption_status === 'impacted' && <Badge variant="danger">Impacted</Badge>}
                  {row.approved && <Badge variant="success">Approved</Badge>}
                </div>
              </div>

              {/* Disruption cascade (expanded) */}
              {selectedMo === row.mo_id && disruptedOps.length > 0 && (
                <div className="px-2 pb-2">
                  <div className="text-xs font-medium text-red-600 mb-1">Disruption Cascade</div>
                  {disruptedOps.slice(0, 5).map((op) => (
                    <div key={op.id} className="flex items-center gap-2 text-xs text-ipe-text-muted ml-40">
                      <div className="w-3 h-3 rounded bg-red-400" />
                      <span>{op.mo_name}</span>
                      <span className="text-ipe-text-muted">{op.work_center_name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex gap-4 mt-4 text-xs text-ipe-text-muted">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-blue-500" />
            <span>Planned</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-400" />
            <span>AI Suggested</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-gray-400" />
            <span>Frozen</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span>Disrupted</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
