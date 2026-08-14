/**
 * Schedule → frappe-gantt task adapter (STREAM-5.2).
 * Resources: work centers. Tasks: MO routing operations.
 * Colors by feasibility band.
 */
import type { GanttOperation, GanttRow } from '../types';
import { scoreTier, type ScoreTier } from '@/lib/scoreVisuals';

export interface FrappeGanttTask {
  id: string;
  name: string;
  start: string;
  end: string;
  progress: number;
  custom_class?: string;
  /** Extra metadata for detail panel */
  _meta?: {
    mo_id: string;
    work_center_id: string;
    work_center_name: string;
    feasibility_score?: number;
    status: string;
    sequence: number;
  };
}

const TIER_CLASS: Record<ScoreTier, string> = {
  excellent: 'bar-feas-excellent',
  good: 'bar-feas-good',
  warning: 'bar-feas-warning',
  risk: 'bar-feas-risk',
  critical: 'bar-feas-critical',
  pending: 'bar-feas-pending',
};

/** Horizon anchor: today 00:00 local when ops use minute offsets. */
export function horizonStartDate(anchor?: Date): Date {
  const d = anchor ? new Date(anchor) : new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

function minutesToIso(base: Date, minutes: number): string {
  const d = new Date(base.getTime() + Math.max(0, minutes) * 60_000);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function opFeasibility(row: GanttRow, _op: GanttOperation): number | undefined {
  return row.feasibility_score;
}

/**
 * Map manufacturing_orders + routing_operations (GanttRow shape) to frappe tasks.
 * planned_start/end are minutes from horizon start when numeric.
 */
export function rowsToFrappeTasks(
  rows: GanttRow[],
  opts?: { horizonStart?: Date; workCenterFilter?: string; statusFilter?: string },
): FrappeGanttTask[] {
  const base = opts?.horizonStart ?? horizonStartDate();
  const tasks: FrappeGanttTask[] = [];

  for (const row of rows) {
    const ops = [...row.operations].sort((a, b) => a.sequence - b.sequence);
    for (const op of ops) {
      if (opts?.workCenterFilter && op.work_center_id !== opts.workCenterFilter) continue;
      if (opts?.statusFilter && op.status !== opts.statusFilter) continue;

      const startMin = Number(op.planned_start) || 0;
      let endMin = Number(op.planned_end) || startMin + (Number(op.duration) || 60);
      if (endMin <= startMin) endMin = startMin + 60;

      const score = opFeasibility(row, op);
      const tier = scoreTier(score);

      tasks.push({
        id: op.id || `${row.mo_id}-${op.sequence}`,
        name: `${row.mo_name || row.mo_id} · ${op.work_center_name || op.work_center_id}`,
        start: minutesToIso(base, startMin),
        end: minutesToIso(base, endMin),
        progress: op.status === 'completed' ? 100 : op.status === 'in_progress' ? 50 : 10,
        custom_class: TIER_CLASS[tier],
        _meta: {
          mo_id: row.mo_id,
          work_center_id: op.work_center_id,
          work_center_name: op.work_center_name,
          feasibility_score: score,
          status: op.status,
          sequence: op.sequence,
        },
      });
    }
  }

  // frappe-gantt needs at least one task to render; provide a placeholder day bar
  if (tasks.length === 0) {
    const today = minutesToIso(base, 0);
    const tomorrow = minutesToIso(base, 24 * 60);
    tasks.push({
      id: 'placeholder',
      name: 'No operations scheduled',
      start: today,
      end: tomorrow,
      progress: 0,
      custom_class: 'bar-feas-pending',
    });
  }

  return tasks;
}

/** Distinct work centers from schedule rows (Gantt resources). */
export function extractWorkCenters(rows: GanttRow[]): { id: string; name: string }[] {
  const map = new Map<string, string>();
  for (const row of rows) {
    for (const op of row.operations) {
      if (op.work_center_id) {
        map.set(op.work_center_id, op.work_center_name || op.work_center_id);
      }
    }
  }
  return Array.from(map.entries()).map(([id, name]) => ({ id, name }));
}
