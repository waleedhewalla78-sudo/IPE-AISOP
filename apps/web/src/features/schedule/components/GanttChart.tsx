import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { applyCpmCascade, previewCpmCascade } from '../api';
import type {
  CpmCascadeResult,
  CpmConflict,
  CpmFinancialDelta,
  GanttOperation,
  GanttRow,
} from '../types';

interface Props {
  rows: GanttRow[];
  loading?: boolean;
  cpmEnabled?: boolean;
  onApprove?: (moIds: string[]) => void;
  onRowsChange?: (rows: GanttRow[]) => void;
}

interface DragState {
  moId: string;
  operationId: string;
  startX: number;
  originalStart: number;
  currentDelta: number;
}

const DEBOUNCE_MS = 400;

function barColor(op: GanttOperation): string {
  if (op.is_frozen) return 'bg-gray-400';
  if (op.is_disrupted) return 'bg-red-500';
  if (op.status === 'on_time' || !op.status) return 'bg-blue-500';
  return 'bg-yellow-500';
}

function isoToMinutes(iso: string, baseDate: Date): number {
  const ms = new Date(iso).getTime() - baseDate.getTime();
  return Math.round(ms / 60000);
}

function getHorizonBase(rows: GanttRow[]): Date {
  let min = Infinity;
  for (const row of rows) {
    for (const op of row.operations) {
      if (op.planned_start < min) min = op.planned_start;
    }
  }
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (!isFinite(min)) return today;
  return new Date(today.getTime() + min * 60000);
}

function mergeCascadeIntoRows(
  rows: GanttRow[],
  cascade: CpmCascadeResult,
  baseDate: Date,
): GanttRow[] {
  const opMap = new Map(cascade.operations.map((o) => [o.operation_id, o]));
  return rows.map((row) => ({
    ...row,
    operations: row.operations.map((op) => {
      const updated = opMap.get(op.id);
      if (!updated) return { ...op, is_critical: cascade.critical_path_ids.includes(op.id) };
      const aiStart = isoToMinutes(updated.planned_start, baseDate);
      const aiEnd = isoToMinutes(updated.planned_end, baseDate);
      return {
        ...op,
        ai_start: aiStart,
        ai_end: aiEnd,
        is_critical: updated.is_critical,
        slack_minutes: updated.slack_minutes,
      };
    }),
    ai_suggested_start: row.operations[0]
      ? (opMap.get(row.operations[0].id)
          ? isoToMinutes(opMap.get(row.operations[0].id)!.planned_start, baseDate)
          : row.ai_suggested_start)
      : row.ai_suggested_start,
  }));
}

export function GanttChart({
  rows,
  loading = false,
  cpmEnabled = false,
  onApprove,
  onRowsChange,
}: Props) {
  const [selectedMo, setSelectedMo] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [applying, setApplying] = useState(false);
  const [drag, setDrag] = useState<DragState | null>(null);
  const [previewRows, setPreviewRows] = useState<GanttRow[] | null>(null);
  const [criticalPathIds, setCriticalPathIds] = useState<string[]>([]);
  const [conflicts, setConflicts] = useState<CpmConflict[]>([]);
  const [financialDelta, setFinancialDelta] = useState<CpmFinancialDelta | null>(null);
  const [cascadeMs, setCascadeMs] = useState<number | null>(null);
  const [cascadeToken, setCascadeToken] = useState<string | undefined>();
  const [cascadeError, setCascadeError] = useState<string | null>(null);
  const [pendingDelta, setPendingDelta] = useState<number>(0);

  const trackRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cascadeSnapshotRef = useRef<CpmCascadeResult | null>(null);

  const displayRows = previewRows ?? rows;

  const { minMinute, maxMinute, totalMinutes, horizonBase } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;
    for (const row of displayRows) {
      for (const op of row.operations) {
        if (op.planned_start < min) min = op.planned_start;
        if (op.planned_end > max) max = op.planned_end;
        if (op.ai_start != null && op.ai_start < min) min = op.ai_start;
        if (op.ai_end != null && op.ai_end > max) max = op.ai_end;
      }
    }
    if (!isFinite(min)) min = 0;
    if (!isFinite(max)) max = 480;
    return {
      minMinute: min,
      maxMinute: max,
      totalMinutes: Math.max(max - min, 1),
      horizonBase: getHorizonBase(displayRows),
    };
  }, [displayRows]);

  const toPct = useCallback(
    (minute: number) => ((minute - minMinute) / totalMinutes) * 100,
    [minMinute, totalMinutes],
  );

  const hours = useMemo(() => {
    const h = [];
    for (let t = minMinute; t <= maxMinute; t += 60) {
      h.push(t);
    }
    return h;
  }, [minMinute, maxMinute]);

  const disruptedOps = useMemo(() => {
    if (!selectedMo) return [];
    const row = displayRows.find((r) => r.mo_id === selectedMo);
    if (!row) return [];
    const selOps = row.operations.map((o) => o.work_center_id);
    return displayRows
      .flatMap((r) => r.operations)
      .filter((o) => o.work_center_id && selOps.includes(o.work_center_id) && o.mo_id !== selectedMo);
  }, [displayRows, selectedMo]);

  const pendingApproval = useMemo(
    () => displayRows.filter((r) => r.ai_suggested_start != null && !r.approved),
    [displayRows],
  );

  const runCascadePreview = useCallback(
    async (moId: string, operationId: string, deltaMinutes: number) => {
      if (!cpmEnabled || deltaMinutes === 0) return;
      setCascadeError(null);
      try {
        const result = await previewCpmCascade({
          mo_id: moId,
          operation_id: operationId,
          delta_minutes: deltaMinutes,
        });
        cascadeSnapshotRef.current = result;
        setCriticalPathIds(result.critical_path_ids);
        setConflicts(result.conflicts);
        setFinancialDelta(result.financial_delta);
        setCascadeMs(result.cascade_ms);
        setCascadeToken(result.cascade_token);
        const merged = mergeCascadeIntoRows(rows, result, horizonBase);
        setPreviewRows(merged);
        onRowsChange?.(merged);
      } catch (err) {
        setCascadeError(err instanceof Error ? err.message : 'Cascade preview failed');
      }
    },
    [cpmEnabled, rows, horizonBase, onRowsChange],
  );

  useEffect(() => {
    if (!drag || !cpmEnabled) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void runCascadePreview(drag.moId, drag.operationId, drag.currentDelta);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [drag, cpmEnabled, runCascadePreview]);

  useEffect(() => {
    setPreviewRows(null);
    setCriticalPathIds([]);
    setConflicts([]);
    setFinancialDelta(null);
    setCascadeMs(null);
    setCascadeToken(undefined);
    setPendingDelta(0);
  }, [rows]);

  const handlePointerDown = (
    e: React.PointerEvent,
    moId: string,
    operationId: string,
    plannedStart: number,
  ) => {
    if (!cpmEnabled) return;
    e.stopPropagation();
    e.preventDefault();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    setDrag({
      moId,
      operationId,
      startX: e.clientX,
      originalStart: plannedStart,
      currentDelta: 0,
    });
    setPendingDelta(0);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!drag || !trackRef.current) return;
    const trackWidth = trackRef.current.clientWidth;
    const dx = e.clientX - drag.startX;
    const deltaMinutes = Math.round((dx / trackWidth) * totalMinutes);
    setDrag({ ...drag, currentDelta: deltaMinutes });
    setPendingDelta(deltaMinutes);
  };

  const handlePointerUp = () => {
    setDrag(null);
  };

  const handleConfirmCascade = async () => {
    if (!cascadeSnapshotRef.current) return;
    setApplying(true);
    setCascadeError(null);
    try {
      const applyResult = await applyCpmCascade({
        cascade_token: cascadeToken,
        operations: cascadeSnapshotRef.current.operations,
      });
      const moIds = applyResult.mo_ids.length
        ? applyResult.mo_ids
        : [...new Set((previewRows ?? rows).map((r) => r.mo_id))];
      if (onApprove && moIds.length) {
        await onApprove(moIds);
      }
      setPreviewRows(null);
      cascadeSnapshotRef.current = null;
      setPendingDelta(0);
    } catch (err) {
      setCascadeError(err instanceof Error ? err.message : 'Apply failed');
    } finally {
      setApplying(false);
    }
  };

  const handleDiscardPreview = () => {
    setPreviewRows(null);
    setCriticalPathIds([]);
    setConflicts([]);
    setFinancialDelta(null);
    setCascadeMs(null);
    setCascadeToken(undefined);
    setPendingDelta(0);
    cascadeSnapshotRef.current = null;
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex h-64 items-center justify-center text-ipe-text-muted">
          Loading schedule...
        </div>
      </Card>
    );
  }

  if (!rows.length) {
    return (
      <Card className="p-6">
        <div className="flex h-64 items-center justify-center text-ipe-text-muted">
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

  const isCritical = (opId: string, op?: GanttOperation) =>
    criticalPathIds.includes(opId) || op?.is_critical === true;

  return (
    <div className="space-y-6">
      {cpmEnabled && (pendingDelta !== 0 || previewRows) && (
        <Card className="border-l-4 border-amber-500 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold text-ipe-text">CPM Cascade Preview</h3>
              <p className="text-sm text-ipe-text-muted">
                Drag adjustment: {pendingDelta > 0 ? '+' : ''}
                {pendingDelta} min
                {cascadeMs != null && ` · computed in ${cascadeMs}ms`}
              </p>
              {financialDelta && (
                <p className="mt-1 text-xs text-ipe-text-muted">
                  Activity cost Δ {financialDelta.activity_cost_delta_usd.toFixed(0)} USD · Overtime{' '}
                  {financialDelta.overtime_usd.toFixed(0)} USD
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={handleDiscardPreview}>
                Discard
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmCascade}
                disabled={applying || conflicts.length > 0}
              >
                {applying ? 'Applying...' : 'Confirm & Approve'}
              </Button>
            </div>
          </div>
          {conflicts.length > 0 && (
            <div className="mt-3 space-y-1">
              {conflicts.map((c) => (
                <p key={c.operation_id} className="text-sm text-red-600">
                  Conflict: {c.reason}
                </p>
              ))}
            </div>
          )}
          {cascadeError && (
            <p className="mt-2 text-sm text-red-600">{cascadeError}</p>
          )}
        </Card>
      )}

      {pendingApproval.length > 0 && (
        <Card className="border-l-4 border-blue-500 p-4">
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

      <Card className="overflow-x-auto p-4">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-semibold text-ipe-text">Schedule Gantt</h3>
          {cpmEnabled && (
            <Badge variant="default">CPM drag-drop enabled</Badge>
          )}
        </div>

        <div
          className="relative mb-2 h-6"
          style={{ minWidth: `${Math.max(totalMinutes / 10, 600)}px` }}
        >
          {hours.map((h) => (
            <div
              key={h}
              className="absolute -translate-x-1/2 text-xs text-ipe-text-muted"
              style={{ left: `${toPct(h)}%` }}
            >
              {Math.floor(h / 60)}h
            </div>
          ))}
        </div>

        <div
          ref={trackRef}
          className="space-y-1"
          style={{ minWidth: `${Math.max(totalMinutes / 10, 600)}px` }}
          onPointerMove={drag ? handlePointerMove : undefined}
          onPointerUp={drag ? handlePointerUp : undefined}
          onPointerLeave={drag ? handlePointerUp : undefined}
        >
          {displayRows.map((row) => (
            <div
              key={row.mo_id}
              className={`relative cursor-pointer rounded transition-colors ${
                selectedMo === row.mo_id ? 'bg-blue-50 ring-1 ring-blue-300' : 'hover:bg-gray-50'
              }`}
              onClick={() => setSelectedMo(selectedMo === row.mo_id ? null : row.mo_id)}
            >
              <div className="flex h-8 items-center">
                <div className="w-40 shrink-0 truncate px-2 text-xs font-medium text-ipe-text">
                  {row.mo_name}
                  {row.primary_constraint && (
                    <Badge variant="warning" className="ml-1">
                      {row.primary_constraint}
                    </Badge>
                  )}
                </div>

                <div className="relative h-6 flex-1">
                  {row.operations.map((op) => {
                    const dragOffset =
                      drag?.operationId === op.id ? drag.currentDelta : 0;
                    const start = op.planned_start + dragOffset;
                    const end = op.planned_end + dragOffset;
                    const critical = isCritical(op.id, op);

                    return (
                      <div
                        key={op.id}
                        className="absolute inset-y-0"
                        style={{
                          left: `${toPct(start)}%`,
                          width: `${Math.max(toPct(end) - toPct(start), 0.5)}%`,
                        }}
                      >
                        <div
                          role="button"
                          tabIndex={cpmEnabled && !op.is_frozen ? 0 : -1}
                          className={`h-3 rounded ${barColor(op)} ${
                            op.is_disrupted ? 'animate-pulse' : ''
                          } ${critical ? 'ring-2 ring-red-600 ring-offset-1' : ''} ${
                            cpmEnabled && !op.is_frozen ? 'cursor-grab active:cursor-grabbing' : ''
                          }`}
                          title={`${op.id}: ${Math.round(op.duration)}min${
                            op.slack_minutes != null ? ` · slack ${op.slack_minutes}m` : ''
                          }`}
                          onPointerDown={(e) =>
                            handlePointerDown(e, row.mo_id, op.id, op.planned_start)
                          }
                        />
                        {op.ai_start != null && op.ai_end != null && (
                          <div
                            className="mt-0.5 h-1 rounded opacity-70"
                            style={{
                              backgroundColor: '#4ade80',
                              marginLeft: `${toPct(op.ai_start) - toPct(start)}%`,
                              width: `${Math.max(toPct(op.ai_end) - toPct(op.ai_start), 0.5)}%`,
                            }}
                            title={`AI: ${op.ai_start}-${op.ai_end}`}
                          />
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="w-16 shrink-0 px-2 text-right text-xs text-ipe-text-muted">
                  {row.disruption_status === 'impacted' && <Badge variant="danger">Impacted</Badge>}
                  {row.approved && <Badge variant="success">Approved</Badge>}
                </div>
              </div>

              {selectedMo === row.mo_id && disruptedOps.length > 0 && (
                <div className="px-2 pb-2">
                  <div className="mb-1 text-xs font-medium text-red-600">Disruption Cascade</div>
                  {disruptedOps.slice(0, 5).map((op) => (
                    <div
                      key={op.id}
                      className="ml-40 flex items-center gap-2 text-xs text-ipe-text-muted"
                    >
                      <div className="h-3 w-3 rounded bg-red-400" />
                      <span>{op.mo_name}</span>
                      <span className="text-ipe-text-muted">{op.work_center_name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-4 text-xs text-ipe-text-muted">
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded bg-blue-500" />
            <span>Planned</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded bg-green-400" />
            <span>AI Suggested</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded ring-2 ring-red-600" />
            <span>Critical path</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded bg-gray-400" />
            <span>Frozen</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded bg-red-500" />
            <span>Disrupted</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
